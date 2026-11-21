import pandas as pd

from dataguard.analyzer import analyze_dataframe
from dataguard.models import ColumnRule


def test_clean_data_scores_one_hundred():
    frame = pd.DataFrame({"id": [1, 2], "email": ["a@b.com", "c@d.com"]})

    report = analyze_dataframe(
        frame,
        [ColumnRule("id", expected_type="integer", unique=True)],
    )

    assert report.quality_score == 100.0
    assert report.issues == ()


def test_analysis_finds_missing_duplicates_and_invalid_values():
    frame = pd.DataFrame(
        {
            "id": [1, 1, 3, 3],
            "email": ["ok@example.com", None, "bad", "bad"],
        }
    )

    report = analyze_dataframe(frame, [ColumnRule("email", expected_type="email", required=True)])

    assert report.missing_cells == 1
    assert report.duplicate_rows == 1
    assert report.invalid_cells == 3
    assert {issue.category for issue in report.issues} == {"missing", "duplicate", "invalid"}
    assert 0 <= report.quality_score < 100


def test_missing_schema_column_is_reported():
    report = analyze_dataframe(
        pd.DataFrame({"id": [1, 2]}),
        [ColumnRule("email", expected_type="email")],
    )

    assert report.invalid_cells == 2
    assert report.issues[0].category == "schema"


def test_empty_dataframe_is_valid_and_does_not_divide_by_zero():
    report = analyze_dataframe(pd.DataFrame())

    assert report.quality_score == 100.0
    assert report.row_count == 0

