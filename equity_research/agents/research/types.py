"""Research agent data types: the frozen plan, citations, resolutions, payload.

Authorship convention: fields prefixed `model_` hold text the model wrote.
Every other field is written by code, from data fetched during the run.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from equity_research.core.result import Gap, GapKind, TerminationReason, require_tuples


class EvidenceKind(StrEnum):
    XBRL_FACT = "xbrl_fact"
    DOCUMENT_SECTION = "document_section"


class ResolutionState(StrEnum):
    OPEN = "open"                                   # in-loop only; never in a built payload
    FOUND = "found"
    UNAVAILABLE = "unavailable"
    OPEN_AT_TERMINATION = "open_at_termination"


@dataclass(frozen=True)
class PlanItem:
    id: str             # "P1"
    claim_id: str
    description: str    # "FY23-FY25 gross margin by segment"
    evidence_kind: EvidenceKind


@dataclass(frozen=True)
class Plan:
    items: tuple[PlanItem, ...]

    def __post_init__(self) -> None:
        require_tuples(self, "items")
        if not self.items:
            raise ValueError("plan has no items")
        ids = self.item_ids
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate plan item ids: {ids}")

    @property
    def item_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.items)

    def get(self, item_id: str) -> PlanItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise KeyError(item_id)


@dataclass(frozen=True)
class DocumentCitation:
    attempt_id: str         # the fetch this quote was verified against
    accession_number: str
    form_type: str
    filing_date: date
    section: str
    page: int
    quote: str              # verified verbatim against the fetched text


@dataclass(frozen=True)
class XbrlCitation:
    fact_ref: str           # code-minted handle, e.g. "F17"
    accession_number: str
    form_type: str
    filing_date: date
    tag: str                # e.g. "us-gaap:Revenues"
    label: str              # human-readable; shown in the memo so a wrong-tag pick is visible
    period_start: date | None   # None for point-in-time facts (balance sheet)
    period_end: date
    unit: str
    value: Decimal          # copied by code from the fetched fact; never model-written


type Citation = DocumentCitation | XbrlCitation


@dataclass(frozen=True)
class Resolution:
    """Status of one plan item. Transitions replace the object; they never mutate it."""
    item_id: str
    state: ResolutionState
    citations: tuple[Citation, ...] = ()
    model_note: str | None = None               # relevance (FOUND) or reason (UNAVAILABLE)
    attempt_ids: tuple[str, ...] = ()           # fetch attempts supporting UNAVAILABLE
    absent_form_types: tuple[str, ...] = ()     # forms the Phase 0 index shows absent in the window

    def __post_init__(self) -> None:
        require_tuples(self, "citations", "attempt_ids", "absent_form_types")
        if self.state is ResolutionState.FOUND:
            if not self.citations:
                raise ValueError(f"{self.item_id}: FOUND requires at least one citation")
            if not self.model_note:
                raise ValueError(f"{self.item_id}: FOUND requires a relevance note")
        elif self.state is ResolutionState.UNAVAILABLE:
            if self.citations:
                raise ValueError(f"{self.item_id}: UNAVAILABLE cannot carry citations")
            if not self.model_note:
                raise ValueError(f"{self.item_id}: UNAVAILABLE requires a reason")
            if not (self.attempt_ids or self.absent_form_types):
                raise ValueError(f"{self.item_id}: UNAVAILABLE must cite attempts or absent form types")
        elif self.citations or self.model_note or self.attempt_ids or self.absent_form_types:
            raise ValueError(f"{self.item_id}: {self.state} carries no evidence")

    @property
    def is_resolved(self) -> bool:
        return self.state in (ResolutionState.FOUND, ResolutionState.UNAVAILABLE)


@dataclass(frozen=True)
class FetchedFiling:
    accession_number: str
    form_type: str
    filing_date: date
    sections: tuple[str, ...]   # sections actually pulled this run

    def __post_init__(self) -> None:
        require_tuples(self, "sections")


@dataclass(frozen=True)
class ResearchPayload:
    ticker: str
    cik: str
    company_name: str
    plan: Plan
    resolutions: tuple[Resolution, ...]     # one per plan item, in plan order
    filings_fetched: tuple[FetchedFiling, ...]

    def __post_init__(self) -> None:
        require_tuples(self, "resolutions", "filings_fetched")
        resolved_ids = tuple(r.item_id for r in self.resolutions)
        if resolved_ids != self.plan.item_ids:
            raise ValueError(f"resolutions {resolved_ids} do not match plan items {self.plan.item_ids}")
        if any(r.state is ResolutionState.OPEN for r in self.resolutions):
            raise ValueError("a built payload cannot contain OPEN items")

    def derive_gaps(self, termination_reason: TerminationReason) -> tuple[Gap, ...]:
        """The only source of gaps for this agent; see build_research_result."""
        gaps = []
        for res in self.resolutions:
            subject = self.plan.get(res.item_id).description
            if res.state is ResolutionState.UNAVAILABLE:
                gaps.append(Gap(res.item_id, subject, GapKind.UNAVAILABLE, res.model_note or ""))
            elif res.state is ResolutionState.OPEN_AT_TERMINATION:
                reason = f"not resolved before the run stopped ({termination_reason})"
                gaps.append(Gap(res.item_id, subject, GapKind.UNRESOLVED, reason))
        return tuple(gaps)
