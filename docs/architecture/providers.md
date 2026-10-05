# Provider Architecture

The application uses a provider-neutral boundary. The domain consumes canonical job data and does not know how a source was accessed.

Conceptual interface:

~~~python
class JobSourceAdapter(Protocol):
    async def search(...) -> ...
    async def get_job_details(...) -> ...
    async def health_check(...) -> ...
~~~

Potential adapters:

- LinkedIn browser adapter
- Licensed third-party provider adapter
- RSS discovery adapter

Provider-specific responsibilities include selectors, session handling, retry behavior, rate limits and source health.

The rest of the application must not contain LinkedIn DOM selectors or provider-specific response parsing.
