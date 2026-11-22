"""备份/校验/演练脚本的单测：真库真 Redis 的部分留给 drill，这里钉住判定口径。

想的是：备份脚本最怕两种假——「文件坏了但说通过」和「恢复不一致但说成功」。
所以单测重点不在 happy path，而在篡改检测、临时库名约束、差异比较这几条红线。
"""

from __future__ import annotations

import gzip
import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.backup_restore import (
    SCHEMA_VERSION,
    BackupError,
    compare_mysql_tables,
    compare_redis_keyspace,
    count_create_table,
    drill_database_name,
    is_drill_database,
    keyspace_signature,
    parse_mysql_dsn,
    parse_redis_url,
    read_manifest,
    redact_mysql_dsn,
    redact_redis_url,
    sha256_file,
    verify_backup,
    write_manifest,
)


def _manifest(tmp_path: Path, *, tables: int = 2, rdb: bytes = b"REDIS0009" + b"\x00" * 8) -> dict:
    dump = tmp_path / "mysql.sql.gz"
    with gzip.open(dump, "wb") as handle:
        for index in range(tables):
            handle.write(f"CREATE TABLE `t{index}` (\n  `id` int\n);\n".encode())
    rdb_path = tmp_path / "redis.rdb"
    rdb_path.write_bytes(rdb)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": "2026-11-22T15:00:00Z",
        "label": "nightly",
        "mysql": {
            "database": "petlumina",
            "server_version": "8.0.29",
            "dsn": "mysql://root:***@127.0.0.1:3306/petlumina",
            "dump": {
                "file": "mysql.sql.gz",
                "bytes": dump.stat().st_size,
                "sha256": hashlib.sha256(dump.read_bytes()).hexdigest(),
            },
            "tables": [
                {"name": f"t{index}", "rows": 1, "checksum": 100 + index}
                for index in range(tables)
            ],
        },
        "redis": {
            "url": "redis://127.0.0.1:6379/0",
            "server_version": "5.0.14.1",
            "rdb": {
                "file": "redis.rdb",
                "bytes": rdb_path.stat().st_size,
                "sha256": hashlib.sha256(rdb_path.read_bytes()).hexdigest(),
            },
            "keyspace": {
                "db0": {
                    "keys": 1,
                    "expires": 0,
                    "keys_sha256": keyspace_signature(["satoken:login:session:1"])["keys_sha256"],
                }
            },
        },
    }
    write_manifest(tmp_path, manifest)
    return manifest


def _checks(result: dict) -> dict[str, bool]:
    return {item["check"]: item["ok"] for item in result["checks"]}


class TestRedaction:
    def test_mysql_password_is_masked(self):
        dsn = "mysql://root:p%40ss%3Aword@127.0.0.1:3306/petlumina"
        assert redact_mysql_dsn(dsn) == "mysql://root:***@127.0.0.1:3306/petlumina"

    def test_mysql_without_credentials(self):
        assert redact_mysql_dsn("mysql://127.0.0.1/petlumina") == "mysql://127.0.0.1:3306/petlumina"

    def test_redis_password_is_masked(self):
        assert redact_redis_url("redis://:secret@127.0.0.1:6379/2") == "redis://:***@127.0.0.1:6379/2"

    def test_redis_without_password(self):
        assert redact_redis_url("redis://127.0.0.1:6379/0") == "redis://127.0.0.1:6379/0"


class TestDsnParsing:
    def test_mysql_defaults_and_unquote(self):
        conn = parse_mysql_dsn("mysql://root:p%40ss@localhost/petlumina")
        assert (conn.host, conn.port, conn.user, conn.password, conn.database) == (
            "localhost",
            3306,
            "root",
            "p@ss",
            "petlumina",
        )

    def test_mysql_rejects_bad_scheme(self):
        with pytest.raises(BackupError, match="DSN scheme"):
            parse_mysql_dsn("postgres://root@localhost/petlumina")

    def test_mysql_rejects_unsafe_database_name(self):
        with pytest.raises(BackupError, match="库名"):
            parse_mysql_dsn("mysql://root@localhost/petlumina;drop")

    def test_redis_db_and_password(self):
        conn = parse_redis_url("redis://:pw@localhost:6380/3")
        assert (conn.host, conn.port, conn.db, conn.password) == ("localhost", 6380, 3, "pw")

    def test_redis_rejects_non_integer_db(self):
        with pytest.raises(BackupError, match="db 不是整数"):
            parse_redis_url("redis://localhost/abc")


class TestDrillDatabaseName:
    def test_generated_name_matches_guard(self):
        name = drill_database_name(datetime(2026, 11, 22, 15, 0, 0, tzinfo=UTC), "a1b2c3")
        assert name == "petlumina_drill_20261122T150000Z_a1b2c3"
        assert is_drill_database(name)

    @pytest.mark.parametrize(
        "bad",
        ["petlumina", "petlumina_drill_2026", "petlumina_drill_20261122T150000Z_XYZ", "x"],
    )
    def test_guard_rejects_non_drill_names(self, bad):
        assert not is_drill_database(bad)


class TestKeyspaceSignature:
    def test_order_does_not_matter(self):
        assert keyspace_signature(["a", "b"]) == keyspace_signature(["b", "a"])

    def test_content_matters(self):
        assert keyspace_signature(["a", "b"])["keys_sha256"] != keyspace_signature(["a", "c"])[
            "keys_sha256"
        ]

    def test_empty_is_stable(self):
        assert keyspace_signature([])["keys"] == 0
        assert keyspace_signature([])["keys_sha256"] == keyspace_signature([])["keys_sha256"]


