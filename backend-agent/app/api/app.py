"""应用装配：把配置、存储、工具、模型、图、运行时串起来，并暴露给测试替换的点。

`create_app()` 的所有依赖都可以注入（model / repo / http_client），
所以测试不需要真模型、真 MySQL，也不需要 monkeypatch 全局变量。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import Settings
from ..core.errors import AgentError
from ..core.logging import configure_logging
from ..graph import build_graph
from ..llm import ChatModel, build_model
from ..runtime import AgentRunner, RunEventLog
from ..storage import AgentRepository, create_repository
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
) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)
    http_owned = http_client is None
    http = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(settings.backend_timeout_s, connect=5.0)
    )

    repository = repo or create_repository(settings)
    registry = build_registry()

    async def audit(audit_record: ToolAudit) -> None:
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
            settings.backend_base_url, token, http, timeout_s=settings.backend_timeout_s
        )

    model_owned = False
    if model is None and settings.model_configured:
        model = build_model(settings)
        model_owned = True

    graph = (
        build_graph(model, gateway, settings, backend_factory) if model is not None else None
    )
    eventlog = RunEventLog(settings.event_log_capacity, settings.event_log_ttl_s)
    runner = AgentRunner(
        settings=settings,
        repo=repository,
        gateway=gateway,
        model=model,
        graph=graph,
        eventlog=eventlog,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await repository.aclose()
            if model is not None and model_owned:
                await model.aclose()
            if http_owned:
                await http.aclose()

    app = FastAPI(title="PetLumina Pet-Agent", version="0.2.0", lifespan=lifespan)
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
    app.state.eventlog = eventlog
    app.state.runner = runner
    app.state.identity = IdentityResolver(settings, http)

    @app.exception_handler(AgentError)
    async def _agent_error(_: Request, exc: AgentError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=exc.to_payload())

    app.include_router(router)
    return app
