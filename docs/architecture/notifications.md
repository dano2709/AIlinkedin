# Notifications

Phase 9 adds high-fit job notifications on top of the Phase 8 scoring pipeline.

## Trigger

A notification is considered after a job is successfully scored.

The notification is created only when:

- notification preferences exist and are enabled;
- the calculated Fit Score is at least the configured `min_fit_score`.

The fingerprint is deterministic per user, job and threshold, preventing duplicate high-fit alerts for the same threshold.

## Delivery

Email delivery uses Brevo transactional email. The backend calls Brevo's `POST /v3/smtp/email` endpoint with server-side credentials.

Required server settings:

- `BREVO_API_KEY`
- `NOTIFICATION_SENDER_EMAIL`
- optional sender name/base URL/timeout settings

The recipient email and Fit Score threshold are stored in `notification_preferences`, so they can be changed without redeploying.

## Persistence

`notifications` stores the logical notification and its payload.

`notification_deliveries` stores the channel, status, provider message id, timestamp and delivery error.

A provider failure changes the delivery to `FAILED` and is persisted; it does not turn an otherwise successful job scoring request into a 5xx response.

## API

`GET /api/v1/notifications/preferences`

`PUT /api/v1/notifications/preferences`

`GET /api/v1/notifications?limit=20`

## Development

Run migrations before using the notification settings in an existing database:

    docker compose exec api alembic upgrade head

For a local test, configure the Brevo sender and API key in `.env`, then enable notifications from the dashboard and set the minimum Fit Score.

No notification is sent for scores below the configured threshold.
