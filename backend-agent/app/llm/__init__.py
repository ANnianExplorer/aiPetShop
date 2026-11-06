"""模型层出口。上层只从这里拿类型，不直接依赖具体实现。"""

from .base import ChatModel, LLMReply, StreamChunk, ToolCall
from .fake import ScriptedModel
from .openai_compat import OpenAICompatModel, build_model

__all__ = [
    "ChatModel",
    "LLMReply",
    "OpenAICompatModel",
    "ScriptedModel",
    "StreamChunk",
    "ToolCall",
    "build_model",
]
