"""Data-quality analysis and explainable scoring."""

from __future__ import annotations

import pandas as pd

from dataguard.models import AnalysisReport, ColumnRule, Issue, Severity
from dataguard.validators import invalid_mask


def _severity(percentage: float) -> Severity:
    if percentage >= 20:
        return "high"
    if percentage >= 5:
        return "medium"
    return "low"


def _percentage(count: int, total: int) -> float:
    return round((count / total * 100) if total else 0.0, 2)


def analyze_dataframe(
    dataframe: pd.DataFrame,
    rules: list[ColumnRule] | tuple[ColumnRule, ...] | None = None,
) -> AnalysisReport:
    """Profile a dataframe and return scores plus actionable issues.

    The overall score weights completeness at 40%, uniqueness at 25%, and
    rule-based validity at 35%. Scores are deterministic and bounded 0–100.
    """

    frame = dataframe.copy()
    rows, columns = frame.shape
    total_cells = rows * columns
    issues: list[Issue] = []

    missing_cells = int(frame.isna().sum().sum())
    for column, count in frame.isna().sum().items():
        count = int(count)
        if count:
            percentage = _percentage(count, rows)
            issues.append(
                Issue(
                    category="missing",
                    column=str(column),
                    count=count,
                    percentage=percentage,
                    severity=_severity(percentage),
                    message=f"{count} missing value(s) in '{column}'",
                )
            )

    duplicate_rows = int(frame.duplicated().sum())
    if duplicate_rows:
        percentage = _percentage(duplicate_rows, rows)
        issues.append(
            Issue(
                category="duplicate",
                count=duplicate_rows,
                percentage=percentage,
                severity=_severity(percentage),
                message=f"{duplicate_rows} duplicate row(s)",
            )
        )

    invalid_cells = 0
    for rule in rules or ():
        if rule.column not in frame.columns:
            issues.append(
                Issue(
                    category="schema",
                    column=rule.column,
                    count=rows,
                    percentage=100.0 if rows else 0.0,
                    severity="high",
                    message=f"Required schema column '{rule.column}' is absent",
                )
            )
            invalid_cells += rows
            continue

        count = int(invalid_mask(frame[rule.column], rule).sum())
        invalid_cells += count
        if count:
            percentage = _percentage(count, rows)
            issues.append(
                Issue(
                    category="invalid",
                    column=rule.column,
                    count=count,
                    percentage=percentage,
                    severity=_severity(percentage),
                    message=f"{count} value(s) violate rules for '{rule.column}'",
                )
            )

    completeness = 100 * (1 - missing_cells / total_cells) if total_cells else 100.0
    uniqueness = 100 * (1 - duplicate_rows / rows) if rows else 100.0
    validity = 100 * (1 - min(invalid_cells, total_cells) / total_cells) if total_cells else 100.0
    score = 0.40 * completeness + 0.25 * uniqueness + 0.35 * validity

    return AnalysisReport(
        row_count=rows,
        column_count=columns,
        quality_score=round(max(0.0, min(score, 100.0)), 1),
        completeness_score=round(completeness, 1),
        uniqueness_score=round(uniqueness, 1),
        validity_score=round(validity, 1),
        duplicate_rows=duplicate_rows,
        missing_cells=missing_cells,
        invalid_cells=invalid_cells,
        issues=tuple(issues),
    )

