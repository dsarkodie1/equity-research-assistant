# 003. A finding counts only if code verifies it

2026-10-18 · Accepted

## Context

The model reports when it has found evidence for a plan item. A model that reports success is indistinguishable from one that made it up unless something outside the model checks.

## Decision

A document finding counts as found only if both checks pass:

1. The cited fetch exists in this run's fetch log. The model cites a code-minted attempt id, so the accession number is derived by code, not typed by the model.
2. The quoted snippet appears verbatim in the text that fetch returned.

If either check fails, the item stays open. Model self-report alone never counts.

Verbatim matching normalizes only what HTML-to-text extraction varies on: whitespace, Unicode quotes and dashes, HTML entities, soft hyphens, and non-breaking spaces. No case folding and no fuzzy matching. Minimum quote length is 30 characters, configurable, so a fragment like "revenue" can't pass.

Every rejected finding is logged with the attempted quote and the nearest match in the fetched text. The model is told only that the quote wasn't verbatim and which attempt and page to re-read.

## Why

The log lets me tell extractor bugs from model errors. The nearest match is withheld from the model because showing it the real text creates a copy-the-answer path: the copied text passes verification without necessarily supporting the claim.

## Consequences

More rejections and retries than a lenient check, which costs iterations. That is the intended trade.
