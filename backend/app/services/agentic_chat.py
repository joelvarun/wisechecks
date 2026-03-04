from typing import TypedDict, List, Dict

from langgraph.graph import StateGraph, END
from sqlalchemy import text
from sqlalchemy.orm import Session


class ChatState(TypedDict, total=False):
    case_id: int
    question: str
    retrieved_rows: List[dict]
    citations: List[dict]
    answer: str
    has_evidence: bool


def _retrieve(state: ChatState, db: Session) -> ChatState:
    rows = db.execute(text('''
      SELECT d.filename, p.page_number, p.ocr_text, p.document_id
      FROM pages p
      JOIN documents d ON p.document_id=d.id
      WHERE d.case_id=:c
        AND d.excluded=false
        AND p.text_search @@ plainto_tsquery('english', :q)
      ORDER BY ts_rank_cd(p.text_search, plainto_tsquery('english', :q)) DESC
      LIMIT 5
    '''), {'c': state['case_id'], 'q': state['question']}).mappings().all()
    return {'retrieved_rows': [dict(r) for r in rows]}


def _validate_evidence(state: ChatState) -> ChatState:
    rows = state.get('retrieved_rows', [])
    return {'has_evidence': len(rows) > 0}


def _build_refusal(_: ChatState) -> ChatState:
    return {
        'answer': 'I cannot answer with defensible evidence. Please refine your query.',
        'citations': [],
    }


def _build_answer(state: ChatState) -> ChatState:
    citations: List[Dict] = []
    snippets: List[str] = []
    for row in state.get('retrieved_rows', [])[:3]:
        excerpt = (row.get('ocr_text') or '')[:220]
        citations.append({
            'document': row.get('filename'),
            'document_id': row.get('document_id'),
            'page': row.get('page_number'),
            'excerpt': excerpt,
        })
        snippets.append(excerpt)

    return {
        'answer': f"Evidence-backed summary: {' | '.join(snippets[:2])}",
        'citations': citations,
    }


def _route_after_validation(state: ChatState) -> str:
    return 'answer' if state.get('has_evidence') else 'refuse'


def build_chat_graph(db: Session):
    graph = StateGraph(ChatState)
    graph.add_node('retrieve', lambda s: _retrieve(s, db))
    graph.add_node('validate', _validate_evidence)
    graph.add_node('answer', _build_answer)
    graph.add_node('refuse', _build_refusal)

    graph.set_entry_point('retrieve')
    graph.add_edge('retrieve', 'validate')
    graph.add_conditional_edges('validate', _route_after_validation, {'answer': 'answer', 'refuse': 'refuse'})
    graph.add_edge('answer', END)
    graph.add_edge('refuse', END)
    return graph.compile()


def run_agentic_chat(db: Session, case_id: int, question: str) -> dict:
    app = build_chat_graph(db)
    out = app.invoke({'case_id': case_id, 'question': question})
    return {'answer': out.get('answer', ''), 'citations': out.get('citations', [])}
