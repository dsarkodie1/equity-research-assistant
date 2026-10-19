# 009. Model access goes through an adapter

2026-10-18 · Proposed

## Context

Plan generation depends on structured outputs, and tool safety depends on strict tool schemas. Both are provider-specific, and so is prompt caching. The model choice itself is still open.

## Decision

- The loop never calls a provider directly. A thin adapter owns the provider's message list and returns normalized turns: tool calls, text, stop reason, and usage.
- Strict tools, structured outputs, caching, and thinking-block handling all live behind the adapter.
- Development runs on a smaller Claude model. The final model is chosen by comparing quality and cost against larger models on a few real theses.
- Python 3.12 with the current Anthropic SDK, instead of pinning an older SDK to stay on Python 3.9.

## Why

- **The upgrade:** structured outputs and strict tools are load-bearing. Pinning an old SDK to keep an old Python would put the safety properties on the wrong side of a version constraint.
- **The adapter:** it makes the model comparison a config change, not a refactor.

## Consequences

The adapter is the one place that has to change if a provider's API changes.
