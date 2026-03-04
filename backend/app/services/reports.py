from sqlalchemy.orm import Session
from app.models.entities import Event, VerificationEnum, Evidence, Report


def generate_verified_report(db: Session, case_id: int, template_id: int, user_id: int):
    events = db.query(Event).filter(Event.case_id == case_id, Event.verification_status == VerificationEnum.verified).order_by(Event.event_date.asc()).all()
    sections = []
    citations = {}
    for idx, e in enumerate(events, start=1):
        refs = db.query(Evidence).filter(Evidence.id.in_(e.evidence_ids)).all() if e.evidence_ids else []
        cite = [{'evidence_id': r.id, 'doc': r.document_id, 'page': r.page_number, 'quote': r.quote} for r in refs]
        citations[f'event_{idx}'] = cite
        sections.append(f"<h3>{e.event_date} - {e.title}</h3><p>Status: {e.verification_status.value}</p>")
    html = '<h1>Verified Chronology Report</h1>' + ''.join(sections)
    report = Report(case_id=case_id, template_id=template_id, generated_by=user_id, html_content=html, citations_by_section=citations)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
