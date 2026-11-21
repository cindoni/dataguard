"""Streamlit dashboard for DataGuard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from dataguard.analyzer import analyze_dataframe
from dataguard.cleaner import CleaningOptions, clean_dataframe
from dataguard.io import read_dataset, to_csv_bytes
from dataguard.models import ColumnRule

st.set_page_config(page_title="DataGuard", page_icon="🛡️", layout="wide")


@st.cache_data(show_spinner=False)
def load_upload(contents: bytes, filename: str) -> pd.DataFrame:
    return read_dataset(contents, filename)


def score_color(score: float) -> str:
    if score >= 90:
        return "green"
    if score >= 70:
        return "orange"
    return "red"


st.title("🛡️ DataGuard")
st.caption("Find, explain, and safely clean data-quality problems before they reach production.")

with st.sidebar:
    st.header("Dataset")
    uploaded = st.file_uploader("Upload CSV or JSON", type=["csv", "json"])
    use_sample = st.button("Load sample dataset", use_container_width=True)

if use_sample:
    st.session_state["sample_enabled"] = True
if uploaded is not None:
    st.session_state["sample_enabled"] = False

try:
    if uploaded is not None:
        frame = load_upload(uploaded.getvalue(), uploaded.name)
        source_name = uploaded.name
    elif st.session_state.get("sample_enabled"):
        sample_path = Path(__file__).parent / "data" / "sample_customers.csv"
        frame = pd.read_csv(sample_path)
        source_name = sample_path.name
    else:
        st.info("Upload a CSV or JSON file, or load the included sample to begin.")
        st.stop()
except (ValueError, TypeError, pd.errors.ParserError) as error:
    st.error(f"Could not read this dataset: {error}")
    st.stop()

with st.sidebar:
    st.divider()
    st.header("Validation rule")
    rule_column = st.selectbox("Column", list(frame.columns))
    expected_type = st.selectbox(
        "Expected type",
        ["none", "text", "number", "integer", "email", "date", "boolean"],
    )
    required = st.checkbox("Required (no missing values)")
    unique = st.checkbox("Values must be unique")

rules = []
if expected_type != "none" or required or unique:
    rules.append(
        ColumnRule(
            column=str(rule_column),
            expected_type=None if expected_type == "none" else expected_type,
            required=required,
            unique=unique,
        )
    )

report = analyze_dataframe(frame, rules)

st.subheader(source_name)
score_column, rows_column, columns_column, issues_column = st.columns(4)
score_column.metric("Quality score", f"{report.quality_score:.1f}/100")
rows_column.metric("Rows", f"{report.row_count:,}")
columns_column.metric("Columns", report.column_count)
issues_column.metric("Issues", len(report.issues))
quality_label = score_color(report.quality_score)
st.progress(report.quality_score / 100, text=f"Overall quality: {quality_label}")

overview_tab, issues_tab, clean_tab, data_tab = st.tabs(
    ["Overview", "Issues", "Clean & export", "Data preview"]
)

with overview_tab:
    left, right = st.columns(2)
    score_frame = pd.DataFrame(
        {
            "Dimension": ["Completeness", "Uniqueness", "Validity"],
            "Score": [
                report.completeness_score,
                report.uniqueness_score,
                report.validity_score,
            ],
        }
    ).set_index("Dimension")
    left.bar_chart(score_frame, horizontal=True, x_label="Score (0–100)")
    summary = pd.DataFrame(
        {
            "Check": ["Missing cells", "Duplicate rows", "Invalid cells"],
            "Count": [report.missing_cells, report.duplicate_rows, report.invalid_cells],
        }
    )
    right.dataframe(summary, hide_index=True, use_container_width=True)

with issues_tab:
    if report.issues:
        issue_frame = pd.DataFrame([issue.to_dict() for issue in report.issues])
        st.dataframe(
            issue_frame[["severity", "category", "column", "count", "percentage", "message"]],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.success("No issues found with the active checks.")

with clean_tab:
    st.write("Cleaning is conservative and never modifies the uploaded source file.")
    trim = st.checkbox("Trim surrounding whitespace", value=True)
    blanks = st.checkbox("Treat blank strings as missing", value=True)
    empty_rows = st.checkbox("Remove fully empty rows", value=True)
    duplicates = st.checkbox("Remove exact duplicate rows", value=True)
    cleaned, audit = clean_dataframe(
        frame,
        CleaningOptions(
            trim_whitespace=trim,
            blank_as_missing=blanks,
            drop_empty_rows=empty_rows,
            drop_duplicates=duplicates,
        ),
    )
    cleaned_report = analyze_dataframe(cleaned, rules)
    before, after = st.columns(2)
    before.metric("Before", f"{report.quality_score:.1f}")
    after.metric(
        "After",
        f"{cleaned_report.quality_score:.1f}",
        delta=round(cleaned_report.quality_score - report.quality_score, 1),
    )
    with st.expander("Cleaning audit log"):
        for entry in audit:
            st.write(f"- {entry}")
    st.download_button(
        "Download cleaned CSV",
        data=to_csv_bytes(cleaned),
        file_name=f"cleaned_{Path(source_name).stem}.csv",
        mime="text/csv",
        type="primary",
    )

with data_tab:
    st.dataframe(frame.head(500), use_container_width=True)
    if len(frame) > 500:
        st.caption("Showing the first 500 rows.")

