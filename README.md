# AIlinkedin

Production-oriented LinkedIn Job Intelligence application.

## Current status

Phase 4 is implemented.

Implemented foundation:
- FastAPI backend
- Next.js frontend
- PostgreSQL and Redis Docker services
- SQLAlchemy domain model
- Alembic migration foundation
- provider-neutral JobSourceAdapter
- SearchQueryCompiler
- Apify LinkedIn search integration
- Apify LinkedIn detail extraction and canonical job normalization
- company enrichment mapping
- salary, location, timestamp and applicant parsing
- ATS/apply URL detection
- job-state and repost signals
- unit and API contract tests
- GitHub Actions CI

## Phase 4 detail API

Resolve a single LinkedIn job into canonical data:

`POST /api/v1/providers/apify/details`

Request:

```json
{
  "source_job_id": "4459772101"
}
```

or:

```json
{
  "job_url": "https://www.linkedin.com/jobs/view/4459772101"
}
```

Phase 4 does not persist the result yet. Phase 5 will add persistence, deduplication and historical snapshots.

## Local development

Requirements: Docker Desktop with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000
API docs: http://localhost:8000/docs
Web: http://localhost:3000

## Roadmap

1. Repository foundation
2. Database/domain models and search compiler — complete
3. Search provider integration — complete
4. Job detail extraction — complete
5. Normalization, deduplication and history
6. Dashboard data integration
7. Candidate profile
8. AI scoring
9. Notifications
10. Provider fallback
11. Observability and production hardening
