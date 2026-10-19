"""Checks the schema-layer guarantees: immutability, state invariants, derived gaps/status."""
import dataclasses
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from equity_research.agents.research.result import build_research_result
from equity_research.agents.research.types import (
    DocumentCitation,
    EvidenceKind,
    Plan,
    PlanItem,
    Resolution,
    ResolutionState,
    XbrlCitation,
)
from equity_research.core.result import GapKind, RunStatus, TerminationReason, TokenUsage, Usage

NOW = datetime(2026, 10, 19, tzinfo=timezone.utc)
USAGE = Usage(tokens=TokenUsage(), model_calls=0, iterations=0, wall_seconds=0.0)


def make_plan() -> Plan:
    return Plan(items=(
        PlanItem("P1", "C1", "FY23-FY25 revenue", EvidenceKind.XBRL_FACT),
        PlanItem("P2", "C1", "Supplier concentration risk", EvidenceKind.DOCUMENT_SECTION),
        PlanItem("P3", "C2", "Segment margin commentary", EvidenceKind.DOCUMENT_SECTION),
    ))


def xbrl_citation() -> XbrlCitation:
    return XbrlCitation(
        fact_ref="F1", accession_number="0000320193-25-000079", form_type="10-K",
        filing_date=date(2025, 10, 31), tag="us-gaap:Revenues", label="Revenues",
        period_start=date(2024, 9, 29), period_end=date(2025, 9, 27), unit="USD",
        value=Decimal("1000"),
    )


def build(resolutions, reason, plan=None):
    return build_research_result(
        run_id="r1", started_at=NOW, finished_at=NOW, termination_reason=reason,
        usage=USAGE, errors=(), ticker="AAPL", cik="0000320193", company_name="Apple Inc.",
        plan=plan or make_plan(), resolutions=resolutions, filings_fetched=(),
    )


# --- immutability ---

def test_plan_items_cannot_be_reassigned():
    plan = make_plan()
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.items = ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.items[0].description = "something easier"


def test_list_instead_of_tuple_is_rejected():
    with pytest.raises(TypeError):
        Plan(items=[PlanItem("P1", "C1", "x", EvidenceKind.XBRL_FACT)])


def test_duplicate_plan_ids_rejected():
    item = PlanItem("P1", "C1", "x", EvidenceKind.XBRL_FACT)
    with pytest.raises(ValueError):
        Plan(items=(item, item))


# --- resolution invariants ---

def test_found_requires_citation_and_note():
    with pytest.raises(ValueError):
        Resolution("P1", ResolutionState.FOUND, model_note="relevant")
    with pytest.raises(ValueError):
        Resolution("P1", ResolutionState.FOUND, citations=(xbrl_citation(),))


def test_unavailable_requires_evidence_of_looking():
    with pytest.raises(ValueError):
        Resolution("P2", ResolutionState.UNAVAILABLE, model_note="not disclosed")
    Resolution("P2", ResolutionState.UNAVAILABLE, model_note="not disclosed", attempt_ids=("A3",))
    Resolution("P2", ResolutionState.UNAVAILABLE, model_note="no DEF 14A", absent_form_types=("DEF 14A",))


def test_open_carries_no_evidence():
    with pytest.raises(ValueError):
        Resolution("P1", ResolutionState.OPEN, attempt_ids=("A1",))


# --- derived status and gaps ---

def test_open_items_become_unresolved_gaps_on_cap():
    resolutions = {
        "P1": Resolution("P1", ResolutionState.FOUND, (xbrl_citation(),), "revenue trend"),
        "P2": Resolution("P2", ResolutionState.UNAVAILABLE, model_note="not disclosed", attempt_ids=("A2",)),
        "P3": Resolution("P3", ResolutionState.OPEN),
    }
    result = build(resolutions, TerminationReason.ITERATION_CAP)

    assert result.status is RunStatus.PARTIAL
    states = {r.item_id: r.state for r in result.payload.resolutions}
    assert states["P3"] is ResolutionState.OPEN_AT_TERMINATION
    assert {(g.ref, g.kind) for g in result.gaps} == {("P2", GapKind.UNAVAILABLE), ("P3", GapKind.UNRESOLVED)}
    assert "iteration_cap" in next(g.reason for g in result.gaps if g.ref == "P3")


def test_all_unavailable_still_counts_as_complete():
    resolutions = {
        pid: Resolution(pid, ResolutionState.UNAVAILABLE, model_note="absent", attempt_ids=("A1",))
        for pid in ("P1", "P2", "P3")
    }
    result = build(resolutions, TerminationReason.PLAN_SATISFIED)
    assert result.status is RunStatus.COMPLETE
    assert all(g.kind is GapKind.UNAVAILABLE for g in result.gaps)


def test_plan_satisfied_with_open_items_is_a_bug():
    resolutions = {pid: Resolution(pid, ResolutionState.OPEN) for pid in ("P1", "P2", "P3")}
    with pytest.raises(ValueError):
        build(resolutions, TerminationReason.PLAN_SATISFIED)


def test_no_plan_means_failed_with_no_payload():
    result = build_research_result(
        run_id="r1", started_at=NOW, finished_at=NOW,
        termination_reason=TerminationReason.TICKER_UNRESOLVED, usage=USAGE, errors=(),
        ticker="ZZZZ", cik=None, company_name=None, plan=None, resolutions={}, filings_fetched=(),
    )
    assert result.status is RunStatus.FAILED
    assert result.payload is None


def test_budget_tokens_exclude_cache_reads():
    t = TokenUsage(input_tokens=100, cache_write_tokens=50, cache_read_tokens=10_000, output_tokens=25)
    assert t.budget_tokens == 175
    assert (t + t).cache_read_tokens == 20_000


def test_document_citation_shape():
    c = DocumentCitation("A1", "0000320193-25-000079", "10-K", date(2025, 10, 31), "Item 1A", 2, "x" * 40)
    assert not hasattr(c, "value")   # document citations carry no numbers
