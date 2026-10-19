"""Result envelope shared by every agent.

Every agent returns an AgentResult. The orchestrator branches on `status`
alone; `termination_reason` says why the run ended and `gaps` says what is
missing. Every type here is frozen and uses tuples, never lists, so a result
cannot be changed after it is built.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RunStatus(StrEnum):
    COMPLETE = "complete"   # every plan item resolved
    PARTIAL = "partial"     # stopped with work remaining; payload still usable
    FAILED = "failed"       # no usable payload


class TerminationReason(StrEnum):
    PLAN_SATISFIED = "plan_satisfied"
    # caps
    ITERATION_CAP = "iteration_cap"
    TOKEN_BUDGET = "token_budget"
    WALL_CLOCK = "wall_clock"
    # loop health
    STALLED = "stalled"
    TOOL_FAILURE_STREAK = "tool_failure_streak"
    # model provider
    MODEL_API_ERROR = "model_api_error"
    MODEL_REFUSAL = "model_refusal"
    # before the loop starts
    TICKER_UNRESOLVED = "ticker_unresolved"
    PLAN_GENERATION_FAILED = "plan_generation_failed"


class GapKind(StrEnum):
    UNAVAILABLE = "unavailable"   # the agent looked; the evidence is not in the sources
    UNRESOLVED = "unresolved"     # the run stopped before the agent finished looking


def require_tuples(obj: object, *field_names: str) -> None:
    """Reject list/dict values in sequence fields; a list would make a frozen dataclass mutable."""
    for name in field_names:
        value = getattr(obj, name)
        if not isinstance(value, tuple):
            raise TypeError(f"{type(obj).__name__}.{name} must be a tuple, got {type(value).__name__}")


@dataclass(frozen=True)
class Gap:
    ref: str        # agent-local id of the missing thing, e.g. plan item "P3"
    subject: str    # what is missing, in reader-facing words
    kind: GapKind
    reason: str


@dataclass(frozen=True)
class ErrorRecord:
    source: str     # e.g. "tool:fetch_section", "model", "phase0:ticker"
    message: str
    occurred_at: datetime
    attempt_id: str | None = None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0           # uncached input only
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0          # includes thinking
    estimated_cost_usd: float = 0.0

    @property
    def budget_tokens(self) -> int:
        """Tokens counted against the run's token cap: new work only, cache reads excluded."""
        return self.input_tokens + self.cache_write_tokens + self.output_tokens

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd,
        )


@dataclass(frozen=True)
class Usage:
    tokens: TokenUsage
    model_calls: int
    iterations: int
    wall_seconds: float


@dataclass(frozen=True)
class AgentResult[P]:
    agent_name: str
    run_id: str
    status: RunStatus
    termination_reason: TerminationReason
    started_at: datetime
    finished_at: datetime
    payload: P | None
    gaps: tuple[Gap, ...]
    errors: tuple[ErrorRecord, ...]
    usage: Usage

    def __post_init__(self) -> None:
        require_tuples(self, "gaps", "errors")
        if (self.status is RunStatus.FAILED) != (self.payload is None):
            raise ValueError("payload must be None exactly when status is FAILED")
        if (self.status is RunStatus.COMPLETE) != (self.termination_reason is TerminationReason.PLAN_SATISFIED):
            raise ValueError("status COMPLETE requires termination_reason PLAN_SATISFIED, and vice versa")
        if self.status is RunStatus.COMPLETE and any(g.kind is GapKind.UNRESOLVED for g in self.gaps):
            raise ValueError("a COMPLETE result cannot contain unresolved gaps")
