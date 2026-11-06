"""工具契约：参数用 pydantic 模型声明，schema 由模型自动生成。

这样做的三个好处（也是上一版手写 dict 的坑）：
1. 参数校验与 OpenAI function schema **同源**，不会出现「文档写了、校验没做」；
2. 模型传入未声明字段（例如伪造 `user_id`）会被直接拒绝；
3. 工具返回值、错误码有统一形状，图里不需要各自防御。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Type

from pydantic import BaseModel

if TYPE_CHECKING:  # 仅类型检查时导入，避免运行期循环依赖
    from .client import BackendClient


@dataclass
class ToolContext:
    """一次工具调用需要的可信上下文。user_id / token 只能来自服务端，永不来自模型参数。"""

    user_id: str
    token: str
    run_id: str
    backend: "BackendClient"
    pet_id: str | None = None
    auto_commit: bool = False


ToolHandler = Callable[[Any, ToolContext], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: Type[BaseModel]
    handler: ToolHandler
    side_effect: bool = False
    tags: frozenset[str] = field(default_factory=frozenset)

    def openai_schema(self) -> dict[str, Any]:
        params = self.args_model.model_json_schema()
        params.pop("title", None)
        if not params.get("$defs"):
            params.pop("$defs", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": params,
            },
        }
