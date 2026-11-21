"""Small command-line interface for automation and CI pipelines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataguard.analyzer import analyze_dataframe
from dataguard.io import read_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a CSV or JSON dataset")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--fail-below", type=float, default=0.0, metavar="SCORE")
    args = parser.parse_args()

    with args.dataset.open("rb") as source:
        frame = read_dataset(source, args.dataset.name)
    report = analyze_dataframe(frame)
    print(json.dumps(report.to_dict(), indent=2))
    if report.quality_score < args.fail_below:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

