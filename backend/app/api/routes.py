from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.models.entities import Case, Event, DuplicateItem, ChatSession, ChatMessage, ReportTemplate
from app.schemas.common import CaseCreate, EventUpdate, ChatRequest, DedupActionRequest, ReportGenerateRequest
from app.services.pipeline import ingest_pdf, extract_date_events, run_dedup
from app.services.storage import ensure_bucket, upload_bytes
from app.services.chat import answer_question
from app.services.reports import generate_verified_report
from app.services.audit import log_action

router = APIRouter()


@router.post('/cases')
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    c = Case(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get('/cases')
def list_cases(db: Session = Depends(get_db)):
    return db.query(Case).order_by(Case.created_at.desc()).all()


@router.post('/cases/{case_id}/documents/upload')
def upload_document(case_id: int, uploaded_by: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    ensure_bucket()
    data = file.file.read()
    uri = upload_bytes(f'case-{case_id}/{file.filename}', data)
    doc = ingest_pdf(db, case_id, uploaded_by, file.filename, data, uri)
    events = extract_date_events(db, case_id, uploaded_by)
    dedup_groups = run_dedup(db, case_id)
    log_action(db, case_id, uploaded_by, 'document_upload', {'document_id': doc.id, 'events_created': len(events), 'dedup_groups': len(dedup_groups)})
    return {'document_id': doc.id, 'events_created': len(events), 'dedup_groups': len(dedup_groups)}


@router.get('/cases/{case_id}/events')
def get_events(case_id: int, db: Session = Depends(get_db)):
    return db.query(Event).filter(Event.case_id == case_id).order_by(Event.event_date.asc()).all()


@router.patch('/cases/{case_id}/events/{event_id}')
def update_event(case_id: int, event_id: int, payload: EventUpdate, actor_id: int, db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.case_id == case_id, Event.id == event_id).first()
    if not ev:
        raise HTTPException(404, 'Event not found')
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(ev, k, v)
    ev.updated_by = actor_id
    db.commit()
    log_action(db, case_id, actor_id, 'event_update', {'event_id': event_id, 'changes': payload.model_dump(exclude_none=True)})
    return ev


@router.get('/cases/{case_id}/dedup')
def dedup_groups(case_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text('''
      SELECT g.id as group_id, g.group_hash, g.match_score, json_agg(json_build_object('item_id', i.id, 'document_id', i.document_id, 'page_number', i.page_number, 'action_status', i.action_status)) as items
      FROM duplicate_groups g JOIN duplicate_items i ON i.duplicate_group_id=g.id
      WHERE g.case_id=:c GROUP BY g.id
    '''), {'c': case_id}).mappings().all()
    return rows


@router.post('/cases/{case_id}/dedup/action')
def dedup_action(case_id: int, payload: DedupActionRequest, actor_id: int, db: Session = Depends(get_db)):
    item = db.query(DuplicateItem).filter(DuplicateItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(404, 'Duplicate item not found')
    item.action_status = payload.action_status
    db.commit()
    log_action(db, case_id, actor_id, 'dedup_action', payload.model_dump())
    return {'ok': True}


@router.post('/cases/{case_id}/chat')
def chat(case_id: int, payload: ChatRequest, actor_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.case_id == case_id, ChatSession.created_by == actor_id).order_by(ChatSession.id.desc()).first()
    if not session:
        session = ChatSession(case_id=case_id, created_by=actor_id)
        db.add(session)
        db.flush()
    ans = answer_question(db, case_id, payload.question)
    db.add(ChatMessage(session_id=session.id, role='user', content=payload.question, evidence_ids=[]))
    db.add(ChatMessage(session_id=session.id, role='assistant', content=ans['answer'], evidence_ids=[]))
    db.commit()
    log_action(db, case_id, actor_id, 'chat_question', {'question': payload.question, 'citation_count': len(ans['citations'])})
    return ans


@router.get('/report-templates')
def list_templates(db: Session = Depends(get_db)):
    return db.query(ReportTemplate).all()


@router.post('/cases/{case_id}/reports/generate')
def generate_report(case_id: int, payload: ReportGenerateRequest, actor_id: int, db: Session = Depends(get_db)):
    report = generate_verified_report(db, case_id, payload.template_id, actor_id)
    log_action(db, case_id, actor_id, 'report_generated', {'report_id': report.id, 'template_id': payload.template_id})
    return report


@router.get('/cases/{case_id}/audit-logs')
def audit(case_id: int, db: Session = Depends(get_db)):
    return db.execute(text('SELECT * FROM audit_logs WHERE case_id=:c ORDER BY created_at DESC'), {'c': case_id}).mappings().all()
