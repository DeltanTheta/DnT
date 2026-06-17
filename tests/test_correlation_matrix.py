import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.correlation_matrix import compute_log_returns, correlation_window


def make_prices(n=150, tickers=("A", "B", "C"), seed=42):
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n, len(tickers))).cumsum(axis=0) + 100
    idx = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame(data, index=idx, columns=list(tickers))


def test_log_returns_drops_first_row():
    prices = make_prices(100)
    returns = compute_log_returns(prices)
    assert returns.shape == (99, 3)


def test_log_returns_correct_value():
    prices = pd.DataFrame(
        {"A": [100.0, 110.0, 99.0]},
        index=pd.bdate_range("2024-01-01", periods=3),
    )
    returns = compute_log_returns(prices)
    assert len(returns) == 2
    assert abs(returns["A"].iloc[0] - np.log(110.0 / 100.0)) < 1e-10
    assert abs(returns["A"].iloc[1] - np.log(99.0 / 110.0)) < 1e-10


def test_correlation_window_shape_and_diagonal():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    corr = correlation_window(returns, end_offset=0, window=63)
    assert corr.shape == (3, 3)
    for col in corr.columns:
        assert abs(corr.loc[col, col] - 1.0) < 1e-10


def test_correlation_window_current_vs_prior_differ():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    cur = correlation_window(returns, end_offset=0, window=63)
    pri = correlation_window(returns, end_offset=5, window=63)
    assert not cur.equals(pri)


def test_correlation_window_prior_slice_is_correct():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    prior = correlation_window(returns, end_offset=5, window=63)
    expected = returns.iloc[-(63 + 5):-5].corr()
    pd.testing.assert_frame_equal(prior, expected)


def test_correlation_window_current_slice_is_correct():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    current = correlation_window(returns, end_offset=0, window=63)
    expected = returns.iloc[-63:].corr()
    pd.testing.assert_frame_equal(current, expected)
