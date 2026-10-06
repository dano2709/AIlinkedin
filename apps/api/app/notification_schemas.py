from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NotificationPreferencesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    email: str = Field(default="", max_length=320)
    min_fit_score: int = Field(default=80, ge=0, le=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized and ("@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]):
            raise ValueError("email must be valid")
        return normalized

    @model_validator(mode="after")
    def require_email_when_enabled(self) -> "NotificationPreferencesInput":
        if self.enabled and not self.email:
            raise ValueError("email is required when notifications are enabled")
        return self


class NotificationPreferencesResponse(BaseModel):
    user_id: UUID
    exists: bool
    preferences: NotificationPreferencesInput
    created_at: datetime | None
    updated_at: datetime | None


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    fingerprint: str
    payload: dict[str, object]
    created_at: datetime


class NotificationDeliveryResponse(BaseModel):
    notification_id: UUID
    channel: str
    status: str
    sent_at: datetime | None
    error: str | None


class NotificationHistoryResponse(BaseModel):
    notifications: list[NotificationResponse]
    deliveries: list[NotificationDeliveryResponse]
