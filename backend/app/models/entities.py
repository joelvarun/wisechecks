from datetime import datetime, date
from enum import Enum
from sqlalchemy import (
    String, DateTime, ForeignKey, Integer, Text, Date, JSON, Enum as SAEnum, Float, Boolean, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR, ARRAY
from pgvector.sqlalchemy import Vector
from app.db.session import Base


class RoleEnum(str, Enum):
    admin = 'Admin'
    reviewer = 'Reviewer'
    viewer = 'Viewer'


class VerificationEnum(str, Enum):
    unverified = 'Unverified'
    verified = 'Verified'
    disputed = 'Disputed'


class EventTypeEnum(str, Enum):
    Encounter = 'Encounter'
    Symptom = 'Symptom'
    Diagnosis = 'Diagnosis'
    Procedure = 'Procedure'
    Lab = 'Lab'
    Imaging = 'Imaging'
    Medication = 'Medication'
    CarePlan = 'CarePlan'
    Note = 'Note'


class DuplicateActionEnum(str, Enum):
    None_ = 'None'
    Keep = 'Keep'
    Remove = 'Remove'


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum), default=RoleEnum.reviewer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = 'cases'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    claimant_name: Mapped[str] = mapped_column(String(255), index=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    insurer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('cases.id'), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    s3_uri: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str] = mapped_column(String(128), index=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    doc_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)


class Page(Base):
    __tablename__ = 'pages'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id'), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    ocr_text: Mapped[str] = mapped_column(Text)
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    text_search: Mapped[str] = mapped_column(TSVECTOR)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(128), nullable=True)


class Evidence(Base):
    __tablename__ = 'evidence'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id'))
    page_number: Mapped[int] = mapped_column(Integer)
    start_char: Mapped[int] = mapped_column(Integer)
    end_char: Mapped[int] = mapped_column(Integer)
    bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    quote: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('cases.id'), index=True)
    event_type: Mapped[EventTypeEnum] = mapped_column(SAEnum(EventTypeEnum), default=EventTypeEnum.Note)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    structured_fields: Mapped[dict] = mapped_column(JSON, default={})
    verification_status: Mapped[VerificationEnum] = mapped_column(SAEnum(VerificationEnum), default=VerificationEnum.unverified)
    evidence_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=[])
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    updated_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DuplicateGroup(Base):
    __tablename__ = 'duplicate_groups'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('cases.id'), index=True)
    group_hash: Mapped[str] = mapped_column(String(128), index=True)
    match_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DuplicateItem(Base):
    __tablename__ = 'duplicate_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    duplicate_group_id: Mapped[int] = mapped_column(ForeignKey('duplicate_groups.id'))
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id'))
    page_number: Mapped[int] = mapped_column(Integer)
    action_status: Mapped[DuplicateActionEnum] = mapped_column(SAEnum(DuplicateActionEnum), default=DuplicateActionEnum.None_)


class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('cases.id'))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('chat_sessions.id'))
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=[])
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReportTemplate(Base):
    __tablename__ = 'report_templates'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    section_rules: Mapped[dict] = mapped_column(JSON)


class Report(Base):
    __tablename__ = 'reports'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('cases.id'))
    template_id: Mapped[int] = mapped_column(ForeignKey('report_templates.id'))
    generated_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    html_content: Mapped[str] = mapped_column(Text)
    citations_by_section: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey('cases.id'), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    action_type: Mapped[str] = mapped_column(String(120), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
