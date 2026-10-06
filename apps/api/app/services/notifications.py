from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    CandidateJobScore,
    Company,
    Job,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    User,
)
from ..providers.brevo_email import BrevoEmailProvider, EmailDeliveryError, EmailMessage
from ..settings import settings


@dataclass(slots=True)
class NotificationPreferencesData:
    enabled: bool
    email: str
    min_fit_score: int


@dataclass(slots=True)
class NotificationPreferencesResult:
    user_id: UUID
    exists: bool
    data: NotificationPreferencesData
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(slots=True)
class NotificationDispatchResult:
    status: str
    notification_id: UUID | None
    delivery_status: str | None
    detail: str | None


class NotificationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_preferences(self, user_id: UUID) -> NotificationPreferencesResult:
        profile = self.session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        ).scalars().first()
        if profile is None:
            return NotificationPreferencesResult(
                user_id=user_id,
                exists=False,
                data=NotificationPreferencesData(enabled=False, email="", min_fit_score=80),
                created_at=None,
                updated_at=None,
            )
        return NotificationPreferencesResult(
            user_id=user_id,
            exists=True,
            data=NotificationPreferencesData(
                enabled=profile.enabled,
                email=profile.email,
                min_fit_score=profile.min_fit_score,
            ),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def upsert_preferences(
        self,
        user_id: UUID,
        data: NotificationPreferencesData,
    ) -> NotificationPreferencesResult:
        user = self.session.execute(select(User).where(User.id == user_id)).scalars().first()
        if user is None:
            user = User(id=user_id)
            self.session.add(user)
            self.session.flush()

        existing = self.session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        ).scalars().first()
        if existing is None:
            existing = NotificationPreference(id=uuid4(), user_id=user_id)
            self.session.add(existing)

        existing.enabled = data.enabled
        existing.email = data.email.strip().lower()
        existing.min_fit_score = data.min_fit_score
        self.session.flush()

        return NotificationPreferencesResult(
            user_id=user_id,
            exists=True,
            data=NotificationPreferencesData(
                enabled=existing.enabled,
                email=existing.email,
                min_fit_score=existing.min_fit_score,
            ),
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )

    async def notify_high_fit(
        self,
        user_id: UUID,
        job_id: UUID,
        *,
        fit_score: int,
        score_payload: dict[str, object],
    ) -> NotificationDispatchResult:
        preferences = self.get_preferences(user_id)
        if not preferences.exists or not preferences.data.enabled:
            return NotificationDispatchResult(
                status="disabled",
                notification_id=None,
                delivery_status=None,
                detail="notifications are disabled",
            )

        if fit_score < preferences.data.min_fit_score:
            return NotificationDispatchResult(
                status="below_threshold",
                notification_id=None,
                delivery_status=None,
                detail=f"fit score {fit_score} is below {preferences.data.min_fit_score}",
            )

        job = self.session.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if job is None:
            return NotificationDispatchResult(
                status="job_not_found",
                notification_id=None,
                delivery_status=None,
                detail=None,
            )

        fingerprint = hashlib.sha256(
            f"high-fit|{user_id}|{job_id}|{preferences.data.min_fit_score}".encode()
        ).hexdigest()
        existing = self.session.execute(
            select(Notification).where(Notification.fingerprint == fingerprint)
        ).scalars().first()
        if existing is not None:
            return NotificationDispatchResult(
                status="duplicate",
                notification_id=existing.id,
                delivery_status=None,
                detail="notification already created",
            )

        company_name = self._company_name(job.company_id)
        summary = str(score_payload.get("summary", ""))
        recommendation = str(score_payload.get("recommendation", ""))
        strengths = self._string_list(score_payload.get("strengths"))
        matched_skills = self._string_list(score_payload.get("matched_skills"))

        payload = {
            "job_id": str(job.id),
            "title": job.title,
            "company_name": company_name,
            "location": job.location_raw,
            "fit_score": fit_score,
            "recommendation": recommendation,
            "summary": summary,
            "strengths": strengths,
            "matched_skills": matched_skills,
            "job_url": job.external_apply_url or job.apply_url or job.canonical_url,
        }

        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            type="HIGH_FIT_JOB",
            fingerprint=fingerprint,
            payload=payload,
        )
        self.session.add(notification)
        delivery = NotificationDelivery(
            id=uuid4(),
            notification_id=notification.id,
            channel="email",
            status="PENDING",
        )
        self.session.add(delivery)
        self.session.flush()

        try:
            provider = BrevoEmailProvider(
                settings.brevo_api_key,
                sender_email=settings.notification_sender_email,
                sender_name=settings.notification_sender_name,
                base_url=settings.brevo_base_url,
                timeout_seconds=settings.notification_timeout_seconds,
            )
            message_id = await provider.send(
                self._email_message(
                    preferences.data.email,
                    company_name,
                    payload,
                )
            )
        except EmailDeliveryError as exc:
            delivery.status = "FAILED"
            delivery.error = str(exc)[:2000]
            self.session.flush()
            return NotificationDispatchResult(
                status="created",
                notification_id=notification.id,
                delivery_status=delivery.status,
                detail=delivery.error,
            )

        delivery.status = "SENT"
        delivery.sent_at = datetime.now(timezone.utc)
        delivery.error = message_id
        self.session.flush()
        return NotificationDispatchResult(
            status="sent",
            notification_id=notification.id,
            delivery_status=delivery.status,
            detail=message_id,
        )

    def recent(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
    ) -> tuple[list[Notification], list[NotificationDelivery]]:
        notifications = list(
            self.session.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            ).scalars()
        )
        if not notifications:
            return [], []

        notification_ids = [notification.id for notification in notifications]
        deliveries = list(
            self.session.execute(
                select(NotificationDelivery)
                .where(NotificationDelivery.notification_id.in_(notification_ids))
                .order_by(NotificationDelivery.id.desc())
            ).scalars()
        )
        return notifications, deliveries

    def _company_name(self, company_id: UUID | None) -> str:
        if company_id is None:
            return "Unknown company"
        company = self.session.execute(select(Company).where(Company.id == company_id)).scalars().first()
        return company.name if company else "Unknown company"

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item not in (None, "")]

    @staticmethod
    def _email_message(
        email: str,
        company_name: str,
        payload: dict[str, object],
    ) -> EmailMessage:
        title = escape(str(payload["title"]))
        company = escape(company_name)
        score = int(payload["fit_score"])
        location = escape(str(payload.get("location") or "Location not provided"))
        summary = escape(str(payload.get("summary") or ""))
        recommendation = escape(str(payload.get("recommendation") or ""))
        job_url = escape(str(payload.get("job_url") or ""))
        strengths = NotificationService._string_list(payload.get("strengths"))
        matched = NotificationService._string_list(payload.get("matched_skills"))

        strength_html = "".join(f"<li>{escape(item)}</li>" for item in strengths[:5])
        matched_html = ", ".join(escape(item) for item in matched[:8])
        html = (
            f"<h2>{score}/100 — {title}</h2>"
            f"<p><strong>{company}</strong> · {location}</p>"
            f"<p>{summary}</p>"
            f"<p><strong>Recommendation:</strong> {recommendation}</p>"
            f"{'<p><strong>Strengths</strong></p><ul>' + strength_html + '</ul>' if strength_html else ''}"
            f"{f'<p><strong>Matched skills:</strong> {matched_html}</p>' if matched_html else ''}"
            f'<p><a href="{job_url}">Open job</a></p>'
        )
        text = (
            f"{score}/100 — {payload['title']}\n"
            f"{company_name} · {payload.get('location') or 'Location not provided'}\n\n"
            f"{payload.get('summary') or ''}\n\n"
            f"Recommendation: {payload.get('recommendation') or ''}\n"
            f"Strengths: {', '.join(strengths[:5])}\n"
            f"Matched skills: {', '.join(matched[:8])}\n\n"
            f"Open job: {payload.get('job_url') or ''}"
        )
        return EmailMessage(
            to_email=email,
            to_name=None,
            subject=f"AIlinkedin: {score}/100 match — {payload['title']}",
            html_content=html,
            text_content=text,
        )
