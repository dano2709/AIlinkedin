# Phase 8 — AI job scoring

Phase 8 compares the normalized candidate profile with persisted canonical jobs.

## Score

The model returns seven validated components:

- title alignment: 25 points
- skills match: 25 points
- experience match: 15 points
- location/workplace: 10 points
- compensation: 10 points
- industry/company: 5 points
- exclusions: 10 points

The backend sums those validated components and clamps the result to 0–100. The model does not control the final total.

The stored result includes confidence, matched skills, missing skills, strengths, concerns, recommendation and summary. The full result is stored in JobAIAnalysis; the current profile/job result is stored in CandidateJobScore.

## API

Score a job:

POST /api/v1/jobs/{job_id}/score

Request body: {"force": false}

A cached score is returned when one already exists. Set force to true to recalculate and append a new analysis.

Read an existing score:

GET /api/v1/jobs/{job_id}/score

## Provider

The default implementation is the OpenAI Responses API using gpt-6-luna. OpenAI API credentials stay server-side. The scoring provider is isolated behind a protocol so another model provider can be added later.

The current API entrypoint used by Docker is app.main_phase8:app, which adds the scoring router to the existing application without changing the Phase 7 test entrypoint.
