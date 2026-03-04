import hashlib
import io
import re
from datetime import datetime
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.entities import Document, Page, Evidence, Event, EventTypeEnum


DATE_RE = re.compile(r'(\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b)')


def fake_embed(text_value: str) -> list[float]:
    base = hashlib.md5(text_value.encode()).digest()
    return [((base[i % len(base)] / 255.0) * 2 - 1) for i in range(128)]


def ingest_pdf(db: Session, case_id: int, uploaded_by: int, filename: str, data: bytes, s3_uri: str):
    file_hash = hashlib.sha256(data).hexdigest()
    doc = Document(case_id=case_id, filename=filename, s3_uri=s3_uri, file_hash=file_hash, uploaded_by=uploaded_by, doc_type='medical_record')
    db.add(doc)
    db.flush()

    reader = PdfReader(io.BytesIO(data))
    for i, page in enumerate(reader.pages, start=1):
        extracted = (page.extract_text() or '').strip()
        page_obj = Page(
            document_id=doc.id,
            page_number=i,
            ocr_text=extracted,
            ocr_confidence=0.8 if extracted else 0.1,
            text_search=' ',
            embedding=fake_embed(extracted or f'page-{i}')
        )
        db.add(page_obj)
    doc.page_count = len(reader.pages)
    db.commit()
    db.execute(text("UPDATE pages SET text_search = to_tsvector('english', coalesce(ocr_text,'')) WHERE document_id=:d"), {'d': doc.id})
    db.commit()
    return doc


def extract_date_events(db: Session, case_id: int, actor_id: int):
    pages = db.execute(text('''
      SELECT p.document_id, p.page_number, p.ocr_text
      FROM pages p JOIN documents d on p.document_id=d.id
      WHERE d.case_id=:c and d.excluded=false
    '''), {'c': case_id}).fetchall()
    created = []
    for row in pages:
        text_val = row.ocr_text or ''
        for match in DATE_RE.finditer(text_val):
            date_text = match.group(0)
            normalized = date_text.replace('/', '-')
            try:
                dt = datetime.fromisoformat(normalized if len(normalized) == 10 else f'20{normalized[-2:]}-{normalized[:2]}-{normalized[3:5]}').date()
            except Exception:
                continue
            ev = Evidence(document_id=row.document_id, page_number=row.page_number, start_char=match.start(), end_char=match.end(), quote=text_val[max(0, match.start()-40):match.end()+80])
            db.add(ev)
            db.flush()
            event = Event(
                case_id=case_id,
                event_type=EventTypeEnum.Note,
                event_date=dt,
                title=f'Clinical note date mention {date_text}',
                structured_fields={'source': 'rule_date_extractor'},
                evidence_ids=[ev.id],
                created_by=actor_id,
                updated_by=actor_id,
            )
            db.add(event)
            created.append(event)
    db.commit()
    return created


def run_dedup(db: Session, case_id: int):
    rows = db.execute(text('''
        SELECT p.document_id, p.page_number, md5(regexp_replace(lower(coalesce(p.ocr_text,'')), '\\s+', '', 'g')) as sig
        FROM pages p JOIN documents d on p.document_id=d.id
        WHERE d.case_id=:c
    '''), {'c': case_id}).fetchall()
    groups = {}
    for r in rows:
        groups.setdefault(r.sig, []).append(r)
    from app.models.entities import DuplicateGroup, DuplicateItem
    out = []
    for sig, items in groups.items():
        if len(items) < 2:
            continue
        g = DuplicateGroup(case_id=case_id, group_hash=sig, match_score=0.99)
        db.add(g)
        db.flush()
        for it in items:
            db.add(DuplicateItem(duplicate_group_id=g.id, document_id=it.document_id, page_number=it.page_number))
        out.append(g)
    db.commit()
    return out
