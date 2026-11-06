"""ASGI 入口。

开发：`uvicorn app.main:app --reload --port 8090`
测试：`pytest -q`
"""

from __future__ import annotations

from .api import create_app

app = create_app()
