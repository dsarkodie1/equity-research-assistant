# Decision records

One file per decision, written when the decision was made. A record is never edited to change its outcome. A reversed decision gets a new record that supersedes the old one.

| # | Decision | Date | Status |
|---|---|---|---|
| [001](001-scope-and-thesis-shape.md) | Scope v1 to one company; thesis shape | 2026-10-18 | Accepted |
| [002](002-frozen-research-plan.md) | Research plan is frozen after generation | 2026-10-18 | Accepted |
| [003](003-code-verified-findings.md) | A finding counts only if code verifies it | 2026-10-18 | Accepted |
| [004](004-earned-unavailable.md) | "Unavailable" is a valid outcome but must be earned | 2026-10-18 | Accepted |
| [005](005-code-filled-financial-values.md) | The model never types a financial value | 2026-10-18 | Accepted |
| [006](006-termination-and-caps.md) | Termination conditions, caps, and failure handling | 2026-10-18 | Accepted |
| [007](007-token-budget-and-caching.md) | Token budget counts new work; prompt caching | 2026-10-18 | Accepted |
| [008](008-retrieval-scope.md) | What the agent can fetch, and in what size | 2026-10-18 | Proposed |
| [009](009-model-adapter.md) | Model access goes through an adapter | 2026-10-18 | Proposed |
| [010](010-derived-gaps.md) | Gaps are derived from resolutions, never written | 2026-10-18 | Accepted |

Template:

```
# NNN. Title
Date · Status (Proposed | Accepted | Superseded by NNN)
## Context      what forced a decision
## Decision     what was decided, specifically enough to test
## Why          the reasoning at the time
## Consequences what this costs or rules out
```
