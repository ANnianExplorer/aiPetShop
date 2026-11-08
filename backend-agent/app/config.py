"""运行时配置：全部来自 `PET_AGENT_` 前缀的环境变量或同目录 `.env`。

原则：
1. 安全相关的项默认「失败关闭」——生产环境缺密钥、或用 header 认证模式，直接拒绝启动；
2. 密钥字段 `repr=False`，不会被日志/异常栈打印出来；
3. 所有阈值集中在此，节点与服务不各自硬编码。
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AuthMode = Literal["backend", "header"]
RepoBackend = Literal["memory", "mysql"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PET_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["dev", "test", "prod"] = "dev"

    # ---- 模型 ----
    llm_api_key: str = Field(default="", repr=False)
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    llm_timeout_s: float = Field(default=30.0, gt=0)
    llm_max_retries: int = Field(default=2, ge=0, le=5)

    # ---- 业务后端（Java /api/v1）----
    backend_base_url: str = "http://localhost:8080/api/v1"
    backend_timeout_s: float = Field(default=8.0, gt=0)
    # backend：拿 token 去 /auth/current 换用户身份（推荐）
    # header  ：信任 X-User-Id 请求头（仅 dev/test，生产禁用）
    auth_mode: AuthMode = "backend"
    identity_cache_ttl_s: int = Field(default=60, ge=0)

    # ---- 存储 ----
    repo_backend: RepoBackend = "memory"
    mysql_dsn: str = Field(default="", repr=False)

    # ---- 运行预算 ----
    max_tool_hops: int = Field(default=6, ge=1, le=20)
    max_tool_calls_per_run: int = Field(default=8, ge=1, le=50)
    # 单次 run 的 token 上限（0 表示不限）：超了立即中止，不让一次提问烧穿预算
    run_token_budget: int = Field(default=30000, ge=0)
    history_limit: int = Field(default=20, ge=0, le=100)
    run_deadline_s: float = Field(default=60.0, gt=0)
    event_log_capacity: int = Field(default=512, ge=16)
    event_log_ttl_s: float = Field(default=900.0, gt=0)
    # 事件流后端：memory 只能单副本续传；redis 用 Stream 支持多副本
    event_backend: Literal["memory", "redis"] = "memory"

    # ---- 配额 ----
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = Field(default=20, ge=1)
    rate_limit_per_day: int = Field(default=300, ge=1)
    rate_limit_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = Field(default="redis://localhost:6379/0", repr=False)
    # 熔断：下游连续失败 N 次后快速失败，冷却期放一个探测请求
    circuit_threshold: int = Field(default=5, ge=1, le=100)
    circuit_cooldown_s: float = Field(default=30.0, gt=0)

    # ---- 旁路任务队列（S1.9）----
    # off: 旁路工作同步执行（默认，行为与 S1.8 一致）；memory: 进程内队列；redis: 列表队列
    task_backend: Literal["off", "memory", "redis"] = "off"
    task_queue_size: int = Field(default=1000, ge=1)
    task_max_attempts: int = Field(default=3, ge=1, le=10)
    # 在途消息可见性超时：取走超过这么久还没 ack，就认为消费者已死、搬回队列重试
    task_visible_timeout_s: float = Field(default=120.0, gt=0)
    # 巡检间隔；<= 0 表示关闭巡检（只保留进程启动时的 recover）
    task_sweep_interval_s: float = Field(default=60.0, ge=0)

    # ---- 文档问答（RAG）----
    # hash：本地哈希嵌入（确定性、零网络）；openai：走兼容 /embeddings 的接口
    embed_backend: Literal["hash", "openai"] = "hash"
    embed_model: str = "text-embedding-3-small"
    embed_dim: int = Field(default=256, ge=32, le=4096)
    doc_storage_dir: str = "data/docs"
    doc_max_bytes: int = Field(default=20 * 1024 * 1024, ge=1024)

    # ---- 画像 ----
    profile_keep_versions: int = Field(default=20, ge=1, le=200)
    profile_refresh_ttl_s: int = Field(default=300, ge=0)
    profile_vaccine_stale_days: int = Field(default=300, ge=1)

    # ---- 通道策略 ----
    allowed_channels: tuple[str, ...] = ("app", "web", "internal")
    cors_origins: tuple[str, ...] = ("*",)

    # ---- 可观测 ----
    log_level: str = "INFO"

    @property
    def model_configured(self) -> bool:
        return bool(self.llm_api_key)

    @model_validator(mode="after")
    def _guard(self) -> Settings:
        if self.repo_backend == "mysql" and not self.mysql_dsn:
            raise ValueError("PET_AGENT_REPO_BACKEND=mysql 时必须提供 PET_AGENT_MYSQL_DSN")
        if self.env == "prod":
            if not self.llm_api_key:
                raise ValueError("生产环境必须配置 PET_AGENT_LLM_API_KEY")
            if self.auth_mode == "header":
                raise ValueError("生产环境禁止 auth_mode=header：不能信任客户端自称的用户 ID")
        return self
