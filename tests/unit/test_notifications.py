import asyncio
from types import SimpleNamespace

import pytest

from apps.api.app.notification_schemas import NotificationPreferencesInput
from apps.api.app.providers.brevo_email import (
    BrevoEmailProvider,
    EmailMessage,
)
from apps.api.app.services.notifications import NotificationService


def test_notification_preferences_require_email_when_enabled() -> None:
    assert NotificationPreferencesInput(enabled=False).email == ""

    with pytest.raises(ValueError):
        NotificationPreferencesInput(enabled=True, email="")


def test_notification_email_message_contains_score_and_link() -> None:
    message = NotificationService._email_message(
        "user@example.com",
        "Example Corp",
        {
            "title": "Senior <Engineer>",
            "location": "Prague",
            "fit_score": 91,
            "summary": "Strong match",
            "recommendation": "strong_match",
            "job_url": "https://example.com/job/1",
            "strengths": ["Python"],
            "matched_skills": ["FastAPI"],
        },
    )

    assert "91/100" in message.subject
    assert "&lt;Engineer&gt;" in message.html_content
    assert "https://example.com/job/1" in message.html_content
    assert "FastAPI" in message.text_content


def test_brevo_provider_posts_transactional_email(monkeypatch) -> None:
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"messageId": "brevo-123"}

    class FakeClient:
        def __init__(self, **kwargs):
            calls["timeout"] = kwargs["timeout"]

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, **kwargs):
            calls["url"] = url
            calls["headers"] = kwargs["headers"]
            calls["json"] = kwargs["json"]
            return FakeResponse()

    monkeypatch.setattr(
        "apps.api.app.providers.brevo_email.httpx.AsyncClient",
        FakeClient,
    )

    provider = BrevoEmailProvider(
        "api-key",
        sender_email="sender@example.com",
        sender_name="AIlinkedin",
    )
    result = asyncio.run(
        provider.send(
            EmailMessage(
                to_email="user@example.com",
                to_name="User",
                subject="Test",
                html_content="<p>Hi</p>",
                text_content="Hi",
            )
        )
    )

    assert result == "brevo-123"
    assert calls["url"] == "https://api.brevo.com/v3/smtp/email"
    assert calls["headers"]["api-key"] == "api-key"
    assert calls["json"]["to"][0]["email"] == "user@example.com"
    assert calls["json"]["subject"] == "Test"


def test_phase9_routes_are_registered() -> None:
    from apps.api.app.main_phase9 import app

    paths = app.openapi()["paths"]
    assert "/api/v1/notifications/preferences" in paths
    assert "/api/v1/notifications" in paths
