from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..notification_schemas import (
    NotificationDeliveryResponse,
    NotificationHistoryResponse,
    NotificationPreferencesInput,
    NotificationPreferencesResponse,
    NotificationResponse,
)
from ..services.notifications import (
    NotificationPreferencesData,
    NotificationService,
)
from ..settings import settings


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])
db_dependency = Depends(get_db)


def preferences_response(result) -> NotificationPreferencesResponse:
    return NotificationPreferencesResponse(
        user_id=result.user_id,
        exists=result.exists,
        preferences=NotificationPreferencesInput(
            enabled=result.data.enabled,
            email=result.data.email,
            min_fit_score=result.data.min_fit_score,
        ),
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_preferences(session: Session = db_dependency) -> NotificationPreferencesResponse:
    result = NotificationService(session).get_preferences(UUID(settings.default_user_id))
    return preferences_response(result)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_preferences(
    payload: NotificationPreferencesInput,
    session: Session = db_dependency,
) -> NotificationPreferencesResponse:
    result = NotificationService(session).upsert_preferences(
        UUID(settings.default_user_id),
        NotificationPreferencesData(
            enabled=payload.enabled,
            email=payload.email,
            min_fit_score=payload.min_fit_score,
        ),
    )
    session.commit()
    return preferences_response(result)


@router.get("", response_model=NotificationHistoryResponse)
def recent_notifications(
    limit: int = 20,
    session: Session = db_dependency,
) -> NotificationHistoryResponse:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")

    notifications, deliveries = NotificationService(session).recent(
        UUID(settings.default_user_id),
        limit=limit,
    )
    return NotificationHistoryResponse(
        notifications=[
            NotificationResponse(
                id=item.id,
                type=item.type,
                fingerprint=item.fingerprint,
                payload=item.payload,
                created_at=item.created_at,
            )
            for item in notifications
        ],
        deliveries=[
            NotificationDeliveryResponse(
                notification_id=item.notification_id,
                channel=item.channel,
                status=item.status,
                sent_at=item.sent_at,
                error=item.error,
            )
            for item in deliveries
        ],
    )
