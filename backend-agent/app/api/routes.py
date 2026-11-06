"""HTTP 路由：只做协议转换（取值 → 校验 → 调运行时 → 编码 SSE），不放业务逻辑。"""

from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from ..config import Settings
from ..core.errors import Forbidden, InvalidRequest, NotFound, Unauthorized
from ..domain.events import Event
from ..runtime import Caller, ChatCommand, RunEventLog, AgentRunner
from ..storage.base import AgentRepository
from .schemas import ChatRequest, HealthOut, MessageOut, MessagesOut

router = APIRouter()

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
    settings: Settings = request.app.state.settings
    resolver = request.app.state.identity
    try:
        return await resolver.resolve(
            _token(request), header_user_id=request.headers.get("x-user-id")
        )
    except Unauthorized:
        raise
    except Exception as exc:  # 后端不可达时不能伪装成"未登录"
        raise InvalidRequest(f"身份校验失败：{type(exc).__name__}") from exc


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


@router.post("/agent/chat")
async def chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    settings: Settings = request.app.state.settings
    if payload.channel not in settings.allowed_channels:
        raise Forbidden(f"通道 {payload.channel} 未开放")

    message = payload.message.strip()
    if not message:
        raise InvalidRequest("message 不能为空")

    identity = await _identity(request)
    runner: AgentRunner = request.app.state.runner
    command = ChatCommand(
        message=message,
        session_id=payload.session_id,
        pet_id=payload.pet_id,
        channel=payload.channel,
    )

    async def events() -> AsyncIterator[str]:
        async for event in runner.stream(command, Caller(identity.user_id, identity.token)):
            yield event.to_sse()

    return StreamingResponse(events(), media_type="text/event-stream", headers=SSE_HEADERS)


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

    log: RunEventLog = request.app.state.eventlog
    pending = log.events(run_id, after_seq)

    async def replay() -> AsyncIterator[str]:
        for event in pending:
            yield event.to_sse()

    return StreamingResponse(replay(), media_type="text/event-stream", headers=SSE_HEADERS)


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
