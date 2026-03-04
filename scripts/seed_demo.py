from datetime import datetime
from reportlab.pdfgen import canvas
from app.db.session import SessionLocal
from app.models.entities import User, RoleEnum, Case, ReportTemplate
from app.services.security import hash_password
from app.services.pipeline import ingest_pdf, extract_date_events, run_dedup


def build_pdf(path: str):
    c = canvas.Canvas(path)
    c.drawString(100, 750, 'Encounter note on 2024-01-14 for knee pain diagnosis')
    c.drawString(100, 730, 'Follow up date 2024-02-21 with imaging ordered')
    c.showPage()
    c.drawString(100, 750, 'Encounter note on 2024-01-14 for knee pain diagnosis')
    c.save()


def run():
    db = SessionLocal()
    user = User(email='reviewer@demo.com', password_hash=hash_password('demo123'), role=RoleEnum.reviewer)
    case = Case(case_number='WC-1001', claimant_name='Jane Claimant', insurer='DemoInsure')
    tmpl = ReportTemplate(name='Chronology Summary', section_rules={'include_verified_only': True})
    db.add_all([user, case, tmpl])
    db.commit(); db.refresh(user); db.refresh(case)
    pdf_path = '/tmp/demo_case.pdf'
    build_pdf(pdf_path)
    with open(pdf_path, 'rb') as f:
        data = f.read()
    ingest_pdf(db, case.id, user.id, 'demo_case.pdf', data, 's3://docs/demo_case.pdf')
    extract_date_events(db, case.id, user.id)
    run_dedup(db, case.id)
    print('Seed complete')


if __name__ == '__main__':
    run()
