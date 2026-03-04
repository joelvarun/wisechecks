from sqlalchemy.orm import Session
from app.models.entities import AuditLog


def log_action(db: Session, case_id: int, actor_id: int, action_type: str, payload: dict):
    db.add(AuditLog(case_id=case_id, actor_id=actor_id, action_type=action_type, payload_json=payload))
    db.commit()
