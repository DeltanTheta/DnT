import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_mock_csv(tmp_path, filename: str, n: int = 60) -> Path:
    """Write a minimal capital_flows CSV to tmp_path and return its path."""
    ALL_TICKERS = [
        "XLE", "XLI", "XLB", "XLY", "XLK",
        "XLP", "XLU", "XLV", "XLRE", "XLC",
        "XLF", "TLT", "GLD",
    ]
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    data = {}
    for t in ALL_TICKERS:
        for w in [5, 15, 30]:
            data[f"{t}_cmf{w}"] = np.random.randn(n) * 0.1
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    csv_path = tmp_path / filename
    df.to_csv(csv_path)
    return csv_path


# ── find_latest_csv ───────────────────────────────────────────────────────────

def test_find_latest_csv_returns_most_recent(tmp_path):
    from tools.flow_trend import find_latest_csv
    make_mock_csv(tmp_path, "capital_flows_20250101.csv")
    make_mock_csv(tmp_path, "capital_flows_20250110.csv")
    result = find_latest_csv(str(tmp_path))
    assert result.endswith("capital_flows_20250110.csv")


def test_find_latest_csv_exits_when_none(tmp_path):
    from tools.flow_trend import find_latest_csv
    with pytest.raises(SystemExit):
        find_latest_csv(str(tmp_path))


# ── load_csv ──────────────────────────────────────────────────────────────────

def test_load_csv_returns_datetime_index(tmp_path):
    from tools.flow_trend import load_csv
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv")
    df = load_csv(str(csv_path))
    assert isinstance(df.index, pd.DatetimeIndex)


def test_load_csv_has_expected_columns(tmp_path):
    from tools.flow_trend import load_csv
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv")
    df = load_csv(str(csv_path))
    assert "XLK_cmf30" in df.columns
    assert "GLD_cmf30" in df.columns


# ── slice_lookback ────────────────────────────────────────────────────────────

def test_slice_lookback_returns_last_n_rows():
    from tools.flow_trend import slice_lookback
    dates = pd.date_range("2025-01-01", periods=100, freq="B")
    df = pd.DataFrame({"XLK_cmf30": np.random.randn(100)}, index=dates)
    result = slice_lookback(df, 30)
    assert len(result) == 30
    assert result.index[-1] == df.index[-1]


def test_slice_lookback_clips_to_available_rows():
    from tools.flow_trend import slice_lookback
    dates = pd.date_range("2025-01-01", periods=10, freq="B")
    df = pd.DataFrame({"XLK_cmf30": np.random.randn(10)}, index=dates)
    result = slice_lookback(df, 60)
    assert len(result) == 10


# ── render_trend_chart ────────────────────────────────────────────────────────

def test_render_trend_chart_creates_file(tmp_path):
    from tools.flow_trend import render_trend_chart
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv", n=60)
    df = pd.read_csv(str(csv_path), index_col=0, parse_dates=True)
    out_path = str(tmp_path / "test_chart.png")
    render_trend_chart(df, as_of="2025-03-31", out_path=out_path)
    assert Path(out_path).exists()
    assert Path(out_path).stat().st_size > 10_000  # non-trivial PNG


def test_render_trend_chart_handles_missing_column(tmp_path):
    """Chart should not crash if a ticker column is absent from the CSV."""
    from tools.flow_trend import render_trend_chart
    dates = pd.date_range("2025-01-01", periods=60, freq="B")
    df = pd.DataFrame({"XLK_cmf30": [0.1] * 60}, index=dates)
    out_path = str(tmp_path / "partial_chart.png")
    render_trend_chart(df, as_of="2025-03-31", out_path=out_path)
    assert Path(out_path).exists()


# ── CLI integration ───────────────────────────────────────────────────────────

def test_cli_runs_end_to_end(tmp_path):
    import subprocess
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv", n=60)
    out_path = str(tmp_path / "out.png")
    result = subprocess.run(
        [sys.executable, "tools/flow_trend.py",
         "--csv", str(csv_path),
         "--out", out_path,
         "--lookback", "30"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Chart saved" in result.stdout
    assert Path(out_path).exists()
