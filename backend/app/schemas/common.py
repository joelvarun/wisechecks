from datetime import date, datetime
from pydantic import BaseModel


class CaseCreate(BaseModel):
    case_number: str
    claimant_name: str
    dob: date | None = None
    insurer: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    verification_status: str | None = None
    structured_fields: dict | None = None


class ChatRequest(BaseModel):
    question: str


class DedupActionRequest(BaseModel):
    item_id: int
    action_status: str


class ReportGenerateRequest(BaseModel):
    template_id: int
