# 007. Token budget counts new work; prompt caching

2026-10-18 · Accepted

## Context

The full conversation history is re-sent on every model call, so cumulative input grows with every iteration. Counted raw, a normal 12-iteration run would come to about 600k input tokens and trip a 300k budget around iteration 7.

## Decision

- The token budget counts output tokens plus uncached new input, including cache writes. Cache reads are tracked and reported but don't count toward the cap.
- Every run reports an estimated dollar cost, priced per model and per token class.
- Prompt caching: an explicit cache breakpoint after the tools and system prompt (shared across runs), another after the per-run context (thesis, filing index, frozen plan), and automatic caching for the growing tail. The history is append-only. Status notes are never deleted.
- Things that would silently break the cache are banned: timestamps or run ids in the system prompt, non-deterministic tool order or JSON key order, and changing the model, effort, or thinking settings mid-run.

## Why

The budget should measure the work the agent did, not the cost of re-reading its own history. Cost stays visible even though it isn't the cap.

I rejected shrinking result pages to fit a raw budget. Smaller pages split more quotes across page boundaries, which drives verification rejections and retries.

## Consequences

If a cache miss happens on iteration 2 or later, it gets logged as a warning. That almost always means one of the banned invalidators slipped in.
