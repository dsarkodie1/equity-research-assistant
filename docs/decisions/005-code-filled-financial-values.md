# 005. The model never types a financial value

2026-10-18 · Accepted

## Context

Financial figures come from XBRL company facts. If the model transcribes a value into its finding, a $4.21B can become $4.12B, and nothing downstream would notice.

## Decision

The model cites a fact by a code-minted handle (for example `F17`) returned by a fact lookup it made this run. Code copies the value, period, unit, and accession from the fetched fact into the citation.

The citation also carries the XBRL tag and its human-readable label, and both are surfaced in the memo.

## Why

Code-filled values remove transcription error, but not selection error: the model can still pick the wrong tag. Putting the tag and label in front of a reviewer makes a wrong-tag pick catchable.

## Consequences

Values are stored as `Decimal` and are only ever written by code.
