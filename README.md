# AIlinkedin

Production-oriented LinkedIn Job Intelligence application.

## Current status

Phase 2 is implemented.

Implemented foundation:
- FastAPI backend
- Next.js frontend
- PostgreSQL and Redis Docker services
- SQLAlchemy domain model
- Alembic migration foundation
- provider-neutral JobSourceAdapter
- SearchQueryCompiler
- search compiler API endpoint
- unit and API contract tests
- GitHub Actions CI

## Phase 2 architecture

Search intent is compiled into:
- provider-facing search text/URL
- structured constraints
- deterministic post-filters
- AI-only constraints
- unsupported constraints

Job data is modeled around source identity, search runs, companies, canonical jobs, provenance, historical snapshots, AI analysis, applications and notifications.

## Local development

Requirements: Docker Desktop with Docker Compose.

~~~bash
cp .env.example .env
docker compose up --build
~~~

API: http://localhost:8000
API docs: http://localhost:8000/docs
Web: http://localhost:3000

## Roadmap

1. Repository foundation
2. Database/domain models and search compiler — complete
3. Search provider integration — Apify LinkedIn adapter complete
4. Job detail extraction
5. Normalization, deduplication and history
6. Dashboard data integration
7. Candidate profile
8. AI scoring
9. Notifications
10. Provider fallback
11. Observability and production hardening