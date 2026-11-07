"""真机冒烟：文档上传 → 解析入库 → 对话里被检索到并带引用。

要求：8099 已按 dev 形态启动（REPO_BACKEND=mysql、LLM 指向 tests.stub_llm）。
    python -m scripts.rag_smoke
"""

from __future__ import annotations

import asyncio
import io
import sys

import httpx

BASE = "http://127.0.0.1:8099"
TOKEN = "token-7001"
HEADERS = {"satoken": TOKEN, "x-user-id": "7001"}

DOC_TEXT = (
    "Lumina 疫苗本\n"
    "2026-09-01 接种猫三联第二针，批号 A2131，接种医院：城南宠物医院。\n"
    "2026-11-20 需补种狂犬疫苗，注意接种前空腹 4 小时。\n"
)

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}".rstrip())


async def wait_ready(client: httpx.AsyncClient, doc_id: str, timeout_s: float = 15.0) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout_s
    last: dict = {}
    while asyncio.get_running_loop().time() < deadline:
        resp = await client.get(f"/agent/documents/{doc_id}", headers=HEADERS)
        last = resp.json()
        if last.get("status") == 2 or last.get("status_label") == "已就绪":
            return last
        await asyncio.sleep(0.2)
    return last


async def main() -> int:
    async with httpx.AsyncClient(base_url=BASE, timeout=30.0) as client:
        caps = (await client.get("/agent/documents/capabilities", headers=HEADERS)).json()
        check(
            "capabilities.text",
            bool((caps.get("text") or {}).get("supported")),
            str((caps.get("text") or {}).get("suffixes"))[:60],
        )
        check(
            "capabilities.image_reason",
            bool((caps.get("image") or {}).get("reason")),
            str((caps.get("image") or {}).get("reason"))[:40],
        )

        files = {"file": ("vaccine.txt", io.BytesIO(DOC_TEXT.encode("utf-8")), "text/plain")}
        upload = await client.post("/agent/documents", headers=HEADERS, files=files, data={"pet_id": ""})
        body = upload.json()
        check("upload", upload.status_code == 202, f"status={upload.status_code} code={body.get('code')}")
        doc_id = str(body.get("id") or "")
        check("doc_id", bool(doc_id), doc_id)

        doc = await wait_ready(client, doc_id)
        check("ready", doc.get("status") == 2, f"status={doc.get('status')} chunks={doc.get('chunk_count')}")
        check("chunks", int(doc.get("chunk_count") or 0) >= 1, str(doc.get("chunk_count")))

        listed = (await client.get("/agent/documents", headers=HEADERS)).json()
        check("list", int(listed.get("total") or 0) >= 1, f"total={listed.get('total')}")

        payload = {"message": "我传的疫苗本里写了什么？", "channel": "app", "pet_id": None}
        tools: list[str] = []
        citations: list[dict] = []
        async with client.stream("POST", "/agent/chat", headers=HEADERS, json=payload) as resp:
            event = ""
            async for line in resp.aiter_lines():
                if line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    import json as _json

                    data = _json.loads(line[5:].strip())
                    if event == "tool":
                        tools.append(str(data.get("name")))
                    if event == "done":
                        citations = data.get("citations") or []
        check("tool search_docs", "search_docs" in tools, str(tools))
        check(
            "citation doc",
            any(c.get("kind") == "doc" for c in citations),
            str(citations)[:120],
        )

        deleted = await client.delete(f"/agent/documents/{doc_id}", headers=HEADERS)
        check("delete", deleted.status_code == 200, str(deleted.json()))

    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"\n{passed}/{len(CHECKS)} passed")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
