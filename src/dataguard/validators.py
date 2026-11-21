"""Reusable, vectorized column validators."""

from __future__ import annotations

import pandas as pd

from dataguard.models import ColumnRule

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
BOOLEAN_VALUES = {"true", "false", "1", "0", "yes", "no", "y", "n"}


def invalid_mask(series: pd.Series, rule: ColumnRule) -> pd.Series:
    """Return a boolean mask for non-null values that violate ``rule``."""

    populated = series.notna()
    mask = pd.Series(False, index=series.index, dtype=bool)

    if rule.expected_type:
        if rule.expected_type == "text":
            type_invalid = populated & ~series.map(lambda value: isinstance(value, str))
        elif rule.expected_type == "number":
            type_invalid = populated & pd.to_numeric(series, errors="coerce").isna()
        elif rule.expected_type == "integer":
            numeric = pd.to_numeric(series, errors="coerce")
            type_invalid = populated & (numeric.isna() | numeric.mod(1).ne(0))
        elif rule.expected_type == "email":
            type_invalid = populated & ~series.astype(str).str.match(EMAIL_PATTERN, na=False)
        elif rule.expected_type == "date":
            type_invalid = populated & pd.to_datetime(series, errors="coerce").isna()
        else:
            type_invalid = populated & ~series.astype(str).str.lower().isin(BOOLEAN_VALUES)
        mask |= type_invalid

    if rule.minimum is not None or rule.maximum is not None:
        numeric = pd.to_numeric(series, errors="coerce")
        if rule.minimum is not None:
            mask |= populated & numeric.lt(rule.minimum)
        if rule.maximum is not None:
            mask |= populated & numeric.gt(rule.maximum)

    if rule.allowed_values:
        mask |= populated & ~series.isin(rule.allowed_values)

    if rule.unique:
        mask |= populated & series.duplicated(keep=False)

    if rule.required:
        mask |= series.isna()

    return mask

