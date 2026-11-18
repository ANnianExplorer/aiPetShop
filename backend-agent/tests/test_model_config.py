"""管理端模型配置：权限、密钥不下发、保存热应用、禁用回退环境变量。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from conftest import AUTH_HEADERS, make_http, make_settings

from app.api import create_app
from app.model_config import ConfigCipher, ConfigCipherError
from app.storage import InMemoryRepository

ADMIN_HEADERS = {"satoken": "token-admin", "x-user-id": "9001", "x-user-role": "admin"}


def _settings(tmp_path: Path, **overrides: object):
    base = {
        "llm_api_key": "",
        "llm_model": "env-model",
        "model_config_key_file": str(tmp_path / "model-config.key"),
        "model_config_file": str(tmp_path / "model-config.json"),
    }
    base.update(overrides)
    return make_settings(**base)


def _app(tmp_path: Path, **overrides: object):
    settings = _settings(tmp_path, **overrides)
    return create_app(
        settings,
        model=None,
        repo=InMemoryRepository(),
        http_client=make_http(),
    )


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[tuple[httpx.AsyncClient, object]]:
    app = _app(tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent") as http:
        yield http, app
    await app.state.model_config.aclose()


async def test_non_admin_forbidden(client: tuple[httpx.AsyncClient, object]) -> None:
    http, _ = client
    resp = await http.get("/agent/admin/model-config", headers=AUTH_HEADERS)
    assert resp.status_code == 403


async def test_empty_config_reports_none(client: tuple[httpx.AsyncClient, object]) -> None:
    http, _ = client
    resp = await http.get("/agent/admin/model-config", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "none"
    assert body["enabled"] is False
    assert body["has_api_key"] is False


async def test_save_masks_key_and_applies(client: tuple[httpx.AsyncClient, object]) -> None:
    http, app = client
    resp = await http.put(
        "/agent/admin/model-config",
        headers=ADMIN_HEADERS,
        json={
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com/v1/",
            "model": "deepseek-chat",
            "api_key": "sk-test-secret-1234",
            "enabled": True,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["api_key_masked"] == "****1234"
    assert "sk-test-secret-1234" not in resp.text
    assert "api_key_cipher" not in resp.text
    assert app.state.model_name == "deepseek-chat"
    assert app.state.model_source == "db"
    assert app.state.graph is not None

    health = await http.get("/healthz")
    assert health.json()["model_configured"] is True
    assert health.json()["model_source"] == "db"


async def test_update_without_key_keeps_saved_key(client: tuple[httpx.AsyncClient, object]) -> None:
    http, _ = client
    first = await http.put(
        "/agent/admin/model-config",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "base_url": "https://example.com/v1",
            "model": "model-a",
            "api_key": "sk-keep-5678",
            "enabled": True,
        },
    )
    assert first.status_code == 200
    second = await http.put(
        "/agent/admin/model-config",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "base_url": "https://example.com/v1",
            "model": "model-b",
            "api_key": "",
            "enabled": True,
        },
    )
    assert second.status_code == 200, second.text
    assert second.json()["has_api_key"] is True
    assert second.json()["api_key_masked"] == "****5678"
    assert second.json()["model"] == "model-b"


async def test_disable_falls_back_to_env(tmp_path: Path) -> None:
    app = _app(tmp_path, llm_api_key="env-key-9999")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent") as http:
        resp = await http.put(
            "/agent/admin/model-config",
            headers=ADMIN_HEADERS,
            json={
                "provider": "deepseek",
                "base_url": "https://api.deepseek.com/v1",
                "model": "db-model",
                "api_key": "sk-db-0000",
                "enabled": False,
            },
        )
        assert resp.status_code == 200, resp.text
        assert app.state.model_name == "env-model"
        assert app.state.model_source == "env"
        assert resp.json()["enabled"] is False
        assert resp.json()["runtime_source"] == "env"
    await app.state.model_config.aclose()


async def test_saved_file_contains_ciphertext_only(tmp_path: Path) -> None:
    app = _app(tmp_path)
    secret = "sk-plaintext-never-on-disk-9876"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent") as http:
        resp = await http.put(
            "/agent/admin/model-config",
            headers=ADMIN_HEADERS,
            json={
                "provider": "openai",
                "base_url": "https://example.com/v1",
                "model": "model-a",
                "api_key": secret,
                "enabled": True,
            },
        )
        assert resp.status_code == 200, resp.text
    stored = (tmp_path / "model-config.json").read_text(encoding="utf-8")
    assert secret not in stored
    assert '"api_key_cipher": "v1:' in stored
    await app.state.model_config.aclose()


async def test_disabled_without_env_is_not_ready(tmp_path: Path) -> None:
    app = _app(tmp_path)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agent") as http:
        resp = await http.put(
            "/agent/admin/model-config",
            headers=ADMIN_HEADERS,
            json={
                "provider": "openai",
                "base_url": "https://example.com/v1",
                "model": "model-a",
                "api_key": "",
                "enabled": False,
            },
        )
        assert resp.status_code == 200, resp.text
        assert app.state.model_name is None
        ready = await http.get("/readyz")
        assert ready.status_code == 503
        assert ready.json()["checks"]["model"] == "not_configured"
    await app.state.model_config.aclose()


async def test_test_connection_without_key_is_rejected(client: tuple[httpx.AsyncClient, object]) -> None:
    http, _ = client
    resp = await http.post(
        "/agent/admin/model-config/test",
        headers=ADMIN_HEADERS,
        json={
            "provider": "openai",
            "base_url": "https://example.com/v1",
            "model": "model-a",
            "api_key": "",
            "enabled": True,
        },
    )
    assert resp.status_code == 400
    assert "API Key" in resp.json()["message"]


def test_cipher_roundtrip_and_tamper(tmp_path: Path) -> None:
    cipher = ConfigCipher("unit-test-secret", tmp_path / "unused.key")
    token = cipher.encrypt("sk-roundtrip-1234")
    assert token.startswith("v1:")
    assert cipher.decrypt(token) == "sk-roundtrip-1234"

    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    with pytest.raises(ConfigCipherError):
        cipher.decrypt(tampered)
