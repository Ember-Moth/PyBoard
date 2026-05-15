"""Cloudflare Turnstile verification tests."""

import pytest

from app.core.exceptions import BadRequestException
from app.models.user.dto import UserCreate
from app.services.turnstile import TURNSTILE_SITEVERIFY_URL, TurnstileService


class FakeSettingService:
    def __init__(self, values: dict[str, str | int]):
        self.values = values

    async def get_int(self, key: str, default: int = 0) -> int:
        return int(self.values.get(key, default))

    async def get_str(self, key: str, default: str = "") -> str:
        return str(self.values.get(key, default))


@pytest.mark.asyncio
async def test_turnstile_skips_when_disabled(monkeypatch):
    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("HTTP client should not be created")

    monkeypatch.setattr("app.services.turnstile.httpx.AsyncClient", FailingAsyncClient)

    service = TurnstileService(FakeSettingService({"recaptcha_enable": 0}))  # type: ignore[arg-type]
    await service.verify_if_enabled(None, "127.0.0.1")


@pytest.mark.asyncio
async def test_turnstile_requires_token_when_enabled():
    service = TurnstileService(
        FakeSettingService({"recaptcha_enable": 1, "recaptcha_key": "turnstile-secret"})  # type: ignore[arg-type]
    )

    with pytest.raises(BadRequestException) as exc:
        await service.verify_if_enabled(None, "127.0.0.1")

    assert exc.value.detail == "请完成人机验证"


@pytest.mark.asyncio
async def test_turnstile_verifies_token(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": True}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, data):
            calls.append((url, data))
            return FakeResponse()

    monkeypatch.setattr("app.services.turnstile.httpx.AsyncClient", FakeAsyncClient)

    service = TurnstileService(
        FakeSettingService({"recaptcha_enable": 1, "recaptcha_key": "turnstile-secret"})  # type: ignore[arg-type]
    )
    await service.verify_if_enabled("turnstile-token", "127.0.0.1")

    assert calls == [
        (
            TURNSTILE_SITEVERIFY_URL,
            {
                "secret": "turnstile-secret",
                "response": "turnstile-token",
                "remoteip": "127.0.0.1",
            },
        )
    ]


@pytest.mark.asyncio
async def test_turnstile_rejects_failed_result(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": False, "error-codes": ["invalid-input-response"]}

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, data):
            return FakeResponse()

    monkeypatch.setattr("app.services.turnstile.httpx.AsyncClient", FakeAsyncClient)

    service = TurnstileService(
        FakeSettingService({"recaptcha_enable": 1, "recaptcha_key": "turnstile-secret"})  # type: ignore[arg-type]
    )
    with pytest.raises(BadRequestException) as exc:
        await service.verify_if_enabled("bad-token", "127.0.0.1")

    assert exc.value.detail == "人机验证失败，请重试"


def test_auth_dto_accepts_turnstile_aliases():
    user = UserCreate.model_validate(
        {
            "email": "turnstile@test.local",
            "password": "password123",
            "turnstile_token": "token-from-widget",
        }
    )

    assert user.recaptcha_data == "token-from-widget"
