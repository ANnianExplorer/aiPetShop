"""一次性迁移：执行 backend/sql/v2.16-doc-rag.sql。

DSN 从环境变量读，不把口令写进仓库（与 E13 的约定一致）：

    $env:PET_AGENT_MYSQL_DSN = "mysql://root:<口令>@127.0.0.1:3306/petlumina"
    .venv\\Scripts\\python -m scripts.migrate_doc_rag
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pymysql

DEFAULT_DSN = "mysql://root@127.0.0.1:3306/petlumina"


def parse_dsn(dsn: str) -> dict[str, object]:
    parsed = urlparse(dsn)
    if parsed.scheme not in ("mysql", "mysql+pymysql"):
        raise SystemExit(f"不支持的 DSN scheme: {parsed.scheme}")
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or os.environ.get("PETLUMINA_DB_PASSWORD", ""),
        "database": (parsed.path or "/petlumina").lstrip("/") or "petlumina",
    }


def statements_of(path: Path) -> list[str]:
    """按 ; 切分，先剔掉整行注释（否则"注释 + 第一条 DDL"会被当成注释整段跳过）。"""
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.strip().startswith("--")]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def main() -> int:
    dsn = os.environ.get("PET_AGENT_MYSQL_DSN") or os.environ.get("PETLUMINA_DB_DSN") or DEFAULT_DSN
    sql_path = Path(__file__).resolve().parents[2] / "backend" / "sql" / "v2.16-doc-rag.sql"
    conn = pymysql.connect(**parse_dsn(dsn))  # type: ignore[arg-type]
    try:
        with conn.cursor() as cur:
            for stmt in statements_of(sql_path):
                cur.execute(stmt)
            conn.commit()
            cur.execute("SHOW TABLES LIKE 'doc_%'")
            print("tables:", [row[0] for row in cur.fetchall()])
    finally:
        conn.close()
    print("MIGRATE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
