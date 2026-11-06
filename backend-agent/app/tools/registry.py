"""工具注册表：只负责「有哪些工具、schema 长什么样」，不做策略也不执行。"""

from __future__ import annotations

from typing import Any, Collection

from .spec import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"工具重复注册：{spec.name}")
        self._specs[spec.name] = spec

    def get(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._specs))

    def schemas(self, allowed: Collection[str] | None = None) -> list[dict[str, Any]]:
        names = set(allowed) if allowed is not None else set(self._specs)
        return [self._specs[n].openai_schema() for n in sorted(names) if n in self._specs]

    def __len__(self) -> int:
        return len(self._specs)

    def __contains__(self, name: object) -> bool:
        return name in self._specs
