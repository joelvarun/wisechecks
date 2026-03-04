# WiseChecks MVP

Production-structured MVP for defensible claims/medical record review.

## Stack
- Backend: FastAPI + PostgreSQL + pgvector + Alembic
- Frontend: Next.js + TypeScript + Tailwind
- Storage: MinIO (S3-compatible)
- OCR/Extraction: pypdf text extraction + pluggable OCR interface

## Repo Structure
- `backend/` API, models, migrations, pipelines, tests
- `frontend/` Wisedocs-style UI shell with case workspace tabs and viewer pane
- `infra/` Docker Compose for local full stack
- `scripts/` seed/demo script

## Local Run
```bash
cd infra && docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- MinIO console: http://localhost:9001

## Seed Demo Data
```bash
cd backend
python -m pip install -r requirements.txt
alembic upgrade head
PYTHONPATH=. python ../scripts/seed_demo.py
```

## MVP Features Implemented
- Case workspace, chronology/timeline/documents/dedup/chat/reports tabs
- PDF upload pipeline with OCR text storage and tsvector + embedding indexing
- Rule-based event extraction with evidence pointers
- Duplicate grouping workflow with keep/remove action status
- Evidence-cited chat responses (refusal when evidence absent)
- Verified-only report generation with citations
- Audit logging for key reviewer actions

## Auth/RBAC
Scaffolded role model (`Admin`, `Reviewer`, `Viewer`) and JWT utilities included. Endpoints accept `actor_id` for MVP wiring and can be upgraded to strict auth middleware.

## Database Choice (Graph DB vs Relational)
- Current backend uses **PostgreSQL + pgvector** as the system of record and retrieval store.
- We are **not** using a graph database (e.g., Neo4j) in this MVP.
- Relationship traversal (event -> evidence -> page -> document) is handled with normalized relational schema and joins.

## Agentic Orchestration
- Added a **LangGraph**-based chat flow (`retrieve -> validate evidence -> answer/refuse`) to make Q&A behavior more agentic while preserving strict citation requirements.
- The graph always refuses when no evidence is retrieved, supporting no-hallucination constraints.
