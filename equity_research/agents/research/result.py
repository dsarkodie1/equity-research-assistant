"""Assembles the research agent's AgentResult from end-of-run state.

This is the only place a research AgentResult is constructed, so gaps and
status are always derived here and never written directly.
"""
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime

from equity_research.agents.research.types import (
    FetchedFiling,
    Plan,
    ResearchPayload,
    Resolution,
    ResolutionState,
)
from equity_research.core.result import AgentResult, ErrorRecord, RunStatus, TerminationReason, Usage

AGENT_NAME = "research"


def build_research_result(
    *,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    termination_reason: TerminationReason,
    usage: Usage,
    errors: tuple[ErrorRecord, ...],
    ticker: str,
    cik: str | None,
    company_name: str | None,
    plan: Plan | None,
    resolutions: Mapping[str, Resolution],
    filings_fetched: tuple[FetchedFiling, ...],
) -> AgentResult[ResearchPayload]:
    if plan is None or cik is None or company_name is None:
        # Nothing was researched (ticker unresolved or plan never frozen).
        return AgentResult(
            agent_name=AGENT_NAME, run_id=run_id, status=RunStatus.FAILED,
            termination_reason=termination_reason, started_at=started_at,
            finished_at=finished_at, payload=None, gaps=(), errors=errors, usage=usage,
        )

    closed = []
    for item_id in plan.item_ids:
        res = resolutions[item_id]   # every item is seeded OPEN when the plan freezes; a miss is a bug
        if res.state is ResolutionState.OPEN:
            res = replace(res, state=ResolutionState.OPEN_AT_TERMINATION)
        closed.append(res)

    payload = ResearchPayload(
        ticker=ticker, cik=cik, company_name=company_name, plan=plan,
        resolutions=tuple(closed), filings_fetched=filings_fetched,
    )
    status = RunStatus.COMPLETE if termination_reason is TerminationReason.PLAN_SATISFIED else RunStatus.PARTIAL
    return AgentResult(
        agent_name=AGENT_NAME, run_id=run_id, status=status,
        termination_reason=termination_reason, started_at=started_at,
        finished_at=finished_at, payload=payload,
        gaps=payload.derive_gaps(termination_reason), errors=errors, usage=usage,
    )
