"""HTTP 路由：只做协议转换（取值 → 校验 → 调运行时 → 编码 SSE），不放业务逻辑。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ..config import Settings
from ..core.errors import Forbidden, InvalidRequest, NotFound, RateLimited, Unauthorized
from ..core.logging import log_event
from ..core.ratelimit import RateLimiter
from ..memory import label_of
from ..runtime import AgentRunner, Caller, ChatCommand
from ..runtime.eventlog import EventStore
from ..storage.base import AgentRepository
from .schemas import (
    AdminDayUsage,
    AdminRunOut,
    AdminSessionDetail,
    AdminSessionItem,
    AdminSessionList,
    AdminStepOut,
    AdminUsageOut,
    ChatRequest,
    HealthOut,
    MemoryFactOut,
    MemoryOut,
    MessageOut,
    MessagesOut,
    UsageOut,
)

router = APIRouter()
ready_log = logging.getLogger("agent.readiness")

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _token(request: Request) -> str:
    token = request.headers.get("satoken") or ""
    if token:
        return token
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


async def _identity(request: Request):
    resolver = request.app.state.identity
    try:
        return await resolver.resolve(
            _token(request),
            header_user_id=request.headers.get("x-user-id"),
            header_role=request.headers.get("x-user-role"),
        )
    except Unauthorized:
        raise
    except Exception as exc:  # 后端不可达时不能伪装成"未登录"
        raise InvalidRequest(f"身份校验失败：{type(exc).__name__}") from exc


async def _admin_identity(request: Request):
    """管理员判定只认后端返回的 role；请求头伪造 role 在 backend 模式下无效。"""
    identity = await _identity(request)
    if not identity.is_admin:
        raise Forbidden("需要管理员权限")
    return identity


def _repo(request: Request) -> AgentRepository:
    return request.app.state.repo


@router.get("/healthz", response_model=HealthOut)
async def healthz(request: Request) -> HealthOut:
    settings: Settings = request.app.state.settings
    gateway = request.app.state.gateway
    return HealthOut(
        status="ok",
        repo=settings.repo_backend,
        model=settings.llm_model if settings.model_configured else None,
        model_configured=settings.model_configured,
        tools=list(gateway.names_for("app")),
        graph_ready=request.app.state.graph is not None,
        auth_mode=settings.auth_mode,
    )


@router.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    """就绪探针：区分「进程活着」（/healthz）与「能接流量」（本接口）。

    存储不可用或模型未配置都返回 503，让编排系统不要把流量打进来。
    """
    settings: Settings = request.app.state.settings
    checks: dict[str, str] = {}
    ready = True

    try:
        await _repo(request).ping()
        checks["repo"] = "ok"
    except Exception as exc:  # 依赖失败不能伪装成 200，也不能把堆栈返回给调用方
        checks["repo"] = type(exc).__name__
        ready = False

    if settings.model_configured:
        checks["model"] = "ok"
    else:
        checks["model"] = "not_configured"
        ready = False

    # 熔断打开时说明下游已经在连续失败：此时接流量只会把请求排进超时队列
    for name in ("llm_breaker", "backend_breaker"):
        breaker = getattr(request.app.state, name, None)
        if breaker is None:
            continue
        snap = breaker.snapshot()
        checks[f"circuit:{snap.name}"] = "ok" if snap.healthy else "open"
        if not snap.healthy:
            ready = False

    payload = {"status": "ready" if ready else "degraded", "checks": checks}
    log_event(ready_log, logging.WARNING if not ready else logging.INFO, "readiness check", **checks)
    return JSONResponse(payload, status_code=200 if ready else 503)


@router.post("/agent/chat")
async def chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    settings: Settings = request.app.state.settings
    if payload.channel not in settings.allowed_channels:
        raise Forbidden(f"通道 {payload.channel} 未开放")

    message = payload.message.strip()
    if not message:
        raise InvalidRequest("message 不能为空")

    identity = await _identity(request)
    limiter: RateLimiter = request.app.state.limiter
    quota_headers: dict[str, str] = {}
    if settings.rate_limit_enabled:
        decision = await limiter.hit(identity.user_id)
        if not decision.allowed:
            raise RateLimited(
                "请求太频繁，请稍后再试",
                retry_after_s=decision.retry_after_s,
                scope=decision.scope,
                limit=decision.limit,
            )
        quota_headers["X-RateLimit-Limit"] = str(decision.limit)
        quota_headers["X-RateLimit-Remaining"] = str(decision.remaining)

    runner: AgentRunner = request.app.state.runner
    command = ChatCommand(
        message=message,
        session_id=payload.session_id,
        pet_id=payload.pet_id,
        channel=payload.channel,
        client_message_id=payload.client_message_id,
    )

    async def events() -> AsyncIterator[str]:
        async for event in runner.stream(command, Caller(identity.user_id, identity.token)):
            yield event.to_sse()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={**SSE_HEADERS, **quota_headers},
    )


@router.get("/agent/runs/{run_id}/events")
async def replay_run(
    run_id: str,
    request: Request,
    after: int | None = Query(default=None, ge=0),
) -> StreamingResponse:
    """断线续传：`Last-Event-ID` 或 `?after=N` 之后的增量事件。"""
    identity = await _identity(request)
    repo = _repo(request)

    run = await repo.get_run(run_id)
    if run is None:
        raise NotFound("运行不存在")
    if await repo.get_session(run.session_id, identity.user_id) is None:
        raise NotFound("运行不存在")

    last_header = request.headers.get("last-event-id") or ""
    after_seq = after if after is not None else (int(last_header) if last_header.isdigit() else 0)

    log: EventStore = request.app.state.eventlog
    pending = await log.events(run_id, after_seq)

    async def replay() -> AsyncIterator[str]:
        for event in pending:
            yield event.to_sse()

    return StreamingResponse(replay(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/agent/usage/me", response_model=UsageOut)
async def usage_me(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
) -> UsageOut:
    """我这个账号最近 N 天的用量：给"这个月花了多少"和成本排查用。"""
    identity = await _identity(request)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    summary = await _repo(request).usage_summary(identity.user_id, since)
    return UsageOut(
        days=days,
        runs=summary.runs,
        prompt_tokens=summary.prompt_tokens,
        completion_tokens=summary.completion_tokens,
        total_tokens=summary.total_tokens,
        avg_latency_ms=summary.avg_latency_ms,
    )


@router.get("/agent/memory/me", response_model=MemoryOut)
async def memory_me(
    request: Request,
    pet_id: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=50),
) -> MemoryOut:
    """我这个账号（可选某只宠物）的长期事实记忆：给"它记住了什么"和排障用。"""
    identity = await _identity(request)
    facts = await _repo(request).list_memory_facts(identity.user_id, pet_id, limit)
    return MemoryOut(
        pet_id=pet_id,
        facts=[
            MemoryFactOut(
                id=f.id,
                key=f.key,
                label=label_of(f.key),
                value=f.value,
                confidence=f.confidence,
                update_time=f.update_time,
            )
            for f in facts
        ],
    )


@router.get("/agent/sessions/{session_id}/messages", response_model=MessagesOut)
async def session_messages(
    session_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
) -> MessagesOut:
    identity = await _identity(request)
    repo = _repo(request)
    session = await repo.get_session(session_id, identity.user_id)
    if session is None:
        raise NotFound("会话不存在")

    messages = await repo.list_messages(session_id, limit)
    return MessagesOut(
        session_id=session_id,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                run_id=m.run_id,
                citations=[c.to_dict() for c in m.citations],
                create_time=m.create_time,
            )
            for m in messages
        ],
    )


# ---------------------------------------------------------------- 管理端（只读）
admin_log = logging.getLogger("agent.admin")


@router.get("/agent/admin/sessions", response_model=AdminSessionList)
async def admin_sessions(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user_id: str | None = Query(default=None, max_length=32),
    q: str | None = Query(default=None, max_length=64),
) -> AdminSessionList:
    """全部会话列表：运营/客服排查的第一入口。"""
    await _admin_identity(request)
    total, items = await _repo(request).list_sessions(
        page=page, page_size=page_size, user_id=user_id, query=q
    )
    return AdminSessionList(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            AdminSessionItem(
                id=s.id,
                user_id=s.user_id,
                pet_id=s.pet_id,
                channel=s.channel,
                title=s.title,
                message_count=s.message_count,
                create_time=s.create_time,
            )
            for s in items
        ],
    )


@router.get("/agent/admin/sessions/{session_id}", response_model=AdminSessionDetail)
async def admin_session_detail(session_id: str, request: Request) -> AdminSessionDetail:
    """一个会话的全貌：消息流 + 每次运行的步骤轨迹。"""
    admin = await _admin_identity(request)
    repo = _repo(request)
    session = await repo.get_session_any(session_id)
    if session is None:
        raise NotFound("会话不存在")

    # 管理员看别人数据必须留痕：只记关系，不记内容
    log_event(
        admin_log,
        logging.INFO,
        "admin.access",
        admin_id=admin.user_id,
        target_user=session.user_id,
        session_id=session_id,
    )

    messages = await repo.list_messages(session_id, 200)
    runs = await repo.list_runs(session_id)
    return AdminSessionDetail(
        session=AdminSessionItem(
            id=session.id,
            user_id=session.user_id,
            pet_id=session.pet_id,
            channel=session.channel,
            title=session.title,
            message_count=session.message_count,
            create_time=session.create_time,
        ),
        messages=[
            MessageOut(
                id=m.id,
                role=m.role.value,
                content=m.content,
                run_id=m.run_id,
                citations=[c.to_dict() for c in m.citations],
                create_time=m.create_time,
            )
            for m in messages
        ],
        runs=[
            AdminRunOut(
                id=r.id,
                route=r.route.value,
                intent=r.intent.value,
                status=r.status.value,
                prompt_tokens=r.prompt_tokens,
                completion_tokens=r.completion_tokens,
                total_tokens=r.total_tokens,
                latency_ms=r.latency_ms,
                error=r.error,
                steps=[
                    AdminStepOut(
                        seq=s.seq,
                        kind=s.kind.value,
                        name=s.name,
                        status=s.status.value,
                        latency_ms=s.latency_ms,
                        error=s.error,
                    )
                    for s in r.steps
                ],
            )
            for r in runs
        ],
    )


@router.get("/agent/admin/memory", response_model=MemoryOut)
async def admin_memory(
    request: Request,
    user_id: str = Query(..., min_length=1, max_length=32),
    pet_id: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=50),
) -> MemoryOut:
    """管理员视角看某个账号记住了什么：抽取错了能当场发现。"""
    admin = await _admin_identity(request)
    log_event(
        admin_log,
        logging.INFO,
        "admin.access",
        admin_id=admin.user_id,
        target_user=user_id,
        scope="memory",
    )
    facts = await _repo(request).list_memory_facts(user_id, pet_id, limit)
    return MemoryOut(
        pet_id=pet_id,
        facts=[
            MemoryFactOut(
                id=f.id,
                key=f.key,
                label=label_of(f.key),
                value=f.value,
                confidence=f.confidence,
                update_time=f.update_time,
            )
            for f in facts
        ],
    )


@router.get("/agent/admin/usage", response_model=AdminUsageOut)
async def admin_usage(
    request: Request,
    days: int = Query(default=7, ge=1, le=90),
) -> AdminUsageOut:
    """全局用量与按天趋势：成本排查与容量预估用。"""
    await _admin_identity(request)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    overview = await _repo(request).usage_overview(since)
    return AdminUsageOut(
        days=days,
        runs=overview.runs,
        users=overview.users,
        prompt_tokens=overview.prompt_tokens,
        completion_tokens=overview.completion_tokens,
        total_tokens=overview.total_tokens,
        avg_latency_ms=overview.avg_latency_ms,
        by_day=[
            AdminDayUsage(day=d.day, runs=d.runs, tokens=d.tokens) for d in overview.by_day
        ],
    )
