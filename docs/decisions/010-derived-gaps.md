# 010. Gaps are derived from resolutions, never written

2026-10-18 · Accepted

## Context

Every agent result carries an explicit list of gaps: what couldn't be verified, and why. If gaps and resolutions are written separately, they can disagree.

## Decision

- Gaps are derived from resolutions when the result is built, and never written directly.
- Gaps live on the shared result envelope, so every agent reports missing data the same way.
- The envelope's `status` (complete, partial, failed) is separate from `termination_reason`, so the orchestrator can branch on status without interpreting reasons.

## Why

A single source of truth means the two can't drift. The memo writer can then render "what we couldn't verify" without knowing which agent produced it.

## Consequences

`build_research_result` is the only constructor path for a research result. The envelope can't enforce that on its own, because it doesn't know any one agent's derivation rule, so the rule is held by convention and tests.
