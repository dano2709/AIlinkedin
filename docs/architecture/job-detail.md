# Phase 4 — Job detail extraction

Phase 4 converts the Apify LinkedIn job detail response into a provider-neutral canonical job object.

The detail request enables company profile and enriched job signals. The canonical object contains structured salary, location, timestamps, application data, ATS detection, job state, repost state, company enrichment and provenance.

No PostgreSQL write happens in Phase 4. Persistence, deduplication and snapshots are handled in Phase 5.
