# Data Model Direction

Planned core entities:

- users
- candidate_profiles
- searches
- search_runs
- providers
- provider_runs
- companies
- jobs
- job_sources
- job_snapshots
- job_search_matches
- skills
- job_skills
- job_ai_analyses
- candidate_job_scores
- applications
- application_events
- notifications
- notification_deliveries
- parser_versions
- system_events
- errors

The model is intentionally separated into identity, source representation, historical snapshots and analysis so reposts and source changes do not destroy history.

Database implementation is Phase 2.
