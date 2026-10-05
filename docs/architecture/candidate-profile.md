# Phase 7 — Candidate profile

Candidate preferences are stored in the existing `candidate_profiles` JSONB column. Phase 7 adds a typed API and normalization layer without changing the database schema.

## Profile fields

The profile captures identity context, target roles, skills, technologies, certifications, education, languages, industries, preferred locations/countries, workplace and employment preferences, seniority, preferred/excluded companies, excluded keywords, salary floor, salary currency, experience and relocation preference.

## API

- `GET /api/v1/profile`
- `PUT /api/v1/profile`

The API currently uses `DEFAULT_USER_ID` as an explicit development-only user. Authentication/user scoping will replace this mechanism later.

## Normalization

Lists are trimmed and deduplicated case-insensitively while retaining the first display spelling. Salary currency is normalized to uppercase. The stored JSON contains a profile schema version so later migrations can evolve the shape without ambiguity.

Candidate profile data is not used to score jobs yet. Phase 8 consumes this profile to calculate fit and explainability.
