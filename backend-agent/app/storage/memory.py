"""内存实现：零依赖，单测与本地开发用；语义必须与 MySQL 版一致。"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

from ..core.errors import Forbidden, NotFound
from ..core.ids import new_id
from ..domain.models import (
    DayUsage,
    MemoryFact,
    Message,
    ProfileSnapshot,
    Role,
    Run,
    RunDetail,
    RunStatus,
    Session,
    SessionSummary,
    Step,
    Usage,
    UsageOverview,
    UsageSummary,
)
from ..rag.models import Chunk, Document, DocumentStatus


class InMemoryRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._messages: dict[str, list[Message]] = {}
        self._runs: dict[str, dict[str, Any]] = {}
        self._steps: dict[str, list[Step]] = {}
        self._tool_calls: list[dict[str, Any]] = []
        self._audit_ids: set[str] = set()
        self._facts: dict[tuple[str, str, str], MemoryFact] = {}
        # 幂等键索引：(session_id, key) -> run_id，模拟库上的唯一键
        self._idem: dict[tuple[str, str], str] = {}
        # 文档问答：文档表 + 按 (user, sha) 去重索引 + 切片表
        self._documents: dict[str, Document] = {}
        self._doc_sha: dict[tuple[str, str], str] = {}
        self._chunks: dict[str, list[Chunk]] = {}
        # 画像快照：(user, pet) -> 版本列表（升序），模拟追加式版本表
        self._profiles: dict[tuple[str, str], list[ProfileSnapshot]] = {}

    # ------------------------------------------------------------ 会话
    async def get_or_create_session(
        self,
        session_id: str | None,
        user_id: str,
        pet_id: str | None,
        channel: str,
        title: str,
    ) -> Session:
        if session_id:
            existing = self._sessions.get(session_id)
            if existing is not None:
                if existing.user_id != user_id:
                    # 不暴露"该会话存在"这一事实，统一按无权限处理
                    raise Forbidden("会话不属于当前用户")
                return existing
        sid = session_id or new_id()
        session = Session(
            id=sid,
            user_id=user_id,
            channel=channel,
            pet_id=pet_id,
            title=title[:64],
            create_time=_now(),
        )
        self._sessions[sid] = session
        self._messages.setdefault(sid, [])
        return session

    async def get_session(self, session_id: str, user_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None or session.user_id != user_id:
            return None
        return session

    async def list_sessions(
        self,
        *,
        page: int,
        page_size: int,
        user_id: str | None = None,
        query: str | None = None,
    ) -> tuple[int, list[SessionSummary]]:
        items = list(self._sessions.values())
        if user_id:
            items = [s for s in items if s.user_id == user_id]
        if query:
            q = query.strip().lower()
            items = [s for s in items if q in (s.title or "").lower()]

        def last_active(s: Session) -> tuple[str, str]:
            # 时间只到秒：同一秒内建的两个会话靠 id（雪花）再降序，和 MySQL 的
            # `ORDER BY last_message_time DESC, id DESC` 保持同一语义
            msgs = self._messages.get(s.id) or []
            stamp = (msgs[-1].create_time or "") if msgs else (s.create_time or "")
            return stamp, s.id

        items.sort(key=last_active, reverse=True)
        total = len(items)
        start = max(0, (page - 1) * page_size)
        return total, [SessionSummary.of(s) for s in items[start : start + page_size]]

    async def get_session_any(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def list_runs(self, session_id: str) -> list[RunDetail]:
        out: list[RunDetail] = []
        for record in self._runs.values():
            run: Run = record["run"]
            if run.session_id != session_id:
                continue
            usage: Usage = record["usage"]
            out.append(
                RunDetail(
                    id=run.id,
                    route=run.route,
                    intent=run.intent,
                    status=record["status"],
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    latency_ms=int(record["latency_ms"]),
                    error=record["error"],
                    steps=list(self._steps.get(run.id, [])),
                )
            )
        out.sort(key=lambda r: r.id)
        return out

    # ------------------------------------------------------------ 消息
    async def add_message(self, msg: Message) -> Message:
        if not msg.id:
            msg.id = new_id()
        msg.create_time = msg.create_time or _now()
        self._messages.setdefault(msg.session_id, []).append(msg)
        session = self._sessions.get(msg.session_id)
        if session is not None:
            session.message_count += 1
        return msg

    async def history(self, session_id: str, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        msgs = [
            m
            for m in self._messages.get(session_id, [])
            if m.role in (Role.USER, Role.ASSISTANT)
        ][-limit:]
        return [{"role": m.role.value, "content": m.content} for m in msgs]

    async def list_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        return list(self._messages.get(session_id, [])[-limit:])

    # ------------------------------------------------------------ 运行
    async def start_run(self, run: Run) -> Run:
        if not run.id:
            run.id = new_id()
        if run.idempotency_key:
            key = (run.user_id, run.idempotency_key)
            existing_id = self._idem.get(key)
            if existing_id is not None:
                # 与 MySQL 唯一键同语义：已存在就返回旧 run，不新建（调用方据此回放）
                existing = self._runs.get(existing_id)
                if existing is not None:
                    return existing["run"]
            self._idem[key] = run.id
        self._runs[run.id] = {
            "run": run,
            "status": RunStatus.RUNNING,
            "error": None,
            "usage": Usage(),
            "latency_ms": 0,
            "created": _now(),
        }
        self._steps.setdefault(run.id, [])
        return run

    async def get_run(self, run_id: str) -> Run | None:
        record = self._runs.get(run_id)
        return record["run"] if record else None

    async def find_run_by_idempotency(self, user_id: str, idempotency_key: str) -> Run | None:
        run_id = self._idem.get((user_id, idempotency_key))
        if run_id is None:
            return None
        return await self.get_run(run_id)

    async def add_steps(self, run_id: str, steps: list[Step], start_seq: int = 1) -> None:
        bucket = self._steps.setdefault(run_id, [])
        if bucket:
            start_seq = max(start_seq, bucket[-1].seq + 1)
        for offset, step in enumerate(steps):
            step.seq = start_seq + offset
            bucket.append(step)

    async def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        usage: Usage,
        latency_ms: int,
        error: str | None = None,
    ) -> None:
        record = self._runs.get(run_id)
        if record is None:
            raise NotFound(f"运行不存在：{run_id}")
        current: RunStatus = record["status"]
        if current is not RunStatus.RUNNING:
            raise ValueError(f"运行已处于终态 {current.value}，不能再次结束")
        record.update({"status": status, "usage": usage, "latency_ms": latency_ms, "error": error})
        # `get_run` 返回的是这个 Run 对象本身，状态不同步的话它会永远停在 running
        # （MySQL 版每次从行里重建，天然一致）。断线跟随靠状态收口，这里必须对齐。
        record["run"].status = status

    async def audit_tool_call(
        self,
        run_id: str,
        name: str,
        ok: bool,
        code: str | None,
        latency_ms: int,
        args_digest: str,
        *,
        event_id: str | None = None,
    ) -> None:
        # 队列是 at-least-once：同一条审计消息重复投递时按 event_id 去重
        if event_id is not None:
            if event_id in self._audit_ids:
                return
            self._audit_ids.add(event_id)
        self._tool_calls.append(
            {
                "id": event_id or new_id(),
                "run_id": run_id,
                "name": name,
                "ok": ok,
                "code": code,
                "latency_ms": latency_ms,
                "args_digest": args_digest,
            }
        )

    # ------------------------------------------------------------ 测试辅助
    def steps_of(self, run_id: str) -> list[Step]:
        return list(self._steps.get(run_id, []))

    def run_record(self, run_id: str) -> dict[str, Any]:
        return dict(self._runs.get(run_id, {}))

    def tool_calls(self) -> list[dict[str, Any]]:
        return list(self._tool_calls)

    async def ping(self) -> None:
        # 内存实现永远可用；保留此方法是为了让 /readyz 不必区分实现
        return None

    # ------------------------------------------------------------ 长期记忆
    async def get_memory_fact(
        self, user_id: str, pet_id: str | None, key: str
    ) -> MemoryFact | None:
        return self._facts.get((user_id, pet_id or "", key))

    async def upsert_memory_fact(self, fact: MemoryFact) -> MemoryFact:
        slot = (fact.user_id, fact.pet_id or "", fact.key)
        existing = self._facts.get(slot)
        if existing is not None and not fact.id:
            fact.id = existing.id
            fact.create_time = existing.create_time
        if not fact.id:
            fact.id = new_id()
        fact.create_time = fact.create_time or _now()
        fact.update_time = _now()
        self._facts[slot] = fact
        return fact

    async def delete_memory_fact(self, user_id: str, pet_id: str | None, key: str) -> bool:
        slot = (user_id, pet_id or "", key)
        return self._facts.pop(slot, None) is not None

    async def list_memory_facts(
        self, user_id: str, pet_id: str | None, limit: int = 10
    ) -> list[MemoryFact]:
        if limit <= 0:
            return []
        items = [
            f
            for (uid, pid, _key), f in self._facts.items()
            if uid == user_id and pid == (pet_id or "")
        ]
        items.sort(key=lambda f: (f.confidence, f.update_time or ""), reverse=True)
        return items[:limit]

    # ------------------------------------------------------------ 用量
    async def usage_summary(self, user_id: str, since: str | None = None) -> UsageSummary:
        runs = 0
        prompt = 0
        completion = 0
        latencies: list[int] = []
        for record in self._runs.values():
            run: Run = record["run"]
            if record["status"] is not RunStatus.SUCCEEDED:
                continue
            session = self._sessions.get(run.session_id)
            if session is None or session.user_id != user_id:
                continue
            runs += 1
            prompt += record["usage"].prompt_tokens
            completion += record["usage"].completion_tokens
            latencies.append(int(record["latency_ms"]))
        avg = int(sum(latencies) / len(latencies)) if latencies else 0
        return UsageSummary(
            runs=runs,
            prompt_tokens=prompt,
            completion_tokens=completion,
            avg_latency_ms=avg,
        )

    # ---- 画像快照 ----
    @staticmethod
    def _profile_slot(user_id: str, pet_id: str | None) -> tuple[str, str]:
        return user_id, pet_id or ""

    async def next_profile_version(self, user_id: str, pet_id: str | None) -> int:
        versions = self._profiles.get(self._profile_slot(user_id, pet_id)) or []
        return (versions[-1].version + 1) if versions else 1

    async def save_profile_snapshot(self, snapshot: ProfileSnapshot) -> ProfileSnapshot:
        slot = self._profile_slot(snapshot.user_id, snapshot.pet_id)
        versions = self._profiles.setdefault(slot, [])
        if any(item.version == snapshot.version for item in versions):
            # 与 MySQL 唯一键同语义：并发重算时只有一个写入成功
            raise ValueError(f"画像版本已存在：{snapshot.version}")
        saved = replace(snapshot, create_time=snapshot.create_time or _now())
        versions.append(saved)
        versions.sort(key=lambda item: item.version)
        return saved

    async def latest_profile_snapshot(
        self, user_id: str, pet_id: str | None
    ) -> ProfileSnapshot | None:
        versions = self._profiles.get(self._profile_slot(user_id, pet_id)) or []
        return versions[-1] if versions else None

    async def list_profile_versions(
        self, user_id: str, pet_id: str | None, limit: int = 10
    ) -> list[ProfileSnapshot]:
        if limit <= 0:
            return []
        versions = self._profiles.get(self._profile_slot(user_id, pet_id)) or []
        return list(reversed(versions))[:limit]

    async def prune_profile_versions(self, user_id: str, pet_id: str | None, keep: int) -> int:
        if keep < 1:
            return 0
        slot = self._profile_slot(user_id, pet_id)
        versions = self._profiles.get(slot) or []
        if len(versions) <= keep:
            return 0
        removed = len(versions) - keep
        self._profiles[slot] = versions[-keep:]
        return removed

    async def latest_memory_update(self, user_id: str, pet_id: str | None) -> str | None:
        slot = (user_id, pet_id or "")
        stamps = [
            fact.update_time or fact.create_time
            for key, fact in self._facts.items()
            if (key[0], key[1]) == slot and (fact.update_time or fact.create_time)
        ]
        return max(stamps) if stamps else None

    async def usage_overview(self, since: str | None = None) -> UsageOverview:
        runs = 0
        prompt = 0
        completion = 0
        latencies: list[int] = []
        users: set[str] = set()
        days: dict[str, list[int]] = {}
        for record in self._runs.values():
            if record["status"] is not RunStatus.SUCCEEDED:
                continue
            created: str = record.get("created") or ""
            if since and created < since:
                continue
            run: Run = record["run"]
            session = self._sessions.get(run.session_id)
            usage: Usage = record["usage"]
            runs += 1
            prompt += usage.prompt_tokens
            completion += usage.completion_tokens
            latencies.append(int(record["latency_ms"]))
            if session is not None:
                users.add(session.user_id)
            bucket = days.setdefault(created[:10], [0, 0])
            bucket[0] += 1
            bucket[1] += usage.total
        avg = int(sum(latencies) / len(latencies)) if latencies else 0
        return UsageOverview(
            runs=runs,
            users=len(users),
            prompt_tokens=prompt,
            completion_tokens=completion,
            avg_latency_ms=avg,
            by_day=[DayUsage(day=d, runs=v[0], tokens=v[1]) for d, v in sorted(days.items())],
        )

    # ------------------------------------------------------------ 文档问答
    async def create_document(self, document: Document) -> Document:
        key = (document.user_id, document.sha256)
        existing_id = self._doc_sha.get(key)
        if existing_id:
            return self._documents[existing_id]
        if document.id in self._documents:
            raise ValueError(f"文档 id 重复：{document.id}")
        document.create_time = document.create_time or datetime.now()
        self._documents[document.id] = document
        self._doc_sha[key] = document.id
        return document

    async def get_document(self, user_id: str, document_id: str) -> Document | None:
        doc = self._documents.get(document_id)
        if doc is None or doc.user_id != user_id:
            return None
        return doc

    async def get_document_by_sha(self, user_id: str, sha256: str) -> Document | None:
        document_id = self._doc_sha.get((user_id, sha256))
        return self._documents.get(document_id) if document_id else None

    async def list_documents(
        self, user_id: str, *, pet_id: str | None = None, limit: int = 50
    ) -> list[Document]:
        items = [d for d in self._documents.values() if d.user_id == user_id]
        if pet_id:
            items = [d for d in items if d.pet_id == pet_id]
        items.sort(key=lambda d: (d.create_time or datetime.min, d.id), reverse=True)
        return items[:limit]

    async def update_document(
        self,
        document_id: str,
        *,
        status: DocumentStatus | None = None,
        error: str | None = None,
        chunk_count: int | None = None,
    ) -> Document:
        doc = self._documents.get(document_id)
        if doc is None:
            raise NotFound(f"文档不存在：{document_id}")
        if status is not None:
            doc.status = status
        if error is not None:
            doc.error = error
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        return doc

    async def delete_document(self, user_id: str, document_id: str) -> bool:
        doc = self._documents.get(document_id)
        if doc is None or doc.user_id != user_id:
            return False
        del self._documents[document_id]
        self._doc_sha.pop((user_id, doc.sha256), None)
        self._chunks.pop(document_id, None)
        return True

    async def add_chunks(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._chunks.setdefault(chunk.file_id, []).append(chunk)

    async def list_chunks(
        self, user_id: str, *, pet_id: str | None = None, limit: int = 2000
    ) -> list[Chunk]:
        rows: list[Chunk] = []
        for chunks in self._chunks.values():
            for chunk in chunks:
                if chunk.user_id != user_id:
                    continue
                if pet_id and chunk.pet_id != pet_id:
                    continue
                rows.append(chunk)
        rows.sort(key=lambda c: (c.file_id, c.chunk_index))
        return rows[:limit]

    async def aclose(self) -> None:
        return None

def _now() -> str:
    # 微秒精度：内存实现没有数据库的 NOW()，同一秒内多次写入必须可区分，
    # 否则「画像是否过期」「同秒会话排序」这类比较会失真。
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
