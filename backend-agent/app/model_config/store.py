"""模型配置的存储层：单行配置，内存/文件与 MySQL 两种实现。

- `repo_backend=memory`（默认本地开发）落到 `data/model-config.json`，重启不丢；
- `repo_backend=mysql` 落到 `agent_model_config`（id=1），多实例共享；
- 两处都只存 `api_key_cipher`，不存明文。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import unquote, urlparse

from ..config import Settings

_TABLE = "agent_model_config"


class ModelConfigStoreError(RuntimeError):
    """配置存储不可用或内容损坏。"""


@dataclass
class ModelConfig:
    provider: str
    base_url: str
    model: str
    api_key_cipher: str = field(repr=False)
    enabled: bool = True
    updated_by: str | None = None
    update_time: str | None = None


class ModelConfigStore(Protocol):
    async def get(self) -> ModelConfig | None: ...

    async def save(self, config: ModelConfig) -> ModelConfig: ...

    async def aclose(self) -> None: ...


class InMemoryModelConfigStore:
    """内存实现；给了 path 就原子落盘，供单机/默认 memory 模式持久化。"""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else None
        self._lock = asyncio.Lock()
        self._config: ModelConfig | None = None
        if self._path is not None and self._path.exists():
            self._config = self._load(self._path)

    @staticmethod
    def _load(path: Path) -> ModelConfig:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ModelConfig(
                provider=str(data["provider"]),
                base_url=str(data["base_url"]),
                model=str(data["model"]),
                api_key_cipher=str(data["api_key_cipher"]),
                enabled=bool(data.get("enabled", True)),
                updated_by=data.get("updated_by"),
                update_time=data.get("update_time"),
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise ModelConfigStoreError(f"模型配置文件损坏：{path}") from exc

    async def get(self) -> ModelConfig | None:
        async with self._lock:
            return self._config

    async def save(self, config: ModelConfig) -> ModelConfig:
        async with self._lock:
            self._config = config
            if self._path is not None:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self._path.with_name(self._path.name + ".tmp")
                tmp.write_text(
                    json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                with contextlib.suppress(OSError):
                    os.chmod(tmp, 0o600)
                os.replace(tmp, self._path)
            return config

    async def aclose(self) -> None:
        return None


class MySqlModelConfigStore:
    def __init__(self, dsn: str) -> None:
        parsed = urlparse(dsn)
        if parsed.scheme not in ("mysql", "mysql+aiomysql", ""):
            raise ValueError(f"不支持的 DSN scheme：{parsed.scheme}")
        self._cfg: dict[str, Any] = {
            "host": parsed.hostname or "127.0.0.1",
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or "root"),
            "password": unquote(parsed.password or ""),
            "db": (parsed.path or "/petlumina").lstrip("/"),
            "charset": "utf8mb4",
            "autocommit": True,
        }
        self._pool: Any = None

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            import aiomysql

            self._pool = await aiomysql.create_pool(minsize=1, maxsize=3, **self._cfg)
        return self._pool

    async def get(self) -> ModelConfig | None:
        pool = await self._ensure_pool()
        import aiomysql

        async with pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT provider,base_url,model,api_key_cipher,enabled,updated_by,"
                "update_time FROM " + _TABLE + " WHERE id=1"
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return ModelConfig(
            provider=str(row["provider"]),
            base_url=str(row["base_url"]),
            model=str(row["model"]),
            api_key_cipher=str(row["api_key_cipher"]),
            enabled=bool(row["enabled"]),
            updated_by=str(row["updated_by"]) if row["updated_by"] is not None else None,
            update_time=str(row["update_time"]) if row["update_time"] is not None else None,
        )

    async def save(self, config: ModelConfig) -> ModelConfig:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO "
                + _TABLE
                + " (id,provider,base_url,model,api_key_cipher,enabled,updated_by,update_time)"
                " VALUES (1,%s,%s,%s,%s,%s,%s,NOW())"
                " ON DUPLICATE KEY UPDATE provider=VALUES(provider),"
                " base_url=VALUES(base_url),model=VALUES(model),"
                " api_key_cipher=VALUES(api_key_cipher),enabled=VALUES(enabled),"
                " updated_by=VALUES(updated_by),update_time=NOW()",
                (
                    config.provider,
                    config.base_url,
                    config.model,
                    config.api_key_cipher,
                    1 if config.enabled else 0,
                    config.updated_by,
                ),
            )
        return config

    async def aclose(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None


def create_model_config_store(settings: Settings) -> ModelConfigStore:
    if settings.repo_backend == "mysql":
        if not settings.mysql_dsn:
            raise ModelConfigStoreError("repo_backend=mysql 但 PET_AGENT_MYSQL_DSN 为空")
        return MySqlModelConfigStore(settings.mysql_dsn)
    return InMemoryModelConfigStore(settings.model_config_file or None)
