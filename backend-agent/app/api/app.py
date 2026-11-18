"""应用装配：把配置、存储、工具、模型、图、运行时串起来，并暴露给测试替换的点。

`create_app()` 的所有依赖都可以注入（model / repo / http_client / limiter / event_store），
所以测试不需要真模型、真 MySQL、真 Redis，也不需要 monkeypatch 全局变量。

依赖关系是单向的：api → runtime → graph → tools/storage/llm/memory → domain。
这里只做「接线」，任何业务判断都不该出现在这个文件里。
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import Settings
from ..core.circuit import CircuitBreaker
from ..core.errors import AgentError, CircuitOpen, RateLimited
from ..core.logging import configure_logging, log_event
from ..core.ratelimit import RateLimiter, create_rate_limiter
from ..graph import build_graph
from ..llm import ChatModel, build_model
from ..memory import MemoryService
from ..model_config import ConfigCipher, ModelConfigService, create_model_config_store
from ..profile import ProfileService
from ..rag import DocumentService
from ..rag.embedder import build_embedder
from ..runtime import AgentRunner
from ..runtime.eventlog import EventStore, create_event_store
from ..runtime.janitor import janitor_log, janitor_loop, sweep_once
from ..runtime.supervisor import RunSupervisor
from ..storage import AgentRepository, create_repository
from ..tasks import TOPICS, TaskQueue, create_task_queue
from ..tasks.base import TaskQueueFull
from ..tasks.consumers import build_handlers
from ..tasks.worker import TaskWorker
from ..tools import BackendClient, ToolAudit, ToolGateway, ToolPolicy, build_registry
from .deps import IdentityResolver
from .observability import RequestContextMiddleware
from .routes import router

task_log = logging.getLogger("agent.task")


def create_app(
    settings: Settings | None = None,
    *,
    model: ChatModel | None = None,
    repo: AgentRepository | None = None,
    http_client: httpx.AsyncClient | None = None,
    limiter: RateLimiter | None = None,
    event_store: EventStore | None = None,
    llm_breaker: CircuitBreaker | None = None,
    backend_breaker: CircuitBreaker | None = None,
    task_queue: TaskQueue | None = None,
    docs_service: Any = None,
    profiles_service: Any = None,
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    http_owned = http_client is None
    http = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(settings.backend_timeout_s, connect=5.0)
    )

    # 熔断器必须在 app 生命周期内共享：每个请求 new 一个，失败计数永远到不了阈值
    llm_breaker = llm_breaker or CircuitBreaker(
        "llm", threshold=settings.circuit_threshold, cooldown_s=settings.circuit_cooldown_s
    )
    backend_breaker = backend_breaker or CircuitBreaker(
        "backend", threshold=settings.circuit_threshold, cooldown_s=settings.circuit_cooldown_s
    )

    repository = repo or create_repository(settings)
    # 文档问答：服务与工具共享同一个实例，检索永远带 user_id
    document_service = docs_service or DocumentService(
        repository,
        build_embedder(settings),
        storage_dir=settings.doc_storage_dir,
        max_bytes=settings.doc_max_bytes,
    )
    registry = build_registry(docs=document_service)
    tasks = task_queue if task_queue is not None else create_task_queue(settings)
    # 画像服务：读接口、旁路重算、对话上下文注入共用同一实例（去抖状态也在这里）
    profile_service = profiles_service or ProfileService(
        repository,
        keep_versions=settings.profile_keep_versions,
        refresh_ttl_s=settings.profile_refresh_ttl_s,
        vaccine_stale_days=settings.profile_vaccine_stale_days,
    )

    async def audit(audit_record: ToolAudit) -> None:
        # 有队列就走旁路：审计落库不该占着对话的响应时间；
        # 投递失败（队列满/中间件挂了）立刻退回同步写，宁可慢也不丢审计。
        if tasks is not None:
            try:
                await tasks.publish(
                    "agent.audit.tool",
                    key=f"{audit_record.run_id}:{audit_record.name}",
                    payload={
                        "run_id": audit_record.run_id,
                        "name": audit_record.name,
                        "ok": audit_record.ok,
                        "code": audit_record.code,
                        "latency_ms": audit_record.latency_ms,
                        "args_digest": audit_record.args_digest,
                    },
                )
                return
            except TaskQueueFull:
                pass
        await repository.audit_tool_call(
            audit_record.run_id,
            audit_record.name,
            audit_record.ok,
            audit_record.code,
            audit_record.latency_ms,
            audit_record.args_digest,
        )

    gateway = ToolGateway(
        registry,
        ToolPolicy(),
        auditor=audit,
        max_calls_per_run=settings.max_tool_calls_per_run,
    )

    def backend_factory(token: str) -> BackendClient:
        return BackendClient(
            settings.backend_base_url,
            token,
            http,
            timeout_s=settings.backend_timeout_s,
            breaker=backend_breaker,
        )

    model_owned = False
    model_config_service: ModelConfigService | None = None
    if model is None and settings.model_config_enabled:
        model_store = create_model_config_store(settings)
        model_config_service = ModelConfigService(
            settings,
            model_store,
            ConfigCipher(settings.config_secret, settings.model_config_key_file),
            lambda cfg: build_model(cfg, breaker=llm_breaker),
        )
        # 真正的模型要等 lifespan/bootstrap 读取 DB/文件后再建；显式注入 model 的测试不走这里
    elif model is None and settings.model_configured:
        model = build_model(settings, breaker=llm_breaker)
        model_owned = True

    graph = (
        build_graph(model, gateway, settings, backend_factory, docs=document_service)
        if model is not None
        else None
    )
    store = event_store or create_event_store(settings)
    memory = MemoryService(repository)
    worker = (
        TaskWorker(
            tasks,
            build_handlers(memory, repository, docs=document_service, profiles=profile_service),
            topics=list(TOPICS),
            sweep_interval_s=settings.task_sweep_interval_s,
            visible_timeout_s=settings.task_visible_timeout_s,
            dlq_redrive_interval_s=settings.task_dlq_redrive_interval_s,
            dlq_max_redrives=settings.task_dlq_max_redrives,
            dlq_redrive_limit=settings.task_dlq_redrive_limit,
        )
        if tasks
        else None
    )
    supervisor = RunSupervisor()
    runner = AgentRunner(
        settings=settings,
        repo=repository,
        gateway=gateway,
        model=model,
        graph=graph,
        eventlog=store,
        memory=memory,
        tasks=tasks,
        profiles=profile_service,
        supervisor=supervisor,
    )
    rate_limiter = limiter or create_rate_limiter(settings)

    def apply_runtime_model(new_model: ChatModel | None, source: str) -> None:
        """配置服务切换模型后的唯一接线点：重建 graph，再让 runner 看到新引用。"""
        nonlocal model, graph
        model = new_model
        graph = (
            build_graph(new_model, gateway, settings, backend_factory, docs=document_service)
            if new_model is not None
            else None
        )
        runner.reconfigure(model=new_model, graph=graph)
        app.state.graph = graph
        app.state.model_name = new_model.name if new_model is not None else None
        app.state.model_source = source
        app.state.model_error = model_config_service.last_error if model_config_service else None

    if model_config_service is not None:
        model_config_service.set_on_change(apply_runtime_model)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        # 先从 DB/文件配置或 env 兜底建立运行时模型；失败不拖垮进程，
        # 管理员仍可通过 /agent/admin/model-config 修好配置后热应用。
        if model_config_service is not None:
            try:
                await model_config_service.bootstrap()
            except Exception as exc:
                log_event(task_log, logging.WARNING, "model config bootstrap failed",
                          error=type(exc).__name__)
        # 先扫一遍上一轮进程消失留下的僵尸 run，再接收新请求：
        # 它们停在 running 会让管理端误以为「还在跑」，前端重连也永远等不到 done。
        with contextlib.suppress(Exception):
            reaped = await sweep_once(repository, timeout_s=settings.stale_run_timeout_s)
            if reaped:
                log_event(
                    janitor_log,
                    logging.WARNING,
                    "stale runs reaped on startup",
                    count=len(reaped),
                    sample=reaped[:5],
                )
        if settings.run_sweep_interval_s > 0:
            supervisor.spawn(
                janitor_loop(
                    repository,
                    timeout_s=settings.stale_run_timeout_s,
                    interval_s=settings.run_sweep_interval_s,
                ),
                name="run-janitor",
            )
        # 先补偿上一次进程崩在「在途」里的消息，再开消费协程：
        # 顺序反了会和新 consumer 抢同一条消息。
        if tasks is not None:
            with contextlib.suppress(Exception):
                recovered = await tasks.recover(list(TOPICS))
                if recovered:
                    log_event(task_log, logging.WARNING, "task inflight recovered on startup",
                              recovered=recovered)
        if worker is not None:
            await worker.start()
        try:
            yield
        finally:
            # 先收后台运行：客户端可能早断线了，但 run 还得有个终态才能收场
            await supervisor.aclose()
            if worker is not None:
                await worker.stop()
            if tasks is not None:
                await tasks.aclose()
            await repository.aclose()
            await store.aclose()
            await rate_limiter.aclose()
            if model_config_service is not None:
                await model_config_service.aclose()
            elif model is not None and model_owned:
                await model.aclose()
            if http_owned:
                await http.aclose()

    app = FastAPI(title="PetLumina Pet-Agent", version="0.3.0", lifespan=lifespan)
    # Starlette 的中间件是「后加的先执行」：
    # CORS 先加 → 在内层，负责给真实响应补跨域头；请求上下文后加 → 在最外层，
    # 保证连 CORS 预检、异常响应都带 x-request-id 和访问日志。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    app.add_middleware(RequestContextMiddleware)

    app.state.settings = settings
    app.state.repo = repository
    app.state.gateway = gateway
    app.state.registry = registry
    app.state.graph = graph
    app.state.eventlog = store
    app.state.runner = runner
    app.state.supervisor = supervisor
    app.state.memory = memory
    app.state.limiter = rate_limiter
    app.state.identity = IdentityResolver(settings, http)
    app.state.llm_breaker = llm_breaker
    app.state.backend_breaker = backend_breaker
    app.state.tasks = tasks
    app.state.task_worker = worker
    app.state.docs = document_service
    app.state.profiles = profile_service
    app.state.model_config = model_config_service
    app.state.model_name = model.name if model is not None else None
    app.state.model_source = (
        "injected" if model is not None and not model_owned
        else "env" if model_owned
        else "none"
    )
    app.state.model_error = model_config_service.last_error if model_config_service else None

    @app.exception_handler(AgentError)
    async def _agent_error(_: Request, exc: AgentError) -> JSONResponse:
        headers = {}
        if isinstance(exc, RateLimited | CircuitOpen):
            # 客户端据此决定退避，不用猜
            headers["Retry-After"] = str(exc.retry_after_s)
        return JSONResponse(status_code=exc.http_status, content=exc.to_payload(), headers=headers)

    app.include_router(router)
    return app
