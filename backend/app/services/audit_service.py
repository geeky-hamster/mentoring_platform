"""AuditService (component C11): append-only trail of sensitive actions."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AuditLog


def record(db: Session, actor_user_id, action: str, entity_type: str, entity_id,
           details: dict | None = None, ip_address: str | None = None) -> None:
    db.add(AuditLog(actor_user_id=actor_user_id, action=action[:100], entity_type=entity_type[:50],
                    entity_id=entity_id, details=details or {}, ip_address=ip_address))
