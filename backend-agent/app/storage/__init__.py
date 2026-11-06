"""存储层出口：按配置选实现，其余代码只依赖 `AgentRepository` 协议。"""

from __future__ import annotations

from ..config import Settings
from .base import AgentRepository
from .memory import InMemoryRepository
from .mysql import MySqlRepository

__all__ = ["AgentRepository", "InMemoryRepository", "MySqlRepository", "create_repository"]


def create_repository(settings: Settings) -> AgentRepository:
    if settings.repo_backend == "mysql":
        if not settings.mysql_dsn:
            raise ValueError("repo_backend=mysql 但缺少 mysql_dsn")
        return MySqlRepository(settings.mysql_dsn)
    return InMemoryRepository()
