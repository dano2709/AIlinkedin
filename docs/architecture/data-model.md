# Data Model

Phase 2 introduces the canonical relational model.

## Identity
- `jobs.source + jobs.source_job_id` is the primary source identity.
- `jobs.canonical_url` is a secondary identity.
- `job_sources` preserves discovery provenance.
- `job_snapshots` preserves historical versions.

## Search
- `searches` stores the user-owned search definition as JSON.
- `search_runs` stores each execution and provider metrics.
- `job_search_matches` links searches to jobs without duplicating job records.

## Analysis
- `candidate_profiles` stores structured candidate information separately from jobs.
- `job_ai_analyses` stores model output with model and prompt version.
- `candidate_job_scores` stores the candidate/job ranking result.

## Applications
- `applications` stores the current application state.
- `application_events` stores status history.

## Operations
- `providers` and `provider_runs` track source providers.
- `parser_versions` supports parser lifecycle management.
- `system_events` and `errors` provide an operational audit trail.

The first Alembic revision creates the canonical metadata. Future migrations should be incremental and explicit.