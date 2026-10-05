# Apify LinkedIn Provider

Phase 3 uses the bebity/linkedin-jobs-scraper Actor through the Apify REST API.

The current Actor documentation exposes multiple titles and locations in one run, search URL input, workplace/employment/experience/Easy Apply/applicant filters, structured salary fields, canonical job ID and URL, direct application URL, company data and provenance via scrapingInfo.

The adapter calls the synchronous dataset endpoint:

POST /v2/acts/bebity~linkedin-jobs-scraper/run-sync-get-dataset-items

Provider-specific payload fields are translated inside ApifyLinkedInAdapter. The core domain never consumes Apify-shaped records.

The application defaults to a low result cap (25) to control cost. Paid hiring-contact enrichment remains disabled.

Required environment variable: APIFY_API_TOKEN

Optional: APIFY_ACTOR_ID, APIFY_BASE_URL, APIFY_TIMEOUT_SECONDS, APIFY_DEFAULT_ROWS