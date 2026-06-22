import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def make_mock_ohlcv(n: int = 60, close_position: float = 0.8) -> pd.DataFrame:
    """
    close_position: 0.0 = close at low (MFM = -1), 1.0 = close at high (MFM = +1)
    """
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    highs = np.ones(n) * 101.0
    lows = np.ones(n) * 99.0
    closes = lows + (highs - lows) * close_position
    return pd.DataFrame(
        {"High": highs, "Low": lows, "Close": closes, "Volume": np.ones(n) * 1_000_000},
        index=dates,
    )


def test_compute_cmf_positive_when_close_near_high():
    from tools.capital_flows import compute_cmf
    df = make_mock_ohlcv(close_position=0.9)
    cmf = compute_cmf(df, window=5)
    assert cmf.dropna().iloc[-1] > 0


def test_compute_cmf_negative_when_close_near_low():
    from tools.capital_flows import compute_cmf
    df = make_mock_ohlcv(close_position=0.1)
    cmf = compute_cmf(df, window=5)
    assert cmf.dropna().iloc[-1] < 0


def test_compute_cmf_range():
    from tools.capital_flows import compute_cmf
    df = make_mock_ohlcv(close_position=0.5)
    cmf = compute_cmf(df, window=5)
    valid = cmf.dropna()
    assert (valid >= -1.0).all() and (valid <= 1.0).all()


def test_build_signal_stack_shape():
    from tools.capital_flows import compute_cmf, build_signal_stack
    raw = {"XLF": make_mock_ohlcv(60), "XLK": make_mock_ohlcv(60)}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    assert ("XLF", 5) in wide.columns
    assert ("XLK", 30) in wide.columns
    assert wide.shape[1] == 6  # 2 tickers × 3 windows


# ── positioning ──────────────────────────────────────────────────────────────

def test_derive_positioning_over():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(0.10) == "OVER"

def test_derive_positioning_under():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(-0.10) == "UNDER"

def test_derive_positioning_neut_positive_edge():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(0.03) == "NEUT"

def test_derive_positioning_neut_negative_edge():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(-0.03) == "NEUT"

def test_derive_positioning_nan():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(float("nan")) == "NEUT"

# ── alignment ─────────────────────────────────────────────────────────────────

def test_derive_alignment_all_over():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("OVER", "OVER", "OVER")
    assert count == 3
    assert arrows == "▲▲▲"

def test_derive_alignment_all_under():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("UNDER", "UNDER", "UNDER")
    assert count == 3
    assert arrows == "▼▼▼"

def test_derive_alignment_mixed():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("OVER", "NEUT", "UNDER")
    assert count == 1
    assert arrows == "▲→▼"

def test_derive_alignment_two_over():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("OVER", "OVER", "NEUT")
    assert count == 2
    assert arrows == "▲▲→"

# ── price return ──────────────────────────────────────────────────────────────

def test_compute_price_return_positive():
    from tools.capital_flows import compute_price_return
    df = make_mock_ohlcv(60, close_position=0.5)
    ret = compute_price_return(df, 15)
    assert isinstance(ret, float)
    assert not np.isnan(ret)
    assert ret == pytest.approx(0.0)

def test_compute_price_return_insufficient_data():
    from tools.capital_flows import compute_price_return
    df = make_mock_ohlcv(10, close_position=0.5)
    ret = compute_price_return(df, 15)
    assert np.isnan(ret)

# ── divergence ────────────────────────────────────────────────────────────────

def test_derive_divergence_distribution():
    from tools.capital_flows import derive_divergence
    # CMF negative, price up = distribution
    assert derive_divergence(-0.15, 0.03) == "[DIV↓]"

def test_derive_divergence_accumulation():
    from tools.capital_flows import derive_divergence
    # CMF positive, price down = accumulation
    assert derive_divergence(0.15, -0.03) == "[DIV↑]"

def test_derive_divergence_none_when_aligned():
    from tools.capital_flows import derive_divergence
    assert derive_divergence(0.15, 0.03) == ""
    assert derive_divergence(-0.15, -0.03) == ""

def test_derive_divergence_none_below_threshold():
    from tools.capital_flows import derive_divergence
    # CMF too small to trigger
    assert derive_divergence(-0.02, 0.03) == ""

# ── position call ─────────────────────────────────────────────────────────────

def test_position_call_all_over():
    from tools.capital_flows import make_position_call
    assert make_position_call("OVER", "OVER", "OVER") == "OVERWEIGHT  2W–90D"

def test_position_call_all_under():
    from tools.capital_flows import make_position_call
    assert make_position_call("UNDER", "UNDER", "UNDER") == "UNDERWEIGHT  2W–90D"

def test_position_call_medium_long_over():
    from tools.capital_flows import make_position_call
    assert make_position_call("NEUT", "OVER", "OVER") == "OVERWEIGHT  30D–90D"

def test_position_call_short_medium_over():
    from tools.capital_flows import make_position_call
    assert make_position_call("OVER", "OVER", "NEUT") == "OVERWEIGHT  2W–30D"

def test_position_call_medium_long_under():
    from tools.capital_flows import make_position_call
    assert make_position_call("NEUT", "UNDER", "UNDER") == "UNDERWEIGHT  30D–90D"

def test_position_call_short_medium_under():
    from tools.capital_flows import make_position_call
    assert make_position_call("UNDER", "UNDER", "NEUT") == "UNDERWEIGHT  2W–30D"

def test_position_call_split_over():
    from tools.capital_flows import make_position_call
    # 5D=OVER, 15D=NEUT, 30D=OVER — non-consecutive, ambiguous
    assert make_position_call("OVER", "NEUT", "OVER") == "HOLD / WATCH"

def test_position_call_mixed():
    from tools.capital_flows import make_position_call
    assert make_position_call("OVER", "NEUT", "UNDER") == "HOLD / WATCH"


def test_derive_snapshot_columns_and_sort():
    from tools.capital_flows import build_signal_stack, derive_snapshot
    raw = {
        "XLF": make_mock_ohlcv(60, close_position=0.9),  # strong positive CMF
        "XLE": make_mock_ohlcv(60, close_position=0.1),  # strong negative CMF
    }
    tickers = {"XLF": "Financials", "XLE": "Energy"}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    snap = derive_snapshot(wide, raw, tickers)

    expected_cols = {
        "ticker", "label", "cmf5", "cmf15", "cmf30",
        "pos5", "pos15", "pos30", "align_count", "align_arrows",
        "price_return_15d", "div_flag", "position_call",
    }
    assert expected_cols.issubset(set(snap.columns))
    # XLF (positive flow) should rank above XLE (negative flow)
    assert snap.iloc[0]["ticker"] == "XLF"
    assert snap.iloc[1]["ticker"] == "XLE"
