# 006. Termination conditions, caps, and failure handling

2026-10-18 · Accepted

## Context

An agent loop needs to stop for a reason that can be checked, and a run that stops early needs to say why.

## Decision

Three caps, all configurable: 12 iterations, 300k tokens, 600 seconds of wall clock. The development default for iterations is 3.

Every way the loop ends is a distinct recorded reason, never a generic timeout: plan satisfied, iteration cap, token budget, wall clock, stalled (two consecutive model turns with no tool calls while items are open), tool failure streak (five consecutive failed tool calls), model API error, model refusal, ticker unresolved, plan generation failed.

Failures are handled per tool call, never around the whole loop:

- Transient errors (429, 5xx, timeout) retry inside the tool, at most twice with backoff. Every request has a timeout.
- Permanent errors (404, section not found) go back to the model as structured errors and are logged as attempts.
- A repeated call that already failed permanently returns the cached error without refetching.
- A truncated model response (`max_tokens`) counts as a failed call and increments the failure streak.

The server-side refusal fallback stays off.

## Why

- **Iterations at about 1.5x expected:** thrashing shows up as PARTIAL instead of hiding under headroom.
- **Wall clock raised:** EDGAR latency is outside our control, and I don't want network conditions polluting the termination-reason distribution.
- **Truncation counts as a failure:** repeated truncation then surfaces as a signal that `max_tokens` is too low.
- **Fallback off:** it would silently switch models mid-run and break reproducibility.

## Consequences

A cap trip produces no final summarizing model call. The result is built by code from run state, and every open item becomes "open at termination."
