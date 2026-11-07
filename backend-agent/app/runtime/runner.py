"""运行时编排：一次对话 = 建会话 → 召回记忆 → 存档 → 跑图 → 流式输出 → 落库 → 收尾。

这里只做「编排」，具体能力在 graph / gateway / storage / memory 里，便于替换。
四个硬约束：
1. 无论成功、失败还是客户端断开，`agent_run` 必须有终态（不留下永远 running 的脏数据）；
2. 事件先写事件存储再下推，客户端断线可用 `Last-Event-ID` 回放（内存或 Redis，见 ADR-0003）；
3. 用量按「图内 LLM 调用 + 最终流式生成」相加，不漏算；
4. 记忆是增强项不是依赖：召回/写入失败只记日志，绝不让对话失败。
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from ..config import Settings
from ..core.errors import AgentError, ModelNotConfigured, RunTimeout
from ..core.logging import log_event, run_id_var, user_id_var
from ..domain.events import Event, EventType
from ..domain.models import Message, Role, Run, RunStatus, StepKind, Usage, dedupe_citations
from ..domain.router import classify
from ..graph import SYSTEM_PROMPT
from ..llm.base import ChatModel
from ..memory import MemoryService
from ..storage.base import AgentRepository
from ..tools import ToolGateway
from .eventlog import EventStore

FALLBACK_ANSWER = "（这次没有生成内容，换个说法再问我一次？）"
run_log = logging.getLogger("agent.run")
memory_log = logging.getLogger("agent.memory")


@dataclass(frozen=True)
class ChatCommand:
    message: str
    session_id: str | None = None
    pet_id: str | None = None
    channel: str = "app"
    # 客户端为每条消息生成的幂等键：重试同一个键时回放已有 run，不重复调用模型
    client_message_id: str | None = None


@dataclass(frozen=True)
class Caller:
    """可信调用方：user_id 由服务端从 token 解析，永远不来自请求体。"""

    user_id: str
    token: str


class AgentRunner:
    def __init__(
        self,
        *,
        settings: Settings,
        repo: AgentRepository,
        gateway: ToolGateway,
        model: ChatModel | None,
        graph: Any,
        eventlog: EventStore,
        memory: MemoryService | None = None,
    ) -> None:
        self._settings = settings
        self._repo = repo
        self._gateway = gateway
        self._model = model
        self._graph = graph
        self._eventlog = eventlog
        self._memory = memory

    async def stream(self, cmd: ChatCommand, caller: Caller) -> AsyncIterator[Event]:
        if self._model is None or self._graph is None:
            yield await self._record(
                None,
                Event(EventType.ERROR, ModelNotConfigured("模型未配置：请设置 PET_AGENT_LLM_API_KEY").to_payload()),
            )
            return

        started = time.perf_counter()
        user_id_var.set(caller.user_id)
        decision = classify(cmd.message)
        run_id: str | None = None
        terminal = False

        try:
            session = await self._repo.get_or_create_session(
                cmd.session_id, caller.user_id, cmd.pet_id, cmd.channel, cmd.message[:24]
            )
            # 幂等快路径：同一 key 已经跑过就直接回放，不建消息、不调模型、不重复计费。
            # 按 user 维度查而不是 session：首次请求可能失败在会话建出来之前。
            if cmd.client_message_id:
                existing = await self._repo.find_run_by_idempotency(
                    caller.user_id, cmd.client_message_id
                )
                if existing is not None:
                    log_event(
                        run_log,
                        logging.INFO,
                        "run replayed",
                        session_id=session.id,
                        run_id=existing.id,
                        idempotency_key=cmd.client_message_id,
                    )
                    async for event in self._replay(session.id, existing):
                        yield event
                    return

            history = await self._repo.history(session.id, self._settings.history_limit)
            memory_lines = await self._recall(caller.user_id, cmd.pet_id)
            user_message = await self._repo.add_message(
                Message(id="", session_id=session.id, role=Role.USER, content=cmd.message)
            )
            run = await self._repo.start_run(
                Run(
                    id="",
                    session_id=session.id,
                    user_id=caller.user_id,
                    user_message_id=user_message.id,
                    route=decision.route,
                    intent=decision.intent,
                    model=self._model.name,
                    idempotency_key=cmd.client_message_id,
                )
            )
            if run.user_message_id and run.user_message_id != user_message.id:
                # 并发撞唯一键：本次新建的 user_message 没被采用，回放已落库的那次运行
                log_event(
                    run_log,
                    logging.INFO,
                    "run replayed",
                    session_id=session.id,
                    run_id=run.id,
                    idempotency_key=cmd.client_message_id,
                    reason="unique_key_race",
                )
                async for event in self._replay(session.id, run):
                    yield event
                return
            run_id = run.id
            self._gateway.reset_run(run_id)
            run_id_var.set(run_id)
            log_event(
                run_log,
                logging.INFO,
                "run started",
                user_id=caller.user_id,
                session_id=session.id,
                route=decision.route.value,
                intent=decision.intent.value,
                channel=cmd.channel,
                msg_chars=len(cmd.message),
                memory_facts=len(memory_lines),
            )

            yield await self._record(
                run_id,
                Event(
                    EventType.ROUTE,
                    {
                        "session_id": session.id,
                        "run_id": run_id,
                        "route": decision.route.value,
                        "intent": decision.intent.value,
                        "reason": decision.reason,
                    },
                ),
            )

            state: dict[str, Any] = {
                "question": cmd.message,
                "channel": cmd.channel,
                "user_id": caller.user_id,
                "token": caller.token,
                "pet_id": cmd.pet_id,
                "run_id": run_id,
                "history": history,
                "memory_lines": memory_lines,
                "citations": [],
                "hops": 0,
            }

            try:
                result = await asyncio.wait_for(
                    self._graph.ainvoke(
                        state, config={"configurable": {"thread_id": run_id}}
                    ),
                    timeout=self._settings.run_deadline_s,
                )
            except TimeoutError as exc:
                raise RunTimeout(f"运行超过 {self._settings.run_deadline_s:.0f} 秒未完成") from exc

            steps = list(result.get("steps") or [])
            await self._repo.add_steps(run_id, steps)
            for step in steps:
                if getattr(step, "kind", None) == StepKind.TOOL:
                    yield await self._record(
                        run_id,
                        Event(
                            EventType.TOOL,
                            {
                                "name": step.name,
                                "status": step.status.value,
                                "latency_ms": step.latency_ms,
                            },
                        ),
                    )

            # 正常终止时由节点给出 answer_messages；达到 hop 上限时退回图内上下文
            # （此时最后一条是工具结果，模型据此收口，而不是把用户问题再复述一遍）。
            answer_messages = (
                result.get("answer_messages")
                or result.get("messages")
                or [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": cmd.message},
                ]
            )

            parts: list[str] = []
            stream_usage = Usage()
            async for chunk in self._model.stream(answer_messages):
                if chunk.text:
                    parts.append(chunk.text)
                    yield await self._record(run_id, Event(EventType.DELTA, {"text": chunk.text}))
                if chunk.usage is not None:
                    stream_usage = chunk.usage

            answer = "".join(parts).strip() or FALLBACK_ANSWER
            citations = dedupe_citations(list(result.get("citations") or []))
            usage = (
                Usage(
                    int(result.get("prompt_tokens") or 0),
                    int(result.get("completion_tokens") or 0),
                )
                + stream_usage
            )

            assistant = await self._repo.add_message(
                Message(
                    id="",
                    session_id=session.id,
                    role=Role.ASSISTANT,
                    content=answer,
                    run_id=run_id,
                    citations=citations,
                    meta={
                        "route": decision.route.value,
                        "intent": decision.intent.value,
                        "reason": decision.reason,
                        "model": self._model.name,
                        "memory_facts": len(memory_lines),
                    },
                )
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            await self._repo.finish_run(run_id, RunStatus.SUCCEEDED, usage, latency_ms)
            terminal = True
            log_event(
                run_log,
                logging.INFO,
                "run finished",
                session_id=session.id,
                route=decision.route.value,
                steps=len(steps),
                citations=len(citations),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                answer_chars=len(answer),
                latency_ms=latency_ms,
            )

            await self._observe(caller.user_id, cmd.pet_id, cmd.message)

            yield await self._record(
                run_id,
                Event(
                    EventType.DONE,
                    {
                        "run_id": run_id,
                        "session_id": session.id,
                        "message_id": assistant.id,
                        "route": decision.route.value,
                        "intent": decision.intent.value,
                        "answer": answer,
                        "citations": [c.to_dict() for c in citations],
                        "steps": [s.to_dict() for s in steps],
                        "usage": {
                            "prompt_tokens": usage.prompt_tokens,
                            "completion_tokens": usage.completion_tokens,
                        },
                        "latency_ms": latency_ms,
                    },
                ),
            )

        except AgentError as exc:
            terminal = True
            await self._finish_failed(run_id, exc, started)
            yield await self._record(run_id, Event(EventType.ERROR, exc.to_payload()))
        except Exception as exc:  # 兜底：任何未预期异常都要落一条可排查的错误
            terminal = True
            await self._finish_failed(run_id, AgentError(f"{type(exc).__name__}: {exc}"), started)
            yield await self._record(
                run_id,
                Event(EventType.ERROR, {"code": "internal_error", "message": "服务内部错误", "retryable": False}),
            )
        finally:
            if run_id is not None and not terminal:
                # 客户端断开 / 任务被取消：run 不能永远停在 running
                with contextlib.suppress(Exception):
                    await self._repo.finish_run(
                        run_id,
                        RunStatus.CANCELLED,
                        Usage(),
                        int((time.perf_counter() - started) * 1000),
                        "客户端断开或任务被取消",
                    )

    # ------------------------------------------------------------------ 回放
    async def _replay(self, session_id: str, run: Run) -> AsyncIterator[Event]:
        """回放一次已完成的运行，而不是重新执行。

        优先用事件日志里的原始事件（保真，客户端拿到的和第一次一模一样）；
        事件已过期（TTL/进程重启）时退化为按库里的消息重建一条最小事件流——
        宁可少一个 delta，也不能报错或让客户端永远转圈。
        """
        events = await self._eventlog.events(run.id, 0)
        if events:
            for event in events:
                if event.type is EventType.DONE:
                    event = Event(
                        EventType.DONE, {**event.data, "replayed": True}, event.seq
                    )
                yield event
            return

        messages = await self._repo.list_messages(session_id, limit=2)
        answer = next(
            (m.content for m in reversed(messages) if m.role is Role.ASSISTANT), ""
        )
        yield Event(
            EventType.ROUTE,
            {
                "session_id": session_id,
                "run_id": run.id,
                "route": run.route.value,
                "intent": run.intent.value,
                "reason": "replay:from_db",
            },
            1,
        )
        yield Event(
            EventType.DONE,
            {
                "session_id": session_id,
                "run_id": run.id,
                "route": run.route.value,
                "intent": run.intent.value,
                "answer": answer,
                "citations": [],
                "steps": [],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "latency_ms": 0,
                "replayed": True,
                "replay_mode": "from_db",
            },
            2,
        )

    # ------------------------------------------------------------------ 记忆
    async def _recall(self, user_id: str, pet_id: str | None) -> list[str]:
        if self._memory is None:
            return []
        try:
            return await self._memory.recall_lines(user_id, pet_id)
        except Exception as exc:  # 记忆不可用不影响对话
            log_event(memory_log, logging.WARNING, "memory recall failed", error=type(exc).__name__)
            return []

    async def _observe(self, user_id: str, pet_id: str | None, text: str) -> None:
        if self._memory is None:
            return
        with contextlib.suppress(Exception):
            await self._memory.observe(user_id, pet_id, text)

    # ------------------------------------------------------------------ 内部
    async def _finish_failed(self, run_id: str | None, err: AgentError, started: float) -> None:
        if run_id is None:
            return
        latency_ms = int((time.perf_counter() - started) * 1000)
        with contextlib.suppress(Exception):
            await self._repo.finish_run(
                run_id,
                RunStatus.FAILED,
                Usage(),
                latency_ms,
                err.message[:500],
            )
        log_event(
            run_log,
            logging.WARNING,
            "run failed",
            code=err.code,
            retryable=err.retryable,
            latency_ms=latency_ms,
        )

    async def _record(self, run_id: str | None, event: Event) -> Event:
        if run_id is None:
            return event
        return await self._eventlog.append(run_id, event)
