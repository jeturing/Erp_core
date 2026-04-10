"""API key audit logging helpers."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..models.database import ApiKeyAuditLog

logger = logging.getLogger(__name__)


def log_api_key_event(
    db: Session,
    *,
    key_id: str,
    auth_mode: Optional[str],
    path: Optional[str],
    method: Optional[str],
    ip_address: Optional[str],
    status_code: int,
    reject_reason: Optional[str] = None,
) -> None:
    """Persist audit event without raising upstream errors."""
    try:
        db.add(
            ApiKeyAuditLog(
                key_id=key_id,
                auth_mode=auth_mode,
                path=path,
                method=method,
                ip_address=ip_address,
                status_code=status_code,
                reject_reason=reject_reason,
            )
        )
    except Exception as exc:
        logger.warning("Failed to add API key audit event: %s", exc)
