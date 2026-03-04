from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.agentic_chat import run_agentic_chat


def answer_question(db: Session, case_id: int, question: str):
    return run_agentic_chat(db, case_id, question)


def answer_question_legacy(db: Session, case_id: int, question: str):
    rows = db.execute(text('''
      SELECT d.filename, p.page_number, p.ocr_text, p.document_id
      FROM pages p join documents d on p.document_id=d.id
      WHERE d.case_id=:c and d.excluded=false and p.text_search @@ plainto_tsquery('english', :q)
      ORDER BY ts_rank_cd(p.text_search, plainto_tsquery('english', :q)) DESC
      LIMIT 3
    '''), {'c': case_id, 'q': question}).fetchall()
    if not rows:
        return {'answer': 'I cannot answer with defensible evidence. Please refine your query.', 'citations': []}
    citations = []
    snippets = []
    for r in rows:
        excerpt = (r.ocr_text or '')[:220]
        citations.append({'document': r.filename, 'document_id': r.document_id, 'page': r.page_number, 'excerpt': excerpt})
        snippets.append(excerpt)
    return {'answer': f"Evidence-backed summary: {' | '.join(snippets[:2])}", 'citations': citations}
