# 001. Scope v1 to one company; thesis shape

2026-10-18 · Accepted

## Context

The research agent takes a structured thesis from the input layer. Its shape decides what the agent can plan against.

## Decision

- One primary company per thesis. The object has a `peers` list, but it stays empty in v1 and the loop is built single-company. Peer research is a later phase.
- Ticker is required, CIK optional. The ticker is resolved through EDGAR's `company_tickers.json`. If it doesn't resolve, the run stops with `TICKER_UNRESOLVED`. The agent never guesses a match.
- A thesis is a list of claims, each with `id`, `text`, `direction` (bull/bear), and `evidence_needed` hints that seed the research plan.
- `lookback_years` defaults to 3.
- The input layer validates the thesis. The agent assumes it is well formed.

## Why

Single-company keeps the loop's state small enough to reason about while the hard parts (verification, termination) get built. A wrong CIK would make every downstream citation wrong while looking correct, so failing loudly is cheaper than guessing.

## Consequences

Pair trades and peer comparisons are out of scope until a later decision adds them.
