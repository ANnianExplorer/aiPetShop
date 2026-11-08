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
from ..rag.models import Chunk, Document, DocumentStatus

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
        *,
        event_id: str | None = None,
    ) -> None:
        pool = await self._ensure_pool()
        # 队列是 at-least-once，`event_id` 作主键 + INSERT IGNORE 让重复投递变成空操作
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO tool_call_log"
                " (id,run_id,tool_name,args_digest,ok,error_code,latency_ms)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (
                    int(event_id or new_id()),
                    int(run_id),
                    name[:64],
                    args_digest,
                    int(ok),
                    code,
                    latency_ms,
                ),
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
            # 唯一键 (user_id, pet_id, fact_key)：同一事实只更新不新增。
            # 用行别名而不是 `VALUES(col)`：MySQL 8.0.20 起后者已弃用，未来版本会移除。
            await cur.execute(
                "INSERT INTO memory_fact (id,user_id,pet_id,fact_key,fact_value,"
                "confidence,source) VALUES (%s,%s,%s,%s,%s,%s,%s) AS new"
                " ON DUPLICATE KEY UPDATE fact_value=new.fact_value,"
                " confidence=GREATEST(memory_fact.confidence,new.confidence),"
                " source=new.source,update_time=NOW()",
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

    async def delete_memory_fact(self, user_id: str, pet_id: str | None, key: str) -> bool:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            # 物理删除：用户行使删除权，不需要保留影子行
            await cur.execute(
                "DELETE FROM memory_fact WHERE user_id=%s AND pet_id=%s AND fact_key=%s",
                (int(user_id), _pet_slot(pet_id), key),
            )
            return cur.rowcount > 0

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

    # ------------------------------------------------------------ 文档问答
    async def create_document(self, document: Document) -> Document:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO doc_file"
                    " (id,user_id,pet_id,name,mime,size_bytes,sha256,storage_key,status,error,chunk_count)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        int(document.id),
                        int(document.user_id),
                        _pet_slot(document.pet_id),
                        document.name,
                        document.mime,
                        document.size_bytes,
                        document.sha256,
                        document.storage_key,
                        int(document.status),
                        document.error,
                        document.chunk_count,
                    ),
                )
                await conn.commit()
            except pymysql.err.IntegrityError:
                await conn.rollback()
                existing = await self.get_document_by_sha(document.user_id, document.sha256)
                if existing is not None:
                    return existing
                # 唯一键包含软删除的行：同一个文件删掉再传会撞 1062，
                # 这里做"复活"而不是报错——否则用户重传同一份文件永远失败。
                revived = await self._revive_document(conn, document)
                if revived is None:
                    raise
                return revived
        return await self._fetch_document(pool, document.id, document.user_id) or document

    async def get_document(self, user_id: str, document_id: str) -> Document | None:
        pool = await self._ensure_pool()
        return await self._fetch_document(pool, document_id, user_id)

    async def _revive_document(self, conn: Any, document: Document) -> Document | None:
        """把同一 (user_id, sha256) 的软删除行恢复成排队中，并清掉旧切片。"""
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM doc_file WHERE user_id=%s AND sha256=%s",
                (int(document.user_id), document.sha256),
            )
            row = await cur.fetchone()
            if row is None:
                return None
            doc_id = int(row[0])
            await cur.execute(
                "UPDATE doc_file SET name=%s, mime=%s, size_bytes=%s, storage_key=%s,"
                " status=%s, error=NULL, chunk_count=0, pet_id=%s, is_delete=0"
                " WHERE id=%s",
                (
                    document.name,
                    document.mime,
                    document.size_bytes,
                    document.storage_key,
                    int(document.status),
                    _pet_slot(document.pet_id),
                    doc_id,
                ),
            )
            await cur.execute("DELETE FROM doc_chunk WHERE file_id=%s", (doc_id,))
            await conn.commit()
        pool = await self._ensure_pool()
        return await self._fetch_document(pool, str(doc_id), document.user_id)

    async def get_document_by_sha(self, user_id: str, sha256: str) -> Document | None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "SELECT id FROM doc_file WHERE user_id=%s AND sha256=%s AND is_delete=0",
                (int(user_id), sha256),
            )
            row = await cur.fetchone()
        return await self._fetch_document(pool, str(row[0]), user_id) if row else None

    async def list_documents(
        self, user_id: str, *, pet_id: str | None = None, limit: int = 50
    ) -> list[Document]:
        pool = await self._ensure_pool()
        sql = (
            "SELECT id,user_id,pet_id,name,mime,size_bytes,sha256,storage_key,status,error,"
            "chunk_count,create_time FROM doc_file WHERE user_id=%s AND is_delete=0"
        )
        params: list[Any] = [int(user_id)]
        if pet_id:
            sql += " AND pet_id=%s"
            params.append(int(pet_id))
        sql += " ORDER BY create_time DESC, id DESC LIMIT %s"
        params.append(int(limit))
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(sql, tuple(params))
            rows = await cur.fetchall()
        return [_row_to_document(r) for r in rows]

    async def update_document(
        self,
        document_id: str,
        *,
        status: DocumentStatus | None = None,
        error: str | None = None,
        chunk_count: int | None = None,
    ) -> Document:
        pool = await self._ensure_pool()
        sets: list[str] = []
        params: list[Any] = []
        if status is not None:
            sets.append("status=%s")
            params.append(int(status))
        if error is not None:
            sets.append("error=%s")
            params.append(error[:500])
        if chunk_count is not None:
            sets.append("chunk_count=%s")
            params.append(int(chunk_count))
        if not sets:
            raise ValueError("没有要更新的字段")
        params.append(int(document_id))
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(f"UPDATE doc_file SET {', '.join(sets)} WHERE id=%s", tuple(params))
            await conn.commit()
            if cur.rowcount == 0:
                raise NotFound(f"文档不存在：{document_id}")
        doc = await self._fetch_document(pool, document_id, None)
        if doc is None:
            raise NotFound(f"文档不存在：{document_id}")
        return doc

    async def delete_document(self, user_id: str, document_id: str) -> bool:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(
                "UPDATE doc_file SET is_delete=1 WHERE id=%s AND user_id=%s AND is_delete=0",
                (int(document_id), int(user_id)),
            )
            removed = cur.rowcount > 0
            if removed:
                await cur.execute("DELETE FROM doc_chunk WHERE file_id=%s", (int(document_id),))
            await conn.commit()
        return removed

    async def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        pool = await self._ensure_pool()
        rows = [
            (
                int(c.id),
                int(c.file_id),
                int(c.user_id),
                _pet_slot(c.pet_id),
                c.chunk_index,
                c.locator,
                c.content,
                c.token_hint,
                json.dumps(c.embedding),
                c.dim,
            )
            for c in chunks
        ]
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.executemany(
                "INSERT INTO doc_chunk"
                " (id,file_id,user_id,pet_id,chunk_index,locator,content,token_hint,embedding,dim)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                rows,
            )
            await conn.commit()

    async def list_chunks(
        self, user_id: str, *, pet_id: str | None = None, limit: int = 2000
    ) -> list[Chunk]:
        pool = await self._ensure_pool()
        sql = (
            "SELECT c.id,c.file_id,c.user_id,c.pet_id,c.chunk_index,c.locator,c.content,"
            "c.token_hint,c.embedding FROM doc_chunk c"
            " JOIN doc_file f ON f.id=c.file_id AND f.is_delete=0"
            " WHERE c.user_id=%s"
        )
        params: list[Any] = [int(user_id)]
        if pet_id:
            sql += " AND c.pet_id=%s"
            params.append(int(pet_id))
        sql += " ORDER BY c.file_id DESC, c.chunk_index ASC LIMIT %s"
        params.append(int(limit))
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(sql, tuple(params))
            rows = await cur.fetchall()
        return [_row_to_chunk(r) for r in rows]

    async def aclose(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def _fetch_document(
        self, pool: Any, document_id: str, user_id: str | None
    ) -> Document | None:
        sql = (
            "SELECT id,user_id,pet_id,name,mime,size_bytes,sha256,storage_key,status,error,"
            "chunk_count,create_time FROM doc_file WHERE id=%s AND is_delete=0"
        )
        params: list[Any] = [int(document_id)]
        if user_id is not None:
            sql += " AND user_id=%s"
            params.append(int(user_id))
        async with pool.acquire() as conn, conn.cursor() as cur:
            await cur.execute(sql, tuple(params))
            row = await cur.fetchone()
        return _row_to_document(row) if row else None

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


def _row_to_document(row: Any) -> Document:
    (rid, uid, pid, name, mime, size_bytes, sha, storage_key, status, error, chunk_count, created) = row
    return Document(
        id=str(rid),
        user_id=str(uid),
        pet_id=str(pid) if pid else None,
        name=name,
        mime=mime or "",
        size_bytes=int(size_bytes or 0),
        sha256=sha,
        storage_key=storage_key,
        status=DocumentStatus(int(status)),
        error=error,
        chunk_count=int(chunk_count or 0),
        create_time=created if isinstance(created, datetime) else None,
    )


def _row_to_chunk(row: Any) -> Chunk:
    (cid, file_id, uid, pid, index, locator, content, token_hint, embedding) = row
    try:
        vector = json.loads(embedding) if embedding else []
    except (TypeError, ValueError):
        vector = []
    return Chunk(
        id=str(cid),
        file_id=str(file_id),
        user_id=str(uid),
        pet_id=str(pid) if pid else None,
        chunk_index=int(index),
        locator=locator or "",
        content=content,
        token_hint=int(token_hint or 0),
        embedding=[float(x) for x in vector],
    )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
