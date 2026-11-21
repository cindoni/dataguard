import pandas as pd

from dataguard.cleaner import CleaningOptions, clean_dataframe


def test_default_cleaning_is_conservative_and_audited():
    frame = pd.DataFrame(
        {
            "name": [" Ada ", " Ada ", "   ", None],
            "value": [1, 1, 2, None],
        }
    )

    cleaned, audit = clean_dataframe(frame)

    assert len(cleaned) == 2
    assert cleaned.loc[0, "name"] == "Ada"
    assert pd.isna(cleaned.loc[1, "name"])
    assert any("duplicate" in entry for entry in audit)
    assert len(audit) == 4


def test_cleaning_options_can_disable_all_changes():
    frame = pd.DataFrame({"name": [" A ", " A "]})
    options = CleaningOptions(False, False, False, False)

    cleaned, audit = clean_dataframe(frame, options)

    pd.testing.assert_frame_equal(cleaned, frame)
    assert audit == []

