# 002. Research plan is frozen after generation

2026-10-18 · Accepted

## Context

The loop needs a checkable definition of "done." Either the plan is derived mechanically from the thesis, or the agent writes it. If the agent writes it, the question is whether it can change it later.

## Decision

The agent generates the plan in its first step. Each item ties to a claim. After generation the plan is frozen: items are immutable, and the loop can change an item's status but never its content. It can never add or remove items.

The research plan is satisfied when every item is either found with a citation or unavailable with a reason. There is no coverage threshold.

## Why

A plan the agent can edit mid-run lets it quietly drop whatever it couldn't find and then declare itself done. A coverage threshold such as 80% has the same problem with extra steps: it decides in advance which gaps are acceptable without knowing which ones they'll be.

## Consequences

A bad plan can't be repaired mid-run. It shows up in the output as a bad plan, which is the right place to catch it. Enforced structurally: `PlanItem` and `Plan` are frozen dataclasses with tuple fields, and resolution status lives in a separate structure keyed by item id.
