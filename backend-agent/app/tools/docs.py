"""`search_docs`：在用户自己上传的资料里做检索（RAG 的读路径）。

边界：
- `user_id` 来自 `ToolContext`（服务端注入），模型无法跨用户检索；
- 只返回带 locator 的片段，让回答能指出"在第 3 页 / 第 90 秒"；
- 服务未装配时工具不注册（白名单里也不会出现），不会出现"调了才知道不支持"。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .spec import ToolContext, ToolSpec


class SearchDocsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=200, description="要检索的问题或关键词")
    top_k: int = Field(default=4, ge=1, le=10, description="返回片段数，1~10，默认 4")


async def search_docs(args: SearchDocsArgs, ctx: ToolContext) -> dict[str, Any]:
    docs = ctx.docs
    if docs is None:
        return {"ok": False, "code": "docs_unavailable", "error": "文档检索未启用"}
    hits = await docs.search(
        user_id=ctx.user_id,
        query=args.query,
        pet_id=ctx.pet_id,
        top_k=args.top_k,
    )
    if not hits:
        return {
            "ok": True,
            "items": [],
            "hint": "没有在用户上传的资料里找到相关内容；可以直接说没找到，不要编造。",
        }
    return {
        "ok": True,
        "items": [
            {
                "document": hit.document_name,
                "locator": hit.chunk.locator,
                "score": hit.score,
                "content": hit.chunk.content[:800],
            }
            for hit in hits
        ],
        "citations": [hit.citation() for hit in hits],
    }


def search_docs_spec() -> ToolSpec:
    return ToolSpec(
        name="search_docs",
        description=(
            "在用户上传的资料（疫苗本、化验单、病历、照片识别文本等）里检索片段。"
            "回答用户关于'我传的文件里写了什么'的问题时优先使用；结果带页码/时间戳用于引用。"
        ),
        args_model=SearchDocsArgs,
        handler=search_docs,
        tags=frozenset({"read", "docs"}),
    )


__all__ = ["SearchDocsArgs", "search_docs", "search_docs_spec"]
