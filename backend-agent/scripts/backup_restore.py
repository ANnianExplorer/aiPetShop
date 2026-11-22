"""MySQL/Redis 备份、离线校验与恢复演练（BACKLOG D7）。

一条命令做三件事，每一步都能单独跑：

    .venv\\Scripts\\python -m scripts.backup_restore backup --out D:\\backups\\petlumina
    .venv\\Scripts\\python -m scripts.backup_restore verify --backup <备份目录>
    .venv\\Scripts\\python -m scripts.backup_restore drill  --backup <备份目录>

- **backup**：`mysqldump --single-transaction` 导 MySQL，`redis-cli --rdb` 导 Redis，
  产物落 `<out>/<UTC 时间戳>-<label>/`，清单 `manifest.json` 记录 sha256、逐表行数/
  `CHECKSUM TABLE`、逐 DB 键数量与键名哈希。清单与日志都不含口令。
- **verify**：纯离线。文件在不在、大小/哈希对不对、gzip 能不能解、dump 里
  `CREATE TABLE` 数是否等于清单表数、RDB 魔数对不对。CI/交接前就能跑。
- **drill**：MySQL 恢复到 `petlumina_drill_<UTC 时间戳>_<6 位随机>` 临时库，逐表比
  行数与校验和；Redis 用新端口 + 新目录起临时实例加载 RDB，逐 DB 比键数量与键名
  哈希。无论成败都在 `finally` 里删临时库/停临时实例。

口径与取舍见 `docs/plans/s1.38-backup-restore.md`。三条纪律：不碰线上库（只写
`petlumina_drill_` 前缀的库）、不猜差异（行数/校验和不一致就报失败）、不留临时
资源（库、进程、目录都清）。
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

SCHEMA_VERSION = 1
DRILL_DB_PREFIX = "petlumina_drill_"
DRILL_DB_RE = re.compile(r"^petlumina_drill_\d{8}T\d{6}Z_[0-9a-f]{6}$")
IDENT_RE = re.compile(r"^[A-Za-z0-9_$]+$")
LABEL_RE = re.compile(r"[^A-Za-z0-9._-]+")
RDB_MAGIC_RE = re.compile(rb"^REDIS\d{4}$")
DUMP_TIMEOUT_S = 600
IMPORT_TIMEOUT_S = 600
RDB_TIMEOUT_S = 120
REDIS_BOOT_TIMEOUT_S = 15.0


class BackupError(RuntimeError):
    """可预期的失败：命令失败、清单损坏、恢复比对不一致。"""


# ---------------------------------------------------------------- 纯函数（可单测）
def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_stamp(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%SZ")


def iso_utc(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_label(label: str) -> str:
    cleaned = LABEL_RE.sub("-", label.strip()).strip("-.")
    if not cleaned:
        raise BackupError("label 不能为空")
    return cleaned[:40]


def drill_database_name(moment: datetime, token: str) -> str:
    """临时库名必须可被 `DRILL_DB_RE` 复验，杜绝把生产库当恢复目标。"""
    name = f"{DRILL_DB_PREFIX}{utc_stamp(moment)}_{token}"
    if not DRILL_DB_RE.match(name):
        raise BackupError(f"临时库名不符合约定：{name}")
    return name


def is_drill_database(name: str) -> bool:
    return bool(DRILL_DB_RE.match(name))


def redact_mysql_dsn(dsn: str) -> str:
    parsed = urlparse(dsn)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 3306
    database = (parsed.path or "").lstrip("/")
    user = unquote(parsed.username or "")
    auth = f"{user}:***@" if user else ""
    return f"mysql://{auth}{host}:{port}/{database}"


def redact_redis_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    db = (parsed.path or "/0").lstrip("/") or "0"
    auth = ":***@" if parsed.password else ""
    return f"redis://{auth}{host}:{port}/{db}"


@dataclass(frozen=True)
class MySqlConn:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class RedisConn:
    host: str
    port: int
    db: int
    password: str


def parse_mysql_dsn(dsn: str) -> MySqlConn:
    parsed = urlparse(dsn)
    if parsed.scheme not in ("mysql", "mysql+aiomysql", ""):
        raise BackupError(f"不支持的 MySQL DSN scheme：{parsed.scheme}")
    database = (parsed.path or "/petlumina").lstrip("/") or "petlumina"
    if not IDENT_RE.match(database):
        raise BackupError(f"库名只允许 [A-Za-z0-9_$]：{database}")
    return MySqlConn(
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 3306,
        user=unquote(parsed.username or "root"),
        password=unquote(parsed.password or ""),
        database=database,
    )


def parse_redis_url(url: str) -> RedisConn:
    parsed = urlparse(url)
    if parsed.scheme not in ("redis", ""):
        raise BackupError(f"不支持的 Redis URL scheme：{parsed.scheme}")
    raw_db = (parsed.path or "/0").lstrip("/") or "0"
    try:
        db = int(raw_db)
    except ValueError as exc:
        raise BackupError(f"Redis URL 的 db 不是整数：{raw_db}") from exc
    return RedisConn(
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 6379,
        db=db,
        password=unquote(parsed.password or ""),
    )


def quote_ident(name: str) -> str:
    """库名/表名来自元数据或本脚本生成，反引号转义即可，不拼接用户输入。"""
    return "`" + name.replace("`", "``") + "`"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_info(path: Path) -> dict[str, Any]:
    return {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def gzip_file(source: Path, target: Path) -> None:
    """mtime=0 + 空文件名：同样的 dump 得到同样的 gz 字节，便于复验。"""
    with (
        source.open("rb") as src,
        target.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz,
    ):
        shutil.copyfileobj(src, gz, length=1024 * 1024)


def count_create_table(path: Path) -> int:
    """数 dump 里的建表语句；`CREATE TABLE ` 必须行首，避免把注释里的字算进去。"""
    count = 0
    with gzip.open(path, "rb") as handle:
        for line in handle:
            if line.startswith(b"CREATE TABLE "):
                count += 1
    return count


def keyspace_signature(keys: list[str]) -> dict[str, Any]:
    ordered = sorted(keys)
    digest = hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest()
    return {"keys": len(ordered), "keys_sha256": digest}


def compare_mysql_tables(
    expected: list[dict[str, Any]], actual: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    """返回 (差异, 说明)。差异=失败；说明=不影响判定但要写进报告的情况。"""
    want = {str(row["name"]): row for row in expected}
    got = {str(row["name"]): row for row in actual}
    diffs: list[str] = []
    notes: list[str] = []
    missing = sorted(set(want) - set(got))
    extra = sorted(set(got) - set(want))
    for name in missing:
        diffs.append(f"表 {name} 在恢复库中不存在")
    for name in extra:
        diffs.append(f"表 {name} 不在清单中")
    for name in sorted(set(want) & set(got)):
        left, right = want[name], got[name]
        if int(left["rows"]) != int(right["rows"]):
            diffs.append(f"表 {name} 行数不一致：清单 {left['rows']} / 恢复 {right['rows']}")
        left_sum, right_sum = left.get("checksum"), right.get("checksum")
        if left_sum is None and right_sum is None:
            notes.append(f"表 {name} 两次 CHECKSUM TABLE 均为 NULL，跳过内容比对")
        elif left_sum is None or right_sum is None:
            diffs.append(f"表 {name} 校验和不可比：清单 {left_sum} / 恢复 {right_sum}")
        elif int(left_sum) != int(right_sum):
            diffs.append(f"表 {name} 校验和不一致：清单 {left_sum} / 恢复 {right_sum}")
    return diffs, notes


def compare_redis_keyspace(
    expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
) -> list[str]:
    diffs: list[str] = []
    if set(expected) != set(actual):
        diffs.append(f"DB 集合不一致：清单 {sorted(expected)} / 恢复 {sorted(actual)}")
    for db in sorted(set(expected) & set(actual)):
        left, right = expected[db], actual[db]
        if int(left["keys"]) != int(right["keys"]):
            diffs.append(f"{db} 键数量不一致：清单 {left['keys']} / 恢复 {right['keys']}")
        if left["keys_sha256"] != right["keys_sha256"]:
            diffs.append(f"{db} 键名哈希不一致")
    return diffs


# ---------------------------------------------------------------- 清单
def write_manifest(backup_dir: Path, manifest: dict[str, Any]) -> Path:
    target = backup_dir / "manifest.json"
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    target.write_text(text, encoding="utf-8")
    return target


def read_manifest(backup_dir: Path) -> dict[str, Any]:
    path = backup_dir / "manifest.json"
    if not path.is_file():
        raise BackupError(f"缺少 manifest.json：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BackupError(f"manifest.json 不是合法 JSON：{exc}") from exc
    if not isinstance(data, dict):
        raise BackupError("manifest.json 顶层必须是对象")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise BackupError(f"manifest schema_version 不支持：{data.get('schema_version')}")
    return data


def _assert_no_secret(manifest: dict[str, Any], secret: str) -> None:
    if not secret:
        return
    if secret in json.dumps(manifest, ensure_ascii=False):
        raise BackupError("清单疑似泄露口令，已中止；请检查脱敏逻辑")


# ---------------------------------------------------------------- 子进程
def _run(
    cmd: list[str],
    *,
    env_extra: dict[str, str] | None = None,
    timeout: int,
    stdin: Any = None,
    stdout: Any = subprocess.PIPE,
    what: str,
) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            cmd,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
            env=env,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BackupError(f"{what} 可执行文件不存在：{cmd[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupError(f"{what} 超时（{timeout}s）：{Path(cmd[0]).name}") from exc
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", "replace").strip()
        raise BackupError(f"{what} 失败（exit {proc.returncode}）：{err[-800:]}")
    return proc


def resolve_tool(name: str, explicit: str | None, bin_dir: str | None) -> str:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    if bin_dir:
        candidates.append(str(Path(bin_dir) / name))
        if os.name == "nt":
            candidates.append(str(Path(bin_dir) / f"{name}.exe"))
    found = shutil.which(name)
    if found:
        candidates.append(found)
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    raise BackupError(f"找不到 {name}；用对应 --*-bin-dir 或显式路径参数指定")


def resolve_optional_tool(name: str, bin_dir: str | None) -> str | None:
    try:
        return resolve_tool(name, None, bin_dir)
    except BackupError:
        return None


# ---------------------------------------------------------------- MySQL
def _mysql_connect(conn: MySqlConn, *, database: str | None = None) -> Any:
    import pymysql

    return pymysql.connect(
        host=conn.host,
        port=conn.port,
        user=conn.user,
        password=conn.password,
        database=database,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=10,
    )


def _mysql_scalar(cursor: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    cursor.execute(sql, params)
    row = cursor.fetchone()
    return None if row is None else row[0]


def mysql_table_stats(conn: MySqlConn) -> tuple[str, list[dict[str, Any]]]:
    """返回 (server_version, [{name, rows, checksum}])；顺序按表名稳定。"""
    client = _mysql_connect(conn)
    try:
        with client.cursor() as cursor:
            version = str(_mysql_scalar(cursor, "SELECT VERSION()"))
            cursor.execute(
                "SELECT TABLE_NAME FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME",
                (conn.database,),
            )
            names = [str(row[0]) for row in cursor.fetchall()]
            stats: list[dict[str, Any]] = []
            for name in names:
                qualified = f"{quote_ident(conn.database)}.{quote_ident(name)}"
                rows = int(_mysql_scalar(cursor, f"SELECT COUNT(*) FROM {qualified}"))
                cursor.execute(f"CHECKSUM TABLE {qualified}")
                row = cursor.fetchone()
                checksum = None if row is None or row[1] is None else int(row[1])
                stats.append({"name": name, "rows": rows, "checksum": checksum})
            return version, stats
    finally:
        client.close()


def backup_mysql(
    conn: MySqlConn, dump_path: Path, *, mysqldump: str
) -> dict[str, Any]:
    version, tables = mysql_table_stats(conn)
    cmd = [
        mysqldump,
        "--host",
        conn.host,
        "--port",
        str(conn.port),
        "--user",
        conn.user,
        "--default-character-set=utf8mb4",
        "--single-transaction",
        "--quick",
        "--skip-lock-tables",
        "--routines",
        "--triggers",
        "--no-tablespaces",
        "--set-gtid-purged=OFF",
        conn.database,
    ]
    with dump_path.open("wb") as raw:
        _run(
            cmd,
            env_extra={"MYSQL_PWD": conn.password},
            timeout=DUMP_TIMEOUT_S,
            stdout=raw,
            what="mysqldump",
        )
    return {
        "database": conn.database,
        "server_version": version,
        "dsn": redact_mysql_dsn(
            f"mysql://{conn.user}:{conn.password}@{conn.host}:{conn.port}/{conn.database}"
        ),
        "tables": tables,
    }


def restore_mysql(
    conn: MySqlConn,
    backup_dir: Path,
    manifest: dict[str, Any],
    *,
    mysql: str,
    token: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    mysql_info = manifest["mysql"]
    dump_path = backup_dir / mysql_info["dump"]["file"]
    drill_db = drill_database_name(utc_now(), token)
    if not is_drill_database(drill_db):
        raise BackupError(f"拒绝操作非演练库：{drill_db}")
    admin = _mysql_connect(conn)
    created = False
    workdir = create_workdir(".tmp-mysql-restore-")
    try:
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME "
                "FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s",
                (conn.database,),
            )
            row = cursor.fetchone()
        charset = str(row[0]) if row else "utf8mb4"
        collation = str(row[1]) if row else "utf8mb4_0900_ai_ci"
        with admin.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE {quote_ident(drill_db)} "
                f"CHARACTER SET {quote_ident(charset)} COLLATE {quote_ident(collation)}"
            )
        created = True
        # gzip.GzipFile 的 fileno 指向压缩文件，不能直接当 stdin；先落一份临时 SQL
        sql_path = workdir / "dump.sql"
        with gzip.open(dump_path, "rb") as src, sql_path.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        with sql_path.open("rb") as payload:
            _run(
                [
                    mysql,
                    "--host",
                    conn.host,
                    "--port",
                    str(conn.port),
                    "--user",
                    conn.user,
                    "--default-character-set=utf8mb4",
                    "--binary-mode",
                    "--max-allowed-packet=64M",
                    drill_db,
                ],
                env_extra={"MYSQL_PWD": conn.password},
                timeout=IMPORT_TIMEOUT_S,
                stdin=payload,
                what="mysql 导入",
            )
        drill_conn = MySqlConn(
            host=conn.host,
            port=conn.port,
            user=conn.user,
            password=conn.password,
            database=drill_db,
        )
        _, actual = mysql_table_stats(drill_conn)
        diffs, notes = compare_mysql_tables(mysql_info["tables"], actual)
        return {
            "restored_database": drill_db,
            "dropped_after_drill": True,
            "tables_total": len(mysql_info["tables"]),
            "tables_matched": len(mysql_info["tables"]) - len(diffs),
            "diffs": diffs,
            "notes": notes,
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }
    finally:
        try:
            if created:
                with admin.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS {quote_ident(drill_db)}")
        finally:
            admin.close()
            shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------- Redis
def _redis_client(conn: RedisConn, *, db: int | None = None) -> Any:
    import redis

    return redis.Redis(
        host=conn.host,
        port=conn.port,
        db=conn.db if db is None else db,
        password=conn.password or None,
        decode_responses=True,
        protocol=2,  # 本机 Redis 5.0.14 不支持 HELLO，与 app/core/redis_client.py 口径一致
        socket_connect_timeout=3,
        socket_timeout=10,
    )


def redis_keyspace(conn: RedisConn) -> dict[str, dict[str, Any]]:
    client = _redis_client(conn)
    try:
        info = client.info("keyspace")
        result: dict[str, dict[str, Any]] = {}
        for db_name, meta in sorted(info.items()):
            if not str(db_name).startswith("db"):
                continue
            db_index = int(str(db_name)[2:])
            db_client = _redis_client(conn, db=db_index)
            try:
                keys = list(db_client.scan_iter(count=500))
            finally:
                db_client.close()
            signature = keyspace_signature(keys)
            result[str(db_name)] = {
                "keys": signature["keys"],
                "expires": int(meta.get("expires", 0)),
                "keys_sha256": signature["keys_sha256"],
            }
        return result
    finally:
        client.close()


def _redis_cli_call(redis_cli: str, conn: RedisConn, *args: str, timeout: int = 60) -> str:
    env = {"REDISCLI_AUTH": conn.password} if conn.password else {}
    cmd = [redis_cli, "-h", conn.host, "-p", str(conn.port), "--no-auth-warning", *args]
    proc = _run(cmd, env_extra=env, timeout=timeout, what=f"redis-cli {args[0] if args else ''}")
    return proc.stdout.decode("utf-8", "replace")


def _redis_info_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def _redis_config_value(redis_cli: str, conn: RedisConn, key: str) -> str:
    lines = [line.strip() for line in _redis_cli_call(redis_cli, conn, "config", "get", key).splitlines()]
    lines = [line for line in lines if line]
    if len(lines) < 2:
        raise BackupError(f"CONFIG GET {key} 返回异常：{lines}")
    return lines[-1]


def _bgsave_copy(conn: RedisConn, target: Path, redis_cli: str) -> bool:
    """本地能摸到 `dir`/`dbfilename` 时，用 BGSAVE 落盘再拷贝；拿不到就返回 False。"""
    try:
        reply = _redis_cli_call(redis_cli, conn, "bgsave").strip()
    except BackupError:
        return False
    if "started" not in reply.lower() and "progress" not in reply.lower():
        raise BackupError(f"BGSAVE 返回异常：{reply}")
    deadline = time.monotonic() + RDB_TIMEOUT_S
    while True:
        fields = _redis_info_fields(_redis_cli_call(redis_cli, conn, "info", "persistence"))
        if fields.get("rdb_bgsave_in_progress") == "0":
            status = fields.get("rdb_last_bgsave_status")
            if status != "ok":
                raise BackupError(f"BGSAVE 失败：rdb_last_bgsave_status={status}")
            break
        if time.monotonic() > deadline:
            raise BackupError(f"BGSAVE 超过 {RDB_TIMEOUT_S}s 未完成")
        time.sleep(0.2)
    try:
        directory = _redis_config_value(redis_cli, conn, "dir")
        filename = _redis_config_value(redis_cli, conn, "dbfilename")
    except BackupError:
        return False
    source = Path(directory) / filename
    if not source.is_file():
        return False
    shutil.copyfile(source, target)
    return True


def backup_redis(
    conn: RedisConn,
    rdb_path: Path,
    *,
    redis_cli: str,
    redis_check_rdb: str | None = None,
) -> dict[str, Any]:
    """优先 BGSAVE+本地拷贝；拿不到数据目录（远端/权限）才退回 `redis-cli --rdb`。

    为什么不是默认 `--rdb`：本机 redis-cli 5.0.14（tporadowski Windows 构建）
    以文本模式写文件，RDB 里的 0x0A 全被写成 0x0D 0x0A，`redis-check-rdb` 直接
    报 `Unknown RDB string encoding type`。BGSAVE 落盘由 redis-server 自己写，
    没有这个坑；远端场景仍保留 `--rdb`，并用 `redis-check-rdb` 复验。
    """
    env = {"REDISCLI_AUTH": conn.password} if conn.password else {}
    method = "bgsave-copy"
    if not _bgsave_copy(conn, rdb_path, redis_cli):
        method = "rdb-replication"
        _run(
            [
                redis_cli,
                "-h",
                conn.host,
                "-p",
                str(conn.port),
                "--no-auth-warning",
                "--rdb",
                str(rdb_path),
            ],
            env_extra=env,
            timeout=RDB_TIMEOUT_S,
            what="redis-cli --rdb",
        )
        if redis_check_rdb:
            _run(
                [redis_check_rdb, str(rdb_path)],
                timeout=60,
                what="redis-check-rdb",
            )
    if not RDB_MAGIC_RE.match(rdb_path.read_bytes()[:9]):
        raise BackupError(f"导出的 RDB 魔数不正确：{rdb_path}")
    version = _redis_info_fields(_redis_cli_call(redis_cli, conn, "info", "server")).get(
        "redis_version", "unknown"
    )
    return {
        "url": redact_redis_url(f"redis://{conn.host}:{conn.port}/{conn.db}"),
        "server_version": version,
        "method": method,
        "keyspace": redis_keyspace(conn),
    }


def create_workdir(prefix: str) -> Path:
    """系统临时目录优先；被沙箱/ACL 拒绝时退回仓库内 `.tmp-` 目录。"""
    try:
        return Path(tempfile.mkdtemp(prefix=prefix))
    except OSError:
        base = Path.cwd() / ".tmp-drill"
        base.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=prefix, dir=base))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_redis(port: int, timeout_s: float = REDIS_BOOT_TIMEOUT_S) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5) as sock:
                sock.sendall(b"PING\r\n")
                if sock.recv(16).startswith(b"+PONG"):
                    return True
        except OSError:
            time.sleep(0.1)
    return False


def restore_redis(
    backup_dir: Path, manifest: dict[str, Any], *, redis_server: str, redis_cli: str
) -> dict[str, Any]:
    started = time.perf_counter()
    rdb_path = backup_dir / manifest["redis"]["rdb"]["file"]
    workdir = create_workdir(".tmp-redis-drill-")
    port = _free_port()
    proc: subprocess.Popen[bytes] | None = None
    diffs: list[str] = []
    actual: dict[str, dict[str, Any]] = {}
    try:
        shutil.copyfile(rdb_path, workdir / "dump.rdb")
        proc = subprocess.Popen(
            [
                redis_server,
                "--port",
                str(port),
                "--dir",
                str(workdir),
                "--dbfilename",
                "dump.rdb",
                "--save",
                "",
                "--appendonly",
                "no",
                "--protected-mode",
                "no",
                "--logfile",
                str(workdir / "redis.log"),
            ],
            cwd=str(workdir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not _wait_redis(port):
            raise BackupError(f"临时 Redis 在 {REDIS_BOOT_TIMEOUT_S}s 内未就绪，端口 {port}")
        temp_conn = RedisConn(host="127.0.0.1", port=port, db=0, password="")
        actual = redis_keyspace(temp_conn)
        diffs = compare_redis_keyspace(manifest["redis"]["keyspace"], actual)
        return {
            "port": port,
            "server_version": manifest["redis"].get("server_version"),
            "dbs_total": len(manifest["redis"]["keyspace"]),
            "dbs_matched": len(manifest["redis"]["keyspace"]) - len(diffs),
            "diffs": diffs,
            "actual_keyspace": actual,
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }
    finally:
        if proc is not None:
            subprocess.run(
                [redis_cli, "-p", str(port), "--no-auth-warning", "shutdown", "nosave"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------- 备份 / 校验 / 演练
def run_backup(
    *,
    out_dir: Path,
    label: str,
    mysql_conn: MySqlConn | None,
    redis_conn: RedisConn | None,
    tools: dict[str, str],
) -> Path:
    if mysql_conn is None and redis_conn is None:
        raise BackupError("MySQL 与 Redis 都未配置，没有可备份的组件")
    created = utc_now()
    backup_dir = out_dir / f"{utc_stamp(created)}-{safe_label(label)}"
    try:
        backup_dir.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise BackupError(f"无法创建备份目录 {backup_dir}：{exc}") from exc
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": iso_utc(created),
        "label": safe_label(label),
    }
    try:
        if mysql_conn is not None:
            dump_raw = backup_dir / "mysql.sql"
            info = backup_mysql(mysql_conn, dump_raw, mysqldump=tools["mysqldump"])
            dump_gz = backup_dir / "mysql.sql.gz"
            gzip_file(dump_raw, dump_gz)
            dump_raw.unlink()
            info["dump"] = file_info(dump_gz)
            manifest["mysql"] = info
            _assert_no_secret(manifest, mysql_conn.password)
        if redis_conn is not None:
            rdb_path = backup_dir / "redis.rdb"
            info = backup_redis(
                redis_conn,
                rdb_path,
                redis_cli=tools["redis-cli"],
                redis_check_rdb=tools.get("redis-check-rdb"),
            )
            info["rdb"] = file_info(rdb_path)
            manifest["redis"] = info
            _assert_no_secret(manifest, redis_conn.password)
        write_manifest(backup_dir, manifest)
        return backup_dir
    except BaseException:
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise


def verify_backup(backup_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})

    manifest_path = backup_dir / "manifest.json"
    add("manifest.exists", manifest_path.is_file(), str(manifest_path))
    try:
        manifest = read_manifest(backup_dir)
    except BackupError as exc:
        add("manifest.valid", False, str(exc))
        return {"backup_dir": str(backup_dir), "ok": False, "checks": checks}
    add("manifest.valid", True, f"schema_version={manifest['schema_version']}")

    components = [name for name in ("mysql", "redis") if name in manifest]
    add("manifest.components", bool(components), f"组件：{components or '无'}")

    if "mysql" in manifest:
        info = manifest["mysql"]
        dump_path = backup_dir / info["dump"]["file"]
        exists = dump_path.is_file()
        add("mysql.dump.exists", exists, str(dump_path))
        if exists:
            size = dump_path.stat().st_size
            add("mysql.dump.bytes", size == int(info["dump"]["bytes"]), f"{size} bytes")
            digest = sha256_file(dump_path)
            add("mysql.dump.sha256", digest == info["dump"]["sha256"], digest)
            try:
                table_count = count_create_table(dump_path)
                expected = len(info["tables"])
                add(
                    "mysql.dump.create_table_count",
                    table_count == expected,
                    f"dump {table_count} / 清单 {expected}",
                )
            except (OSError, EOFError, gzip.BadGzipFile) as exc:
                add("mysql.dump.gzip", False, f"{type(exc).__name__}: {exc}")
            else:
                add("mysql.dump.gzip", True, "可完整解压")

    if "redis" in manifest:
        info = manifest["redis"]
        rdb_path = backup_dir / info["rdb"]["file"]
        exists = rdb_path.is_file()
        add("redis.rdb.exists", exists, str(rdb_path))
        if exists:
            size = rdb_path.stat().st_size
            add("redis.rdb.bytes", size == int(info["rdb"]["bytes"]), f"{size} bytes")
            digest = sha256_file(rdb_path)
            add("redis.rdb.sha256", digest == info["rdb"]["sha256"], digest)
            with rdb_path.open("rb") as handle:
                magic = handle.read(9)
            add("redis.rdb.magic", bool(RDB_MAGIC_RE.match(magic)), magic.decode("ascii", "replace"))

    ok = all(bool(item["ok"]) for item in checks)
    return {"backup_dir": str(backup_dir), "ok": ok, "checks": checks}


def drill_token() -> str:
    return os.urandom(3).hex()


def run_drill(
    *,
    backup_dir: Path,
    mysql_conn: MySqlConn | None,
    tools: dict[str, str],
) -> dict[str, Any]:
    manifest = read_manifest(backup_dir)
    started = time.perf_counter()
    report: dict[str, Any] = {
        "backup_dir": str(backup_dir),
        "started_at": iso_utc(utc_now()),
        "ok": True,
        "mysql": None,
        "redis": None,
    }
    if "mysql" in manifest:
        if mysql_conn is None:
            raise BackupError("清单包含 MySQL，但未提供 --mysql-dsn / PET_AGENT_MYSQL_DSN")
        mysql_report = restore_mysql(
            mysql_conn, backup_dir, manifest, mysql=tools["mysql"], token=drill_token()
        )
        report["mysql"] = mysql_report
        if mysql_report["diffs"]:
            report["ok"] = False
    if "redis" in manifest:
        redis_report = restore_redis(
            backup_dir, manifest, redis_server=tools["redis-server"], redis_cli=tools["redis-cli"]
        )
        report["redis"] = redis_report
        if redis_report["diffs"]:
            report["ok"] = False
    report["duration_ms"] = int((time.perf_counter() - started) * 1000)
    report["finished_at"] = iso_utc(utc_now())
    (backup_dir / "drill-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


# ---------------------------------------------------------------- CLI
def _resolve_conns(
    args: argparse.Namespace,
) -> tuple[MySqlConn | None, RedisConn | None]:
    mysql_dsn = args.mysql_dsn or os.environ.get("PET_AGENT_MYSQL_DSN", "")
    redis_url = args.redis_url or os.environ.get("PET_AGENT_REDIS_URL", "")
    mysql_conn = parse_mysql_dsn(mysql_dsn) if mysql_dsn else None
    redis_conn = parse_redis_url(redis_url) if redis_url else None
    return mysql_conn, redis_conn


def _resolve_tools(args: argparse.Namespace, names: tuple[str, ...]) -> dict[str, str]:
    mapping = {
        "mysqldump": ("mysqldump", args.mysqldump, args.mysql_bin_dir),
        "mysql": ("mysql", args.mysql, args.mysql_bin_dir),
        "redis-cli": ("redis-cli", args.redis_cli, args.redis_bin_dir),
        "redis-server": ("redis-server", args.redis_server, args.redis_bin_dir),
    }
    return {key: resolve_tool(mapping[key][0], mapping[key][1], mapping[key][2]) for key in names}


def _print_checks(result: dict[str, Any]) -> None:
    for item in result["checks"]:
        mark = "PASS" if item["ok"] else "FAIL"
        print(f"[{mark}] {item['check']}: {item['detail']}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PetLumina MySQL/Redis 备份与恢复演练")
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup", help="导出 MySQL + Redis 并写 manifest")
    backup.add_argument("--out", required=True, type=Path)
    backup.add_argument("--label", default="manual")
    backup.add_argument("--mysql-dsn", default="")
    backup.add_argument("--redis-url", default="")
    backup.add_argument("--mysql-bin-dir", default=os.environ.get("PET_AGENT_MYSQL_BIN", ""))
    backup.add_argument("--redis-bin-dir", default=os.environ.get("PET_AGENT_REDIS_BIN", ""))
    backup.add_argument("--mysqldump", default=None)
    backup.add_argument("--mysql", default=None)
    backup.add_argument("--redis-cli", default=None)
    backup.add_argument("--redis-check-rdb", default=None)
    backup.add_argument("--redis-server", default=None)

    verify = sub.add_parser("verify", help="离线校验备份完整性")
    verify.add_argument("--backup", required=True, type=Path)

    drill = sub.add_parser("drill", help="恢复演练：临时库/临时 Redis 实例")
    drill.add_argument("--backup", required=True, type=Path)
    drill.add_argument("--mysql-dsn", default="")
    drill.add_argument("--redis-url", default="")
    drill.add_argument("--mysql-bin-dir", default=os.environ.get("PET_AGENT_MYSQL_BIN", ""))
    drill.add_argument("--redis-bin-dir", default=os.environ.get("PET_AGENT_REDIS_BIN", ""))
    drill.add_argument("--mysqldump", default=None)
    drill.add_argument("--mysql", default=None)
    drill.add_argument("--redis-cli", default=None)
    drill.add_argument("--redis-server", default=None)

    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            mysql_conn, redis_conn = _resolve_conns(args)
            backup_tools = _resolve_tools(args, ("mysqldump", "redis-cli"))
            backup_tools["redis-check-rdb"] = resolve_optional_tool(
                "redis-check-rdb", args.redis_bin_dir
            )
            backup_dir = run_backup(
                out_dir=args.out,
                label=args.label,
                mysql_conn=mysql_conn,
                redis_conn=redis_conn,
                tools=backup_tools,
            )
            manifest = read_manifest(backup_dir)
            print(f"[backup] 目录 {backup_dir}", flush=True)
            if manifest.get("mysql"):
                info = manifest["mysql"]
                print(
                    f"[backup] mysql {info['database']} {len(info['tables'])} 张表，"
                    f"{info['dump']['bytes']} bytes，sha256 {info['dump']['sha256'][:16]}…",
                    flush=True,
                )
            if manifest.get("redis"):
                info = manifest["redis"]
                dbs = info["keyspace"]
                total = sum(int(meta["keys"]) for meta in dbs.values())
                print(
                    f"[backup] redis {info['server_version']} {len(dbs)} 个 DB / {total} 个键，"
                    f"{info['rdb']['bytes']} bytes，方式 {info.get('method', 'unknown')}",
                    flush=True,
                )
            print("RESULT: ok", flush=True)
            return 0
        if args.command == "verify":
            result = verify_backup(args.backup)
            _print_checks(result)
            print(f"RESULT: {'ok' if result['ok'] else 'failed'}", flush=True)
            return 0 if result["ok"] else 1
        mysql_conn, _ = _resolve_conns(args)
        report = run_drill(
            backup_dir=args.backup,
            mysql_conn=mysql_conn,
            tools=_resolve_tools(args, ("mysql", "redis-cli", "redis-server")),
        )
        if report["mysql"]:
            info = report["mysql"]
            print(
                f"[drill] mysql {info['restored_database']}: "
                f"{info['tables_matched']}/{info['tables_total']} 张表一致，"
                f"{info['duration_ms']} ms，已删除临时库",
                flush=True,
            )
            for diff in info["diffs"]:
                print(f"[drill] mysql DIFF {diff}", flush=True)
        if report["redis"]:
            info = report["redis"]
            print(
                f"[drill] redis 端口 {info['port']}: "
                f"{info['dbs_matched']}/{info['dbs_total']} 个 DB 一致，{info['duration_ms']} ms",
                flush=True,
            )
            for diff in info["diffs"]:
                print(f"[drill] redis DIFF {diff}", flush=True)
        print(f"[drill] 报告 {args.backup / 'drill-report.json'}", flush=True)
        print(f"RESULT: {'ok' if report['ok'] else 'failed'}", flush=True)
        return 0 if report["ok"] else 1
    except BackupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        print("RESULT: failed", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
