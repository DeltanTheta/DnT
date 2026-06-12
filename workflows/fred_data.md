# Workflow: FRED Data Ingestion

## Objective

Pull macro time-series data from the St. Louis Federal Reserve's FRED API and save it as a CSV for downstream analysis or charting.

## Prerequisites

- `FRED_API_KEY` set in `.env` (register free at https://fred.stlouisfed.org/docs/api/api_key.html)
- `fredapi`, `pandas`, `python-dotenv` installed

## Tool

`tools/fred_fetch.py`

## Inputs

| Parameter | Required | Description |
| --- | --- | --- |
| `--series` | Yes | One or more FRED series IDs (space-separated) |
| `--start` | No | Start date `YYYY-MM-DD` (default: 2000-01-01) |
| `--end` | No | End date `YYYY-MM-DD` (default: today) |
| `--out` | No | Output CSV path (default: `.tmp/fred_<series>_<date>.csv`) |

## Execution

```bash
# Yield curve — 2Y, 10Y, and the 10Y-2Y spread
python tools/fred_fetch.py --series DGS2 DGS10 T10Y2Y

# Inflation series — CPI, Core CPI, PCE, Core PCE
python tools/fred_fetch.py --series CPIAUCSL CPILFESL PCEPI PCEPILFE --start 1990-01-01

# Full macro dashboard pull
python tools/fred_fetch.py --series DGS2 DGS10 T10Y2Y CPIAUCSL CPILFESL UNRATE M2SL GDP BAMLH0A0HYM2 --out .tmp/macro_dashboard.csv
```

## Expected Output

A CSV file at the specified path with:
- Row index: date (daily or monthly depending on series)
- Columns: one per series ID
- Missing values (`NaN`) where a series has no observation on that date — this is normal for mixed-frequency data

Example output (first few rows):
```
date,DGS2,DGS10,T10Y2Y
2000-01-03,6.27,6.58,0.31
2000-01-04,6.19,6.49,0.30
...
```

## Key FRED Series Reference

### Yield Curve
| Series ID | Description |
| --- | --- |
| DGS1MO | 1-Month Treasury Yield |
| DGS3MO | 3-Month Treasury Yield |
| DGS2 | 2-Year Treasury Yield |
| DGS5 | 5-Year Treasury Yield |
| DGS10 | 10-Year Treasury Yield |
| DGS30 | 30-Year Treasury Yield |
| T10Y2Y | 10Y minus 2Y Spread |
| T10Y3M | 10Y minus 3M Spread |

### Inflation
| Series ID | Description |
| --- | --- |
| CPIAUCSL | CPI All Items (seasonally adjusted) |
| CPILFESL | Core CPI (ex Food & Energy) |
| PCEPI | PCE Price Index |
| PCEPILFE | Core PCE Price Index (Fed's preferred measure) |

### Labor Market
| Series ID | Description |
| --- | --- |
| UNRATE | Unemployment Rate |
| PAYEMS | Nonfarm Payrolls |
| JTSJOL | Job Openings (JOLTS) |

### Money Supply / Credit
| Series ID | Description |
| --- | --- |
| M2SL | M2 Money Supply |
| BAMLH0A0HYM2 | High Yield Credit Spread (OAS) |
| TEDRATE | TED Spread (credit stress indicator) |

### Dollar / Commodities
| Series ID | Description |
| --- | --- |
| DTWEXBGS | Trade-Weighted USD Index (Broad) |
| DCOILWTICO | WTI Crude Oil |
| GOLDAMGBD228NLBM | Gold (London AM Fix) |

## Notes and Constraints

- **Rate limits**: FRED allows 120 API calls per 60 seconds. A single `fred_fetch.py` call with 10 series = 10 API calls — well within limits.
- **Frequency mismatch**: Daily series (yields) and monthly series (CPI) will produce sparse monthly data for daily series — use `.resample('ME').last()` in downstream analysis when you want monthly alignment.
- **Data vintage**: FRED data is subject to revision. The tool always fetches the latest vintage. For backtesting, vintage-aware data sources (e.g., ALFRED) would be needed — document this caveat in any signal research.
- **Series discovery**: Browse or search series at https://fred.stlouisfed.org/. Any public series ID works with this tool.

## Common Errors

| Error | Cause | Fix |
| --- | --- | --- |
| `FRED_API_KEY not set` | Key missing from `.env` | Register and add key |
| `Bad Request` on series | Series ID typo | Double-check ID at fred.stlouisfed.org |
| Empty DataFrame | Bad date range | Verify series history starts before `--start` date |

## Next Steps After Fetching

- Visualize: use `tools/chart_macro.py` (to be built in Post 4)
- Analyze: import the CSV in a Jupyter notebook or pass path to analysis tools
- Share: upload to Google Sheets via `tools/sheets_upload.py` (future)
