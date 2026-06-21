import io
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def make_mock_df(series=("HY", "IG")):
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    data = {}
    if "HY" in series:
        data["HY"] = np.linspace(3.0, 2.0, 300)
    if "IG" in series:
        data["IG"] = np.linspace(1.5, 0.7, 300)
    if "CCC" in series:
        data["CCC"] = np.linspace(9.0, 7.0, 300)
    return pd.DataFrame(data, index=dates)


def capture_print_summary(df, keys):
    from tools.credit_spreads import print_summary
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        print_summary(df, keys)
    finally:
        sys.stdout = old
    return buf.getvalue()


def test_differential_row_appears_when_hy_and_ig_present():
    df = make_mock_df(("HY", "IG"))
    out = capture_print_summary(df, ["HY", "IG"])
    assert "HY" in out
    assert "Quality Premium" in out


def test_differential_row_absent_when_only_hy():
    df = make_mock_df(("HY",))
    out = capture_print_summary(df, ["HY"])
    assert "Quality Premium" not in out


def test_differential_row_absent_when_only_ig():
    df = make_mock_df(("IG",))
    out = capture_print_summary(df, ["IG"])
    assert "Quality Premium" not in out


def test_differential_value_is_hy_minus_ig():
    df = make_mock_df(("HY", "IG"))
    out = capture_print_summary(df, ["HY", "IG"])
    # Last HY = 2.00, last IG = 0.70, diff = 1.30
    assert "1.30%" in out
