"""一次性迁移：执行 backend/sql/v2.17-profile.sql（画像快照表）。

复用 `migrate_doc_rag` 里的 DSN 解析与「先剥注释再切分」逻辑：
迁移脚本最容易踩的两个坑（口令进仓库、注释吞掉第一条 DDL）只修一次。

    $env:PET_AGENT_MYSQL_DSN = "mysql://root:<口令>@127.0.0.1:3306/petlumina"
    .venv\\Scripts\\python -m scripts.migrate_profile
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pymysql

from .migrate_doc_rag import DEFAULT_DSN, parse_dsn, statements_of


def main() -> int:
    dsn = (
        os.environ.get("PET_AGENT_MYSQL_DSN")
        or os.environ.get("PETLUMINA_DB_DSN")
        or DEFAULT_DSN
    )
    sql_path = Path(__file__).resolve().parents[2] / "backend" / "sql" / "v2.17-profile.sql"
    conn = pymysql.connect(**parse_dsn(dsn))  # type: ignore[arg-type]
    try:
        with conn.cursor() as cur:
            for stmt in statements_of(sql_path):
                cur.execute(stmt)
            conn.commit()
            cur.execute("SHOW TABLES LIKE 'profile_snapshot'")
            print("tables:", [row[0] for row in cur.fetchall()])
    finally:
        conn.close()
    print("MIGRATE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
