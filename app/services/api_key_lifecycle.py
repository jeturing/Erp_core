"""API key lifecycle maintenance tasks (GW-009/GW-010 support)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.database import ApiKey, ApiKeyStatus, ApiKeyRotationRequest, ApiKeyRotationStatus

logger = logging.getLogger(__name__)


def cleanup_api_keys(db: Session) -> dict[str, int]:
    """Revokes rotating keys after grace period and expires stale records."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    revoked_rotating = (
        db.query(ApiKey)
        .filter(
            ApiKey.status == ApiKeyStatus.rotating,
            ApiKey.expires_at.isnot(None),
            ApiKey.expires_at <= now,
        )
        .update(
            {
                ApiKey.status: ApiKeyStatus.revoked,
                ApiKey.updated_at: now,
            },
            synchronize_session=False,
        )
    )

    expired_active = (
        db.query(ApiKey)
        .filter(
            ApiKey.status.in_([ApiKeyStatus.active, ApiKeyStatus.rotating]),
            ApiKey.expires_at.isnot(None),
            ApiKey.expires_at <= now,
        )
        .update(
            {
                ApiKey.status: ApiKeyStatus.expired,
                ApiKey.updated_at: now,
            },
            synchronize_session=False,
        )
    )

    expired_rotation_requests = (
        db.query(ApiKeyRotationRequest)
        .filter(
            ApiKeyRotationRequest.status == ApiKeyRotationStatus.pending,
            ApiKeyRotationRequest.expires_at <= now,
        )
        .update(
            {
                ApiKeyRotationRequest.status: ApiKeyRotationStatus.expired,
                ApiKeyRotationRequest.resolved_at: now,
            },
            synchronize_session=False,
        )
    )

    db.commit()

    result = {
        "revoked_rotating": int(revoked_rotating or 0),
        "expired_active": int(expired_active or 0),
        "expired_rotation_requests": int(expired_rotation_requests or 0),
    }
    if any(result.values()):
        logger.info("🔑 API key lifecycle cleanup: %s", result)
    return result
