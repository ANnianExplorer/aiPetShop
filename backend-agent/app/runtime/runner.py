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
from ..core.metrics import RUNS, TOKENS, metrics
from ..domain.events import Event, EventType
from ..domain.models import Message, Role, Run, RunStatus, StepKind, Usage, dedupe_citations
from ..domain.router import classify
from ..graph import SYSTEM_PROMPT
from ..llm.base import ChatModel
from ..memory import MemoryService
from ..profile import ProfileService
from ..storage.base import AgentRepository
from ..tasks.base import TaskQueue, TaskQueueFull
from ..tools import ToolGateway
from .eventlog import EventStore
from .follow import follow_events
from .supervisor import RunSupervisor

FALLBACK_ANSWER = "（这次没有生成内容，换个说法再问我一次？）"
run_log = logging.getLogger("agent.run")
memory_log = logging.getLogger("agent.memory")
profile_log = logging.getLogger("agent.profile")


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


@dataclass
class _StreamContext:
    """`_drive` 与 `stream` 之间的交接牌：这次到底有没有可托管的新 run。

    - `run_id`：新 run 建出来后填上，表示"后续事件可以去事件日志里等"；
    - `replay_only`：幂等命中了已有 run，事件是现成的回放，不该再被后台接管
      （否则会重新驱动一次执行，等于把 I16 撕开）。
    """

    run_id: str | None = None
    replay_only: bool = False


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
        tasks: TaskQueue | None = None,
        profiles: ProfileService | None = None,
        supervisor: RunSupervisor | None = None,
    ) -> None:
        self._settings = settings
        self._repo = repo
        self._gateway = gateway
        self._model = model
        self._graph = graph
        self._eventlog = eventlog
        self._memory = memory
        self._tasks = tasks
        self._profiles = profiles
        self._supervisor = supervisor or RunSupervisor()

    async def stream(self, cmd: ChatCommand, caller: Caller) -> AsyncIterator[Event]:
        """对外的唯一入口：先同步拿到首事件，再把执行交给后台任务。

        首事件（route / error / 幂等回放的第一条）必须留在请求路径里：客户端要它才知道
        run_id，重连才有游标可谈。从第二条事件起一律走事件日志——请求路径只是"读者"，
        它断开不会影响写者（后台任务）。
        """
        ctx = _StreamContext()
        drive = self._drive(cmd, caller, ctx)
        try:
            first = await anext(drive)
        except StopAsyncIteration:
            return

        if ctx.replay_only or ctx.run_id is None:
            # 没有可托管的 run：要么是幂等回放（事件已经现成），要么压根没建出 run
            # （模型未配置）。这两种情况都没有"续传"可言，原样转发即可。
            yield first
            async for event in drive:
                yield event
            return

        run_id = ctx.run_id
        # 先托管、再交付首事件：客户端可能收到 route 就断（切后台），
        # 若先 yield 再 spawn，那一瞬间的断开仍会把 run 冲掉——窗口小，但不是零。
        self._supervisor.spawn(self._drain(drive, run_id), name=f"run:{run_id}")
        yield first
        async for event in follow_events(
            self._eventlog,
            self._repo,
            run_id,
            first.seq,
            poll_s=self._settings.run_follow_poll_s,
            idle_timeout_s=self._settings.run_follow_timeout_s,
        ):
            yield event

    async def _drain(self, drive: AsyncIterator[Event], run_id: str) -> None:
        """后台把运行跑完：事件由 `_record` 直接写进日志，这里只负责推进执行。

        绝不能在客户端断开时被取消——"运行的生命周期属于 run，不属于这条连接"。
        只有进程退出（supervisor.aclose）才会取消它，届时 `_drive` 的 finally 会把
        run 收成 cancelled，不留 `running` 僵尸。
        """
        try:
            async for _event in drive:
                pass
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # `_drive` 已把 AgentError 转成 error 事件，这里只兜底
            log_event(
                run_log,
                logging.ERROR,
                "run drain crashed",
                run_id=run_id,
                error=f"{type(exc).__name__}: {exc}",
            )
        finally:
            with contextlib.suppress(Exception):
                await drive.aclose()

    async def _drive(
        self, cmd: ChatCommand, caller: Caller, ctx: _StreamContext
    ) -> AsyncIterator[Event]:
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
                    ctx.replay_only = True
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
                ctx.replay_only = True
                async for event in self._replay(session.id, run):
                    yield event
                return
            run_id = run.id
            ctx.run_id = run_id
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
                "profile_lines": await self._profile_context(caller.user_id, cmd.pet_id),
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
            metrics.inc(RUNS, {"route": decision.route.value, "status": RunStatus.SUCCEEDED.value})
            metrics.inc(TOKENS, {"direction": "prompt"}, usage.prompt_tokens)
            metrics.inc(TOKENS, {"direction": "completion"}, usage.completion_tokens)
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

            await self._observe(caller.user_id, cmd.pet_id, cmd.message, run_id=run_id)

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

    async def _observe(
        self, user_id: str, pet_id: str | None, text: str, *, run_id: str | None = None
    ) -> None:
        """记忆写入走旁路队列：不占响应时间；队列不可用时退回同步，绝不丢。"""
        if self._memory is None:
            return
        if self._tasks is not None:
            try:
                await self._tasks.publish(
                    "agent.memory.observe",
                    key=f"{user_id}:{run_id or ''}",
                    payload={"user_id": user_id, "pet_id": pet_id, "text": text},
                )
                return
            except TaskQueueFull:
                log_event(memory_log, logging.WARNING, "task queue full, memory inline")
        with contextlib.suppress(Exception):
            await self._memory.observe(user_id, pet_id, text)

    async def _profile_context(self, user_id: str, pet_id: str | None) -> list[str]:
        """画像只贡献「风险 / 待办」两行；没有画像或读失败都不影响对话。"""
        if self._profiles is None:
            return []
        with contextlib.suppress(Exception):
            return await self._profiles.context_lines(user_id, pet_id)
        return []

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
        metrics.inc(RUNS, {"route": "unknown", "status": RunStatus.FAILED.value})
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