class TestCompareMysql:
    def _rows(self, **overrides):
        rows = [
            {"name": "agent_run", "rows": 3, "checksum": 111},
            {"name": "pet", "rows": 2, "checksum": 222},
        ]
        for row in rows:
            row.update(overrides.get(row["name"], {}))
        return rows

    def test_equal_has_no_diff(self):
        diffs, notes = compare_mysql_tables(self._rows(), self._rows())
        assert diffs == [] and notes == []

    def test_row_count_diff_is_reported(self):
        diffs, _ = compare_mysql_tables(self._rows(), self._rows(pet={"rows": 1}))
        assert any("pet" in item and "行数" in item for item in diffs)

    def test_checksum_diff_is_reported(self):
        diffs, _ = compare_mysql_tables(self._rows(), self._rows(pet={"checksum": 999}))
        assert any("pet" in item and "校验和" in item for item in diffs)

    def test_missing_and_extra_tables(self):
        actual = [row for row in self._rows() if row["name"] != "pet"]
        actual.append({"name": "ghost", "rows": 1, "checksum": 1})
        diffs, _ = compare_mysql_tables(self._rows(), actual)
        assert any("pet" in item and "不存在" in item for item in diffs)
        assert any("ghost" in item and "不在清单" in item for item in diffs)

    def test_null_checksums_are_noted_not_failed(self):
        left = self._rows(pet={"rows": 2, "checksum": None})
        right = self._rows(pet={"rows": 2, "checksum": None})
        diffs, notes = compare_mysql_tables(left, right)
        assert diffs == []
        assert any("pet" in item and "NULL" in item for item in notes)

    def test_null_vs_value_is_a_diff(self):
        left = self._rows(pet={"checksum": None})
        diffs, _ = compare_mysql_tables(left, self._rows())
        assert any("pet" in item and "不可比" in item for item in diffs)


class TestCompareRedis:
    def test_equal_has_no_diff(self):
        expected = {"db0": {"keys": 1, "keys_sha256": "abc"}}
        assert compare_redis_keyspace(expected, expected) == []

    def test_key_count_diff(self):
        expected = {"db0": {"keys": 1, "keys_sha256": "abc"}}
        actual = {"db0": {"keys": 2, "keys_sha256": "abc"}}
        assert any("键数量" in item for item in compare_redis_keyspace(expected, actual))

    def test_db_set_diff(self):
        expected = {"db0": {"keys": 1, "keys_sha256": "abc"}}
        actual = {"db1": {"keys": 1, "keys_sha256": "abc"}}
        assert any("DB 集合" in item for item in compare_redis_keyspace(expected, actual))


class TestVerify:
    def test_complete_backup_passes(self, tmp_path):
        _manifest(tmp_path)
        result = verify_backup(tmp_path)
        assert result["ok"], result
        assert all(_checks(result).values())

    def test_tampered_dump_fails_sha256(self, tmp_path):
        _manifest(tmp_path)
        dump = tmp_path / "mysql.sql.gz"
        dump.write_bytes(dump.read_bytes() + b"tamper")
        checks = _checks(verify_backup(tmp_path))
        assert checks["mysql.dump.sha256"] is False
        assert checks["mysql.dump.bytes"] is False

    def test_missing_dump_fails(self, tmp_path):
        _manifest(tmp_path)
        (tmp_path / "mysql.sql.gz").unlink()
        checks = _checks(verify_backup(tmp_path))
        assert checks["mysql.dump.exists"] is False

    def test_bad_gzip_fails(self, tmp_path):
        manifest = _manifest(tmp_path)
        broken = tmp_path / "mysql.sql.gz"
        broken.write_bytes(b"not a gzip stream")
        manifest["mysql"]["dump"]["bytes"] = broken.stat().st_size
        manifest["mysql"]["dump"]["sha256"] = sha256_file(broken)
        write_manifest(tmp_path, manifest)
        checks = _checks(verify_backup(tmp_path))
        assert checks["mysql.dump.gzip"] is False
        assert checks["mysql.dump.sha256"] is True

    def test_create_table_count_mismatch_fails(self, tmp_path):
        manifest = _manifest(tmp_path, tables=2)
        manifest["mysql"]["tables"].append({"name": "ghost", "rows": 0, "checksum": None})
        write_manifest(tmp_path, manifest)
        checks = _checks(verify_backup(tmp_path))
        assert checks["mysql.dump.create_table_count"] is False

    def test_bad_rdb_magic_fails(self, tmp_path):
        _manifest(tmp_path, rdb=b"NOTREDIS0009")
        checks = _checks(verify_backup(tmp_path))
        assert checks["redis.rdb.magic"] is False

    def test_missing_manifest_reports_and_stops(self, tmp_path):
        result = verify_backup(tmp_path)
        assert result["ok"] is False
        assert _checks(result)["manifest.exists"] is False
        assert _checks(result)["manifest.valid"] is False


class TestManifest:
    def test_roundtrip(self, tmp_path):
        manifest = {"schema_version": SCHEMA_VERSION, "created_at": "x", "label": "y"}
        write_manifest(tmp_path, manifest)
        assert read_manifest(tmp_path) == manifest

    def test_schema_mismatch_rejected(self, tmp_path):
        write_manifest(tmp_path, {"schema_version": 999})
        with pytest.raises(BackupError, match="schema_version"):
            read_manifest(tmp_path)

    def test_invalid_json_rejected(self, tmp_path):
        (tmp_path / "manifest.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(BackupError, match="JSON"):
            read_manifest(tmp_path)


class TestCountCreateTable:
    def test_counts_only_line_start(self, tmp_path):
        path = tmp_path / "dump.gz"
        with gzip.open(path, "wb") as handle:
            handle.write(b"CREATE TABLE `a` (\n);\n")
            handle.write(b"-- CREATE TABLE `fake`\n")
            handle.write(b"CREATE TABLE `b` (\n);\n")
        assert count_create_table(path) == 2
