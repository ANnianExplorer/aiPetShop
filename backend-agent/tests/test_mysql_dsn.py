"""MySQL 实现的「无数据库」契约：DSN 解析 + 依赖可导入。

这组测试曾经抓到一个真实缺口：`aiomysql` 写在 requirements.txt 里却从未被安装，
因为实现是懒加载 import，单测永远发现不了，直到 `PET_AGENT_REPO_BACKEND=mysql` 才炸。
"""

from __future__ import annotations

import pytest

from app.storage.mysql import MySqlRepository


def test_dsn_parsed_with_credentials() -> None:
    repo = MySqlRepository("mysql://app:p%40ss@db.internal:3307/petlumina")
    assert repo._cfg["host"] == "db.internal"
    assert repo._cfg["port"] == 3307
    assert repo._cfg["user"] == "app"
    assert repo._cfg["password"] == "p@ss"  # 百分号编码要还原
    assert repo._cfg["db"] == "petlumina"
    assert repo._cfg["charset"] == "utf8mb4"


def test_dsn_defaults_when_only_db_given() -> None:
    repo = MySqlRepository("mysql:///petlumina")
    assert repo._cfg["host"] == "127.0.0.1"
    assert repo._cfg["port"] == 3306
    assert repo._cfg["user"] == "root"
    assert repo._cfg["db"] == "petlumina"


def test_unsupported_scheme_rejected() -> None:
    with pytest.raises(ValueError, match="不支持的 DSN scheme"):
        MySqlRepository("postgres://localhost/petlumina")


def test_aiomysql_available() -> None:
    import aiomysql

    assert aiomysql.__version__
