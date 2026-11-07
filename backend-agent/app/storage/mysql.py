"""MySQL 实现：写的就是 `backend/sql/v2.10-agent.sql` 那五张表。

并发/一致性上多做了三件事（内存版不需要，但生产必须）：
1. 建会话用 `INSERT` 撞唯一键后回查，避免并发下同一 session_id 被建两次；
2. `finish_run` 带 `AND status='running'` 条件，天然防止重复收尾；
3. 消息落库与会话计数在同一事务里，失败一起回滚。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from urllib.parse import unquote, urlparse

import pymysql.err

from ..core.errors import Forbidden, NotFound
from ..core.ids import new_id
from ..domain.models import (
    Citation,
    DayUsage,
    Intent,
    MemoryFact,
    Message,
    Role,
    Route,
    Run,
    RunDetail,
    RunStatus,
    Session,
    SessionSummary,
    Step,
    StepKind,
    StepStatus,
    Usage,
    UsageOverview,
    UsageSummary,
)

_INSERT_SESSION = (
    "INSERT INTO agent_session (id,user_id,pet_id,title,channel,status,message_count,"
    "total_tokens,last_message_time) VALUES (%s,%s,%s,%s,%s,1,0,0,NOW())"
)


class MySqlRepository:
    def __init__(self, dsn: str, *, pool_min: int = 1, pool_max: int = 5) -> None:
        parsed = urlparse(dsn)
        if parsed.scheme not in ("mysql", "mysql+aiomysql", ""):
            raise ValueError(f"不支持的 DSN scheme：{parsed.scheme}")
        self._cfg = {
            "host": parsed.hostname or "127.0.0.1",
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or "root"),
            "password": unquote(parsed.password or ""),
            "db": (parsed.path or "/petlumina").lstrip("/"),
            "charset": "utf8mb4",
            "autocommit": True,
        }
        self._pool_min = pool_min
        self._pool_max = pool_max
        self._pool: Any = None

    async def _ensure_pool(self) -> Any:
        if self._pool is None:
            import aiomysql

            self._pool = await aiomysql.create_pool(
                minsize=self._pool_min, maxsize=self._pool_max, **self._cfg
            )
        return self._pool

    # ------------------------------------------------------------ 会话
    async def get_or_create_session(
        self,
        session_id: str | None,
        user_id: str,
        pet_id: str | None,
        channel: str,
        title: str,
    ) -> Session:
        pool = await self._ensure_pool()
        if session_id:
            session = await self._fetch_session(pool, session_id)
            if session is not None:
                self._assert_owner(session, user_id)
                return session

        sid = session_id or new_id()
        try:
            async with pool.acquire() as conn, conn.cursor() as cur:
                await cur.execute(
                    _INSERT_SESSION,
                    (int(sid), int(user_id), int(pet_id) if pet_id else None, title[:64], channel),
                )
        except Exception as exc:
            if not _is_duplicate(exc):
                raise
            existing = await self._fetch_session(pool, sid)
            if existing is None:
                raise
            self._assert_owner(existing, user_id)
            return existing

        return Session(
            id=sid,
            user_id=user_id,
            channel=channel,
            pet_id=pet_id,
            title=title[:64],
            create_time=_now(),
        )

    async def get_session(self, session_id: str, user_id: str) -> Session | None:
        pool = await self._ensure_pool()
        session = await self._fetch_session(pool, session_id)
        if session is None or session.user_id != user_id:
            return None
        return session

    # ------------------------------------------------------------ 消息
    async def add_message(self, msg: Message) -> Message:
        if not msg.id:
            msg.id = new_id()
        msg.create_time = msg.create_time or _now()
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.begin()
            try:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO agent_message (id,session_id,run_id,role,content,"
                        "content_type,citations,meta) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            int(msg.id),
                            int(msg.session_id),
                            int(msg.run_id) if msg.run_id else None,
                            msg.role.value,
                            msg.content,
                            "markdown",
                            json.dumps([c.to_dict() for c in msg.citations], ensure_ascii=False)
                            if msg.citations
                            else None,
                            json.dumps(msg.meta, ensure_ascii=False) if msg.meta else None,
                        ),
                    )
                    await cur.execute(
                        "UPDATE agent_session SET message_count=message_count+1,"
                        "last_message_time=NOW() WHERE id=%s",
                        (int(msg.session_id),),
                    )
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
        return msg

    async def history(self, session_id: str, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT role,content FROM agent_message WHERE session_id=%s AND is_delete=0"
                " AND role IN ('user','assistant') ORDER BY create_time DESC, id DESC LIMIT %s",
                (int(session_id), limit),
            )
            rows = await cur.fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    async def list_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id,run_id,role,content,citations,create_time FROM agent_message"
                " WHERE session_id=%s AND is_delete=0 ORDER BY create_time DESC, id DESC LIMIT %s",
                (int(session_id), limit),
            )
            rows = await cur.fetchall()
        out: list[Message] = []
        for mid, run_id, role, content, citations, create_time in reversed(rows):
            out.append(
                Message(
                    id=str(mid),
                    session_id=session_id,
                    role=Role(role),
                    content=content,
                    run_id=str(run_id) if run_id else None,
                    citations=_load_citations(citations),
                    create_time=str(create_time),
                )
            )
        return out

    # ------------------------------------------------------------ 运行
    async def start_run(self, run: Run) -> Run:
        if not run.id:
            run.id = new_id()
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO agent_run"
                    " (id,session_id,user_id,user_message_id,intent,route,status,model,"
                    " idempotency_key)"
                    " VALUES (%s,%s,%s,%s,%s,%s,'running',%s,%s)",
                    (
                        int(run.id),
                        int(run.session_id),
                        int(run.user_id) if run.user_id else 0,
                        int(run.user_message_id) if run.user_message_id else None,
                        run.intent.value,
                        run.route.value,
                        run.model,
                        run.idempotency_key,
                    ),
                )
            except pymysql.err.IntegrityError:
                # 并发重复提交：唯一键 (user_id, idempotency_key) 拦下，回查已有 run
                existing = await self.find_run_by_idempotency(
                    run.user_id, run.idempotency_key or ""
                )
                if existing is None:
                    raise
                return existing
        return run

    async def find_run_by_idempotency(self, user_id: str, idempotency_key: str) -> Run | None:
        if not idempotency_key or not user_id:
            return None
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM agent_run WHERE user_id=%s AND idempotency_key=%s",
                (int(user_id), idempotency_key),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return await self.get_run(str(row[0]))

    async def get_run(self, run_id: str) -> Run | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id,session_id,user_id,user_message_id,intent,route,status,model,"
                " idempotency_key"
                " FROM agent_run WHERE id=%s",
                (int(run_id),),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        rid, sid, uid, umid, intent, route, status, model, idem = row
        return Run(
            id=str(rid),
            session_id=str(sid),
            user_id=str(uid or ""),
            user_message_id=str(umid) if umid else "",
            route=Route(route),
            intent=Intent(intent or "chat"),
            model=model or "",
            status=RunStatus(status),
            idempotency_key=idem,
        )

    async def add_steps(self, run_id: str, steps: list[Step], start_seq: int = 1) -> None:
        if not steps:
            return
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT COALESCE(MAX(seq),0) FROM agent_step WHERE run_id=%s", (int(run_id),)
            )
            row = await cur.fetchone()
            base = max(start_seq, int(row[0]) + 1 if row else start_seq)
            rows = [
                (
                    int(new_id()),
                    int(run_id),
                    base + offset,
                    step.kind.value,
                    step.name[:64],
                    json.dumps(step.input, ensure_ascii=False) if step.input else None,
                    (step.output_digest or "")[:512] or None,
                    step.status.value,
                    int(step.latency_ms),
                    (step.error or "")[:512] or None,
                )
                for offset, step in enumerate(steps)
            ]
            await cur.executemany(
                "INSERT INTO agent_step (id,run_id,seq,kind,name,input,output_digest,"
                "status,latency_ms,error) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                rows,
            )

    async def finish_run(
        self,
        run_id: str,
        status: RunStatus,
        usage: Usage,
        latency_ms: int,
        error: str | None = None,
    ) -> None:
        pool = await self._ensure_pool()
        try:
            rid = int(run_id)
        except (TypeError, ValueError) as exc:
            # 非数字 id 在雪花 id 空间里不可能存在，按"找不到"处理，而不是抛 ValueError 炸成 500
            raise NotFound(f"运行不存在：{run_id}") from exc
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "UPDATE agent_run SET status=%s,prompt_tokens=%s,completion_tokens=%s,"
                "latency_ms=%s,error=%s WHERE id=%s AND status='running'",
                (
                    status.value,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    latency_ms,
                    (error or "")[:512] or None,
                    rid,
                ),
            )
            if cur.rowcount == 0:
                await cur.execute("SELECT status FROM agent_run WHERE id=%s", (rid,))
                row = await cur.fetchone()
                if row is None:
                    raise NotFound(f"运行不存在：{run_id}")
                raise ValueError(f"运行已处于终态 {row[0]}，不能再次结束")
            await cur.execute(
                "UPDATE agent_session s JOIN agent_run r ON r.session_id=s.id"
                " SET s.total_tokens=s.total_tokens+%s WHERE r.id=%s",
                (usage.total, rid),
            )

    async def audit_tool_call(
        self,
        run_id: str,
        name: str,
        ok: bool,
        code: str | None,
        latency_ms: int,
        args_digest: str,
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO tool_call_log (id,run_id,tool_name,args_digest,ok,error_code,latency_ms)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (int(new_id()), int(run_id), name[:64], args_digest, int(ok), code, latency_ms),
            )

    async def ping(self) -> None:
        """`/readyz` 用：真正拿连接执行一次 `SELECT 1`，而不是只看连接池对象是否存在。"""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()

    # ------------------------------------------------------------ 长期记忆
    async def get_memory_fact(
        self, user_id: str, pet_id: str | None, key: str
    ) -> MemoryFact | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id,user_id,pet_id,fact_key,fact_value,confidence,source,"
                "create_time,update_time FROM memory_fact"
                " WHERE user_id=%s AND pet_id=%s AND fact_key=%s AND is_delete=0",
                (int(user_id), _pet_slot(pet_id), key),
            )
            row = await cur.fetchone()
        return _row_to_fact(row) if row else None

    async def upsert_memory_fact(self, fact: MemoryFact) -> MemoryFact:
        pool = await self._ensure_pool()
        fact_id = int(fact.id) if fact.id else int(new_id())
        async with pool.acquire() as conn, conn.cursor() as cur:
            # 唯一键 (user_id, pet_id, fact_key)：同一事实只更新不新增
            await cur.execute(
                "INSERT INTO memory_fact (id,user_id,pet_id,fact_key,fact_value,"
                "confidence,source) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                " ON DUPLICATE KEY UPDATE fact_value=VALUES(fact_value),"
                " confidence=GREATEST(confidence,VALUES(confidence)),"
                " source=VALUES(source),update_time=NOW()",
                (
                    fact_id,
                    int(fact.user_id),
                    _pet_slot(fact.pet_id),
                    fact.key,
                    fact.value[:255],
                    float(fact.confidence),
                    fact.source[:32],
                ),
            )
            await cur.execute(
                "SELECT id,user_id,pet_id,fact_key,fact_value,confidence,source,"
                "create_time,update_time FROM memory_fact"
                " WHERE user_id=%s AND pet_id=%s AND fact_key=%s",
                (int(fact.user_id), _pet_slot(fact.pet_id), fact.key),
            )
            row = await cur.fetchone()
        return _row_to_fact(row) if row else fact

    async def list_memory_facts(
        self, user_id: str, pet_id: str | None, limit: int = 10
    ) -> list[MemoryFact]:
        if limit <= 0:
            return []
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id,user_id,pet_id,fact_key,fact_value,confidence,source,"
                "create_time,update_time FROM memory_fact"
                " WHERE user_id=%s AND pet_id=%s AND is_delete=0"
                " ORDER BY confidence DESC, update_time DESC LIMIT %s",
                (int(user_id), _pet_slot(pet_id), int(limit)),
            )
            rows = await cur.fetchall()
        return [_row_to_fact(row) for row in rows]

    # ------------------------------------------------------------ 用量
    async def usage_summary(self, user_id: str, since: str | None = None) -> UsageSummary:
        pool = await self._ensure_pool()
        sql = (
            "SELECT COUNT(*), COALESCE(SUM(r.prompt_tokens),0),"
            " COALESCE(SUM(r.completion_tokens),0), COALESCE(AVG(r.latency_ms),0)"
            " FROM agent_run r JOIN agent_session s ON s.id=r.session_id"
            " WHERE s.user_id=%s AND r.status='succeeded'"
        )
        params: list[Any] = [int(user_id)]
        if since:
            sql += " AND r.create_time>=%s"
            params.append(since)
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(sql, tuple(params))
            row = await cur.fetchone()
        if not row:
            return UsageSummary()
        return UsageSummary(
            runs=int(row[0]),
            prompt_tokens=int(row[1]),
            completion_tokens=int(row[2]),
            avg_latency_ms=int(row[3]),
        )

    # ------------------------------------------------------------ 管理端只读
    async def list_sessions(
        self,
        *,
        page: int,
        page_size: int,
        user_id: str | None = None,
        query: str | None = None,
    ) -> tuple[int, list[SessionSummary]]:
        where = ["is_delete=0"]
        params: list[Any] = []
        if user_id:
            where.append("user_id=%s")
            params.append(int(user_id))
        if query:
            where.append("title LIKE %s")
            params.append(f"%{query.strip()}%")
        clause = " AND ".join(where)
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(f"SELECT COUNT(*) FROM agent_session WHERE {clause}", tuple(params))
            row = await cur.fetchone()
            total = int(row[0]) if row else 0
            await cur.execute(
                "SELECT id,user_id,pet_id,channel,title,message_count,create_time"
                f" FROM agent_session WHERE {clause}"
                " ORDER BY last_message_time DESC, id DESC LIMIT %s OFFSET %s",
                (*params, int(page_size), int((page - 1) * page_size)),
            )
            rows = await cur.fetchall()
        items = [
            SessionSummary(
                id=str(rid),
                user_id=str(uid),
                pet_id=str(pid) if pid else None,
                channel=channel,
                title=title or "",
                message_count=int(count or 0),
                create_time=str(created) if created else None,
            )
            for rid, uid, pid, channel, title, count, created in rows
        ]
        return total, items

    async def get_session_any(self, session_id: str) -> Session | None:
        return await self._fetch_session(await self._ensure_pool(), session_id)

    async def list_runs(self, session_id: str) -> list[RunDetail]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id,intent,route,status,prompt_tokens,completion_tokens,latency_ms,error"
                " FROM agent_run WHERE session_id=%s ORDER BY create_time ASC, id ASC",
                (int(session_id),),
            )
            rows = await cur.fetchall()
            run_ids = [str(r[0]) for r in rows]
            steps: dict[str, list[Step]] = {}
            if run_ids:
                placeholders = ",".join(["%s"] * len(run_ids))
                await cur.execute(
                    "SELECT run_id,seq,kind,name,status,latency_ms,error FROM agent_step"
                    f" WHERE run_id IN ({placeholders}) ORDER BY run_id ASC, seq ASC",
                    tuple(int(x) for x in run_ids),
                )
                for rid, seq, kind, name, status, latency, error in await cur.fetchall():
                    steps.setdefault(str(rid), []).append(
                        Step(
                            seq=int(seq),
                            kind=StepKind(kind),
                            name=name,
                            status=StepStatus(status),
                            latency_ms=int(latency or 0),
                            error=error,
                        )
                    )
        return [
            RunDetail(
                id=str(rid),
                route=Route(route),
                intent=Intent(intent or "chat"),
                status=RunStatus(status),
                prompt_tokens=int(prompt or 0),
                completion_tokens=int(completion or 0),
                latency_ms=int(latency or 0),
                error=error,
                steps=steps.get(str(rid), []),
            )
            for rid, intent, route, status, prompt, completion, latency, error in rows
        ]

    async def usage_overview(self, since: str | None = None) -> UsageOverview:
        pool = await self._ensure_pool()
        where = "r.status='succeeded'"
        params: list[Any] = []
        if since:
            where += " AND r.create_time>=%s"
            params.append(since)
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*), COUNT(DISTINCT s.user_id),"
                " COALESCE(SUM(r.prompt_tokens),0), COALESCE(SUM(r.completion_tokens),0),"
                " COALESCE(AVG(r.latency_ms),0)"
                " FROM agent_run r JOIN agent_session s ON s.id=r.session_id"
                f" WHERE {where}",
                tuple(params),
            )
            row = await cur.fetchone()
            await cur.execute(
                "SELECT DATE(r.create_time) AS d, COUNT(*),"
                " COALESCE(SUM(r.prompt_tokens+r.completion_tokens),0)"
                " FROM agent_run r JOIN agent_session s ON s.id=r.session_id"
                f" WHERE {where} GROUP BY d ORDER BY d ASC",
                tuple(params),
            )
            day_rows = await cur.fetchall()
        runs, users, prompt, completion, avg = row if row else (0, 0, 0, 0, 0)
        return UsageOverview(
            runs=int(runs or 0),
            users=int(users or 0),
            prompt_tokens=int(prompt or 0),
            completion_tokens=int(completion or 0),
            avg_latency_ms=int(avg or 0),
            by_day=[
                DayUsage(day=str(d), runs=int(c or 0), tokens=int(t or 0)) for d, c, t in day_rows
            ],
        )

    async def aclose(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
    # ------------------------------------------------------------ 内部
    async def _fetch_session(self, pool: Any, session_id: str) -> Session | None:
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id,user_id,pet_id,channel,title,create_time,message_count FROM agent_session"
                " WHERE id=%s AND is_delete=0",
                (int(session_id),),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        sid, uid, pid, channel, title, created, count = row
        return Session(
            id=str(sid),
            user_id=str(uid),
            pet_id=str(pid) if pid else None,
            channel=channel,
            title=title,
            create_time=str(created),
            message_count=int(count or 0),
        )

    @staticmethod
    def _assert_owner(session: Session, user_id: str) -> None:
        if session.user_id != user_id:
            raise Forbidden("会话不属于当前用户")


def _is_duplicate(exc: Exception) -> bool:
    code = getattr(exc, "args", (None, None))[0]
    return code == 1062


def _pet_slot(pet_id: str | None) -> int:
    """`pet_id` 可空，但唯一键里的 NULL 不参与去重——用 0 当"未指定宠物"的槽位。"""
    return int(pet_id) if pet_id else 0


def _row_to_fact(row: Any) -> MemoryFact:
    rid, uid, pid, key, value, confidence, source, created, updated = row
    return MemoryFact(
        id=str(rid),
        user_id=str(uid),
        pet_id=str(pid) if pid else None,
        key=key,
        value=value,
        confidence=float(confidence or 0.0),
        source=source or "conversation",
        create_time=str(created) if created else None,
        update_time=str(updated) if updated else None,
    )


def _load_citations(raw: Any) -> list[Any]:

    if not raw:
        return []
    try:
        items = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
    except (TypeError, ValueError):
        return []
    return [Citation.from_dict(x) for x in items if isinstance(x, dict)]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
