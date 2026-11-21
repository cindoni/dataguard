import io

import pytest

from dataguard.io import read_dataset, to_csv_bytes


def test_read_csv_and_round_trip_export():
    frame = read_dataset(b"name,value\nAda,1\n", "data.csv")

    assert frame.to_dict(orient="records") == [{"name": "Ada", "value": 1}]
    assert to_csv_bytes(frame) == b"name,value\nAda,1\n"


def test_read_json():
    frame = read_dataset(io.BytesIO(b'[{"name":"Ada"}]'), "data.json")

    assert frame.loc[0, "name"] == "Ada"


def test_unsupported_file_type_has_clear_error():
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_dataset(b"hello", "data.txt")

