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
