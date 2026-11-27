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

from .core.pricing import ModelPrice

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

    # ---- 管理端模型配置 ----
    # 开启后可用管理端配置覆盖上面的 LLM_*；未配置/禁用时仍回退环境变量
    model_config_enabled: bool = True
    # 主密钥；为空时自动生成 model_config_key_file，生产建议用 KMS/Vault 注入
    config_secret: str = Field(default="", repr=False)
    model_config_key_file: str = "data/model-config.key"
    model_config_file: str = "data/model-config.json"

    # ---- 成本估算 ----
    # 按模型配置单价（USD / 1M tokens），只用于管理端展示；
    # 未配置的模型返回 cost_usd=null，不猜价格。
    model_prices: dict[str, ModelPrice] = Field(default_factory=dict)

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
    # 跟随/续传单次最长挂多久（秒）：到了先返回，客户端再连一次；别让中间层替我们掐
    run_follow_timeout_s: float = Field(default=90.0, gt=0)
    # 跟随轮询间隔：0.05s → 首 token 最坏多等 50ms，够小
    run_follow_poll_s: float = Field(default=0.05, gt=0, le=1.0)
    # 僵尸 run 收敛阈值（秒）：开始时间超过它还在 running，只能是进程没来得及收尾。
    # 必须大于 run_deadline_s，否则会把还在正常跑的 run 误判成僵尸。
    stale_run_timeout_s: float = Field(default=900.0, gt=0)
    # 巡检间隔（秒）：0 表示只在启动时扫一次
    run_sweep_interval_s: float = Field(default=60.0, ge=0)

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
    # 失败退避（B4）：第 n 次失败后等待 min(base * 2^(n-1), cap) 秒再重投
    task_retry_base_s: float = Field(default=5.0, ge=0)
    task_retry_cap_s: float = Field(default=600.0, ge=0)
    # 死信自动重投（默认关闭：死信通常意味着代码/数据问题，自动重投只会刷日志）
    task_dlq_redrive_interval_s: float = Field(default=0.0, ge=0)
    task_dlq_max_redrives: int = Field(default=3, ge=0, le=10)
    task_dlq_redrive_limit: int = Field(default=5, ge=1, le=100)
    # 死信告警阈值（条）：某 topic 的死信数 >= 阈值时打 WARN 并计数；0 = 关闭。
    # 默认 1——死信本身即异常，不该等人工翻管理端才发现。告警依赖巡检，
    # task_sweep_interval_s <= 0 时不会触发。
    task_dlq_alert_threshold: int = Field(default=1, ge=0)

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
            # 允许把 key 只放在管理端配置里；进程可以先启动，/readyz 会等待管理员配置
            if not self.llm_api_key and not self.model_config_enabled:
                raise ValueError("生产环境必须配置 PET_AGENT_LLM_API_KEY 或开启管理端模型配置")
            if self.auth_mode == "header":
                raise ValueError("生产环境禁止 auth_mode=header：不能信任客户端自称的用户 ID")
        return self
