from __future__ import annotations

from dataclasses import dataclass

import httpx


class EmailDeliveryError(RuntimeError):
    pass


@dataclass(slots=True)
class EmailMessage:
    to_email: str
    to_name: str | None
    subject: str
    html_content: str
    text_content: str


class BrevoEmailProvider:
    def __init__(
        self,
        api_key: str,
        *,
        sender_email: str,
        sender_name: str,
        base_url: str = "https://api.brevo.com/v3",
        timeout_seconds: float = 20.0,
    ) -> None:
        if not api_key:
            raise EmailDeliveryError("Brevo email provider is not configured")
        if not sender_email:
            raise EmailDeliveryError("Brevo sender email is not configured")
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def send(self, message: EmailMessage) -> str:
        payload = {
            "sender": {"email": self.sender_email, "name": self.sender_name},
            "to": [{"email": message.to_email, "name": message.to_name or message.to_email}],
            "subject": message.subject,
            "htmlContent": message.html_content,
            "textContent": message.text_content,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/smtp/email",
                    headers={
                        "accept": "application/json",
                        "api-key": self.api_key,
                        "content-type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise EmailDeliveryError(f"Brevo delivery failed: {detail}") from exc

        data = response.json()
        message_id = data.get("messageId")
        return str(message_id) if message_id else "sent"
