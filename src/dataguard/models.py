"""Domain models used by the analysis and presentation layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

RuleType = Literal["text", "number", "integer", "email", "date", "boolean"]
Severity = Literal["low", "medium", "high"]


@dataclass(frozen=True, slots=True)
class ColumnRule:
    """Optional expectations for one column."""

    column: str
    expected_type: RuleType | None = None
    required: bool = False
    unique: bool = False
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True)
class Issue:
    """A summarized data-quality issue."""

    category: str
    message: str
    count: int
    percentage: float
    severity: Severity
    column: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    """Complete, serializable output of a DataGuard analysis."""

    row_count: int
    column_count: int
    quality_score: float
    completeness_score: float
    uniqueness_score: float
    validity_score: float
    duplicate_rows: int
    missing_cells: int
    invalid_cells: int
    issues: tuple[Issue, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = [issue.to_dict() for issue in self.issues]
        return payload

