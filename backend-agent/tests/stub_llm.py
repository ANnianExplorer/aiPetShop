"""本地 LLM 桩：只用于验证链路，不参与生产。

两种模式：
- 传了 tools 且用户问到"记录/疫苗/洗澡" → 返回一次 `search_logs` 工具调用；
- 消息里已经出现 `role=tool` → 基于工具结果作答；
- 其余情况 → 固定闲聊。

流式响应末尾追加 usage 帧（对齐 `stream_options.include_usage` 的线上格式）。

    python -m uvicorn tests.stub_llm:app --port 8098
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

CHAT_REPLY = "我在呢。想先看看哪只宠物的记录？"
ANSWER = "9月1日打过疫苗，记录里写的是猫三联。"


def _wants_tool(body: dict[str, Any]) -> bool:
    messages = body.get("messages") or []
    if any(m.get("role") == "tool" for m in messages):
        return False
    if not body.get("tools"):
        return False
    text = " ".join(str(m.get("content") or "") for m in messages)
    return any(word in text for word in ("记录", "疫苗", "洗澡", "驱虫"))


def _reply(body: dict[str, Any]) -> dict[str, Any]:
    if _wants_tool(body):
        return {
            "content": None,
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "search_logs",
                        "arguments": json.dumps({"keyword": "疫苗"}, ensure_ascii=False),
                    },
                }
            ],
        }
    has_tool_result = any(m.get("role") == "tool" for m in body.get("messages") or [])
    return {"content": ANSWER if has_tool_result else CHAT_REPLY, "tool_calls": None}


@app.post("/v1/chat/completions")
async def completions(request: Request):
    body = await request.json()
    reply = _reply(body)
    usage = {"prompt_tokens": 11, "completion_tokens": 7}

    if not body.get("stream"):
        return {
            "id": "stub",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", **reply},
                    "finish_reason": "tool_calls" if reply["tool_calls"] else "stop",
                }
            ],
            "usage": usage,
        }

    async def gen() -> AsyncIterator[str]:
        if reply["tool_calls"]:
            payload = {
                "id": "stub",
                "choices": [
                    {
                        "index": 0,
                        "delta": {"tool_calls": [{"index": 0, **reply["tool_calls"][0]}]},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        else:
            text = reply["content"] or ""
            for i in range(0, len(text), 4):
                payload = {
                    "id": "stub",
                    "choices": [
                        {"index": 0, "delta": {"content": text[i : i + 4]}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                time.sleep(0.01)

        # 末尾 usage 帧，模拟 OpenAI 的 stream_options.include_usage
        yield f"data: {json.dumps({'id': 'stub', 'choices': [], 'usage': usage})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
