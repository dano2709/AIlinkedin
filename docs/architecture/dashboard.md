# Phase 6 — Dashboard data integration

The dashboard is backed by PostgreSQL through a small read-only service layer.

## API

- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/jobs`
- `GET /api/v1/dashboard/search-runs`

The job endpoint supports pagination plus deterministic filters for free-text title/company search, job state, remote-only jobs and country code.

The dashboard does not perform provider scraping from the browser. The browser reads persisted canonical data from the API. This keeps provider credentials and scraping logic server-side.

## Web

The Next.js home page now loads overview statistics and the persisted job inventory from the API. A refresh button re-reads the database, while the search box and remote-only toggle re-query the job endpoint.

Phase 6 is intentionally unauthenticated. User-specific dashboard scoping is introduced with the candidate/authentication work in later phases.
