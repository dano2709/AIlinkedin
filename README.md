# AIlinkedin

Production-oriented LinkedIn Job Intelligence application.

## Current status

Phase 7 is implemented.

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
- dashboard read service over PostgreSQL
- dashboard overview, jobs and search-run APIs
- live Next.js dashboard with job search and remote filter
- browser-to-API CORS configuration
- typed candidate profile schema and normalization
- candidate profile PostgreSQL persistence
- candidate profile GET/PUT API
- editable candidate profile dashboard section
- unit and API contract tests
- GitHub Actions CI

## Phase 6 dashboard API

Overview:

`GET /api/v1/dashboard/overview`

Job inventory:

`GET /api/v1/dashboard/jobs?limit=50&query=python&remote_only=true`

Recent search runs:

`GET /api/v1/dashboard/search-runs?limit=10`

The dashboard reads persisted canonical data. Scraping and provider credentials remain on the backend.

The dashboard is intentionally unauthenticated at this stage. User-specific scoping will be added with candidate/authentication work.

## Phase 7 candidate profile API

Read the current development candidate profile:

`GET /api/v1/profile`

Update it:

`PUT /api/v1/profile`

The profile is stored in the existing `candidate_profiles.profile` JSONB field. Lists are normalized and deduplicated before persistence.

The current API uses `DEFAULT_USER_ID` as an explicit development-only identity until authentication is introduced.

## Phase 5 persistence API

Import one LinkedIn job from Apify and persist it:

`POST /api/v1/jobs/import`

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
6. Dashboard data integration — complete
7. Candidate profile — complete
8. AI scoring
9. Notifications
10. Provider fallback
11. Observability and production hardening
