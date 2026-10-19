# 008. What the agent can fetch, and in what size

2026-10-18 · Proposed

## Context

A 10-K can run past 300k tokens. EDGAR offers three surfaces: the submissions index, filing documents, and XBRL company facts.

## Decision

- **All three surfaces:** XBRL for numbers, documents for prose.
- **Fetches are section-level, never whole filings.** Results are paged at a 3k-token cap per page with about 200 characters of overlap between pages, both configurable.
- **Phase 0 fetches the submissions index once**, before the loop starts. The index is filtered to 10-K, 10-Q, 8-K, and DEF 14A within the lookback window. 8-Ks are rendered compactly. If the list is still too long, it is truncated explicitly, never silently.

## Why

- **Overlap:** a quote that spans a page boundary still appears intact on one page, so a verbatim check doesn't fail on how the page was cut.
- **Pre-fetching the index:** the model's real decision is which filing and section to read. Spending an iteration to discover what filings exist adds nothing.

## Consequences

- Proxy statements (DEF 14A) have no standard item structure, so their sections are matched by heading. That is the weakest extraction path.
