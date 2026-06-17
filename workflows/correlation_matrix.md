# Workflow: Correlation Matrix

## Objective

Generate a 3-panel correlation heatmap for a configurable set of macro asset proxy
tickers: current 63-day snapshot, 1-week-prior snapshot, and the delta between them.
Used to identify shifting inter-asset relationships across macro regimes.

## When to Run

- Publishing a correlation-focused post
- Monitoring regime changes (run weekly or after major macro events)
- Adding/removing tickers to explore a new factor relationship

## Prerequisites

```sh
pip install seaborn yfinance curl_cffi pandas numpy matplotlib python-dotenv
```

No API keys required — data comes from Yahoo Finance via yfinance (free).

## Execution

**Default run (7 tickers, 63-day window, 1-week prior):**

```sh
python tools/correlation_matrix.py
```

**Custom tickers:**

```sh
python tools/correlation_matrix.py --tickers SPY TLT GLD USO XLE
```

**Custom window (21-day = ~1 month):**

```sh
python tools/correlation_matrix.py --window 21
```

**Custom prior offset (compare to 1 month ago instead of 1 week):**

```sh
python tools/correlation_matrix.py --prior-offset 21
```

**Override display labels:**

```sh
python tools/correlation_matrix.py --labels DX-Y.NYB:DXY IEF:10Y
```

**Save to a specific path:**

```sh
python tools/correlation_matrix.py --out .tmp/corr_custom.png
```

## Default Ticker Set

| Ticker | Yahoo Symbol | Macro Factor |
|--------|-------------|--------------|
| SPY | SPY | US equities (S&P 500) |
| IWM | IWM | Risk appetite / small caps (Russell 2000) |
| QQQ | QQQ | Growth / tech (Nasdaq 100) |
| TLT | TLT | Long-duration rates (20Y+ Treasuries) |
| IEF | IEF | 10Y note proxy (7–10Y Treasuries) |
| GLD | GLD | Gold / real assets / fear |
| DXY | DX-Y.NYB | US dollar strength |

## Adding or Removing Tickers

Pass `--tickers` with the new set. No code changes needed.

```sh
# Add crude oil and remove IWM
python tools/correlation_matrix.py --tickers SPY QQQ TLT IEF GLD DX-Y.NYB USO
```

If a ticker's display name is ugly (e.g. `DX-Y.NYB`), add it to `DEFAULT_LABELS`
in the script or pass `--labels DX-Y.NYB:DXY` at call time.

## How to Interpret the Delta Panel

The delta heatmap (Panel 3) shows `current_corr - prior_corr` for each pair:

- **Green cell (+):** The two assets became more positively correlated this week.
  If SPY/TLT goes green, equities and bonds are moving more together — risk-off
  diversification is weakening.
- **Red cell (-):** Correlation fell. Assets are moving more independently or
  more inversely.
- **Near zero (yellow):** Relationship is stable week-over-week.

The magnitude matters: a delta of ±0.10 is noise; ±0.25+ is worth noting.

## Known Quirks

- **DX-Y.NYB (DXY):** Yahoo Finance's DXY index can have missing sessions
  on days when US markets are open. If it causes errors, substitute `UUP`
  (Invesco USD Bull ETF) which has fewer gaps, or just drop it from `--tickers`.
- **SSL:** `CURL_CA_BUNDLE` and `REQUESTS_CA_BUNDLE` are cleared at import time
  (same workaround as all other tools in this project — required for yfinance on
  some Windows environments).
- **Market holidays:** yfinance returns only trading days, so `--window 63`
  is truly 63 trading days regardless of calendar gaps.

## Output

PNG saved to `.tmp/correlation_matrix_YYYYMMDD.png`.
`.tmp/` is gitignored — regenerate on demand.
