# Search Query Compiler

`SearchQueryCompiler` converts user intent into a provider-neutral `CompiledSearch`.

## Inputs
- titles
- keywords
- locations
- remote preference
- employment types
- seniority
- companies
- posting age
- exclusions
- natural-language query
- imported LinkedIn URL

## Outputs
- search text
- optional normalized LinkedIn URL
- structured constraints
- deterministic post-filters
- AI-only constraints
- unsupported constraints

## Design rule
LinkedIn URL parameters are transport hints, not the application's source of truth.
Important constraints remain available to deterministic filtering after extraction. Business logic therefore stays independent of changes in LinkedIn search behavior.