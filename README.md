# AIlinkedin

Production-oriented LinkedIn Job Intelligence application.

## Current status

Phase 5 is implemented.

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
- PostgreSQL job/company upsert
- deterministic job identity and deduplication
- source provenance records
- change-only historical snapshots
- unit and API contract tests
- GitHub Actions CI

## Phase 5 persistence API

Import one LinkedIn job from Apify and persist it:

`POST /api/v1/jobs/import`

Example:

```json
{
  "source_job_id": "4459772101",
  "discovered_from": "manual"
}
```

The import flow:
1. Fetches the current job detail from Apify.
2. Normalizes it into the canonical job shape.
3. Upserts the company.
4. Matches by source ID, canonical URL, external apply URL, and conservative title/company/location signals.
5. Updates the canonical job without creating duplicates.
6. Records the source/provenance.
7. Creates a `JobSnapshot` only for a new job or a detected content change.

The PostgreSQL schema already contained the required job, company, source and snapshot tables, so Phase 5 does not require a new migration.

## Phase 4 detail API

Resolve a single LinkedIn job into canonical data without persistence:

`POST /api/v1/providers/apify/details`

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
5. Normalization, deduplication and history — complete
6. Dashboard data integration
7. Candidate profile
8. AI scoring
9. Notifications
10. Provider fallback
11. Observability and production hardening
