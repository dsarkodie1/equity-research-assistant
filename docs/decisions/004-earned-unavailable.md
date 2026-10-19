# 004. "Unavailable" is a valid outcome but must be earned

2026-10-18 · Accepted

## Context

Plan items can legitimately have no evidence. A company may not disclose a figure at all. But if marking an item unavailable is free, the cheapest path to "plan satisfied" is to mark everything unavailable in the first iteration.

## Decision

`mark_unavailable` must cite at least one of:

- an attempt id from this run's fetch log, or
- the Phase 0 submissions index showing no filing of the relevant type in the lookback window.

Code verifies whichever is cited.

"Unavailable" (looked, and the evidence isn't there) is a separate state from "open at termination" (the run stopped before finishing). They are never merged.

## Why

This applies the same rule as decision 003 to the negative case. Keeping the two states separate stops the memo from saying "not disclosed" when the truth is "we didn't get to it."

## Consequences

A run where every item is unavailable can still be COMPLETE. That is correct: it is an informative result, not a failure.
