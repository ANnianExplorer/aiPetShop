"""应用装配：把配置、存储、工具、模型、图、运行时串起来，并暴露给测试替换的点。

`create_app()` 的所有依赖都可以注入（model / repo / http_client / limiter / event_store），
所以测试不需要真模型、真 MySQL、真 Redis，也不需要 monkeypatch 全局变量。

依赖关系是单向的：api → runtime → graph → tools/storage/llm/memory → domain。
这里只做「接线」，任何业务判断都不该出现在这个文件里。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import Settings
from ..core.circuit import CircuitBreaker
from ..core.errors import AgentError, CircuitOpen, RateLimited
from ..core.logging import configure_logging
from ..core.ratelimit import RateLimiter, create_rate_limiter
from ..graph import build_graph
from ..llm import ChatModel, build_model
from ..memory import MemoryService
from ..runtime import AgentRunner
from ..runtime.eventlog import EventStore, create_event_store
from ..storage import AgentRepository, create_repository
from ..tasks import TOPICS, TaskQueue, create_task_queue
from ..tasks.base import TaskQueueFull
from ..tasks.consumers import build_handlers
from ..tasks.worker import TaskWorker
from ..tools import BackendClient, ToolAudit, ToolGateway, ToolPolicy, build_registry
from .deps import IdentityResolver
from .observability import RequestContextMiddleware
from .routes import router


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
    registry = build_registry()
    tasks = task_queue if task_queue is not None else create_task_queue(settings)

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
    if model is None and settings.model_configured:
        model = build_model(settings, breaker=llm_breaker)
        model_owned = True

    graph = (
        build_graph(model, gateway, settings, backend_factory) if model is not None else None
    )
    store = event_store or create_event_store(settings)
    memory = MemoryService(repository)
    worker = TaskWorker(tasks, build_handlers(memory, repository), topics=list(TOPICS)) if tasks else None
    runner = AgentRunner(
        settings=settings,
        repo=repository,
        gateway=gateway,
        model=model,
        graph=graph,
        eventlog=store,
        memory=memory,
        tasks=tasks,
    )
    rate_limiter = limiter or create_rate_limiter(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if worker is not None:
            await worker.start()
        try:
            yield
        finally:
            if worker is not None:
                await worker.stop()
            if tasks is not None:
                await tasks.aclose()
            await repository.aclose()
            await store.aclose()
            await rate_limiter.aclose()
            if model is not None and model_owned:
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
    app.state.memory = memory
    app.state.limiter = rate_limiter
    app.state.identity = IdentityResolver(settings, http)
    app.state.llm_breaker = llm_breaker
    app.state.backend_breaker = backend_breaker
    app.state.tasks = tasks
    app.state.task_worker = worker

    @app.exception_handler(AgentError)
    async def _agent_error(_: Request, exc: AgentError) -> JSONResponse:
        headers = {}
        if isinstance(exc, RateLimited | CircuitOpen):
            # 客户端据此决定退避，不用猜
            headers["Retry-After"] = str(exc.retry_after_s)
        return JSONResponse(status_code=exc.http_status, content=exc.to_payload(), headers=headers)

    app.include_router(router)
    return app
