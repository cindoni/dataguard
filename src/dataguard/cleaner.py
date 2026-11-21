"""Conservative and transparent dataset cleaning operations."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class CleaningOptions:
    trim_whitespace: bool = True
    blank_as_missing: bool = True
    drop_duplicates: bool = True
    drop_empty_rows: bool = True


def clean_dataframe(
    dataframe: pd.DataFrame,
    options: CleaningOptions | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Apply safe cleaning steps and return the result plus an audit log."""

    options = options or CleaningOptions()
    cleaned = dataframe.copy()
    audit: list[str] = []
    text_columns = cleaned.select_dtypes(include=["object", "string"]).columns

    if options.trim_whitespace:
        changed = 0
        for column in text_columns:
            original = cleaned[column].copy()
            cleaned[column] = cleaned[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            changed += int((original.fillna("") != cleaned[column].fillna("")).sum())
        audit.append(f"Trimmed whitespace in {changed} cell(s)")

    if options.blank_as_missing:
        blank_count = 0
        for column in text_columns:
            blanks = cleaned[column].map(
                lambda value: isinstance(value, str) and not value.strip()
            )
            blank_count += int(blanks.sum())
            cleaned.loc[blanks, column] = pd.NA
        audit.append(f"Converted {blank_count} blank cell(s) to missing values")

    if options.drop_empty_rows:
        before = len(cleaned)
        cleaned = cleaned.dropna(how="all")
        audit.append(f"Removed {before - len(cleaned)} fully empty row(s)")

    if options.drop_duplicates:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        audit.append(f"Removed {before - len(cleaned)} duplicate row(s)")

    return cleaned.reset_index(drop=True), audit

