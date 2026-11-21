"""File parsing and export helpers."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import pandas as pd


def read_dataset(source: bytes | BinaryIO, filename: str) -> pd.DataFrame:
    """Read a CSV or JSON upload, raising a useful error for unsupported files."""

    suffix = Path(filename).suffix.lower()
    buffer = io.BytesIO(source) if isinstance(source, bytes) else source
    if suffix == ".csv":
        return pd.read_csv(buffer)
    if suffix == ".json":
        return pd.read_json(buffer)
    raise ValueError("Unsupported file type. Upload a .csv or .json file.")


def to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8")

