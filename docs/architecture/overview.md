# Architecture Overview

AIlinkedin is split into independent layers so the LinkedIn extraction mechanism can be replaced without rewriting the product.

## Layers

1. Web UI
2. Application API
3. Domain and business logic
4. Job intelligence pipeline
5. Provider adapters
6. External job sources

## Asynchronous pipeline

Scheduler
-> Search Queue
-> Discovery Workers
-> Deduplication
-> Detail Queue
-> Detail Workers
-> Normalization
-> Deterministic Filtering
-> AI Analysis
-> Ranking
-> Notifications

## Core rules

- Search is cheap; detail extraction is expensive.
- Deterministic filtering happens before deep AI work.
- Historical snapshots are retained.
- Provider-specific code stays behind an adapter boundary.
- Every extraction carries provenance and extractor version.
- Missing data is represented as unknown, never fabricated.

## Phase 1 boundary

The current repository establishes infrastructure only. Source adapters, canonical job tables and AI analysis are deliberately deferred until the foundation is verified.
