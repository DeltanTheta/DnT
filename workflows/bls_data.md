# Workflow: BLS Employment Data Ingestion

## Objective

Pull labor market time-series directly from the Bureau of Labor Statistics public API v2 and save as CSV for downstream analysis or charting.

## Prerequisites

- `pandas`, `requests`, `python-dotenv` installed
- No API key required for basic use (10 series/request, 10-year chunks auto-handled)
- Optional: `BLS_API_KEY` in `.env` for extended access (50 series/request, 20-year chunks)
  - Register free at https://www.bls.gov/developers/

## Tool

`tools/bls_fetch.py`

## Inputs

| Parameter | Required | Description |
| --- | --- | --- |
| `--series` | No | One or more BLS series IDs (overrides `--preset`) |
| `--preset` | No | Named group: `dashboard` (default), `sectors`, `wages` |
| `--start` | No | Start year (default: 2000) |
| `--end` | No | End year (default: 2025) |
| `--out` | No | Output CSV path (default: `.tmp/bls_<preset>_<start>_<end>.csv`) |
| `--list-series` | No | Print all known series IDs by preset group and exit |

## Execution

```bash
# Default employment dashboard (unemployment, payrolls, earnings, participation)
python tools/bls_fetch.py

# NFP sector breakdown — who is adding / losing jobs
python tools/bls_fetch.py --preset sectors --out .tmp/bls_sectors.csv

# Wage growth series
python tools/bls_fetch.py --preset wages --out .tmp/bls_wages.csv

# Custom series
python tools/bls_fetch.py --series LNS14000000 LNS13327709 CES0000000001 --start 2005 --end 2025

# Discover all known series IDs
python tools/bls_fetch.py --list-series
```

## Expected Output

A CSV file with:
- Row index: date (first of month, monthly frequency)
- Columns: one per series, named with readable labels
- Monthly data only — annual/quarterly rows are filtered out

Example (dashboard preset):
```
date,Unemployment Rate (U-3, SA),U-6 Unemployment (Broad, SA),...
2024-01-01,3.7,7.2,...
2024-02-01,3.9,7.3,...
```

## Key BLS Series Reference

### Unemployment
| Series ID | Description |
| --- | --- |
| LNS14000000 | Unemployment Rate (U-3, headline, SA) |
| LNS13327709 | U-6 Unemployment (broadest measure, SA) |
| LNS14000006 | Unemployment Rate, Men 20+ (SA) |
| LNS14000009 | Unemployment Rate, Women 20+ (SA) |

### Payrolls (Establishment Survey)
| Series ID | Description |
| --- | --- |
| CES0000000001 | Total Nonfarm Payrolls (thousands, SA) |
| CES2000000001 | Construction |
| CES3000000001 | Manufacturing |
| CES4142000001 | Trade, Transport & Utilities |
| CES5500000001 | Financial Activities |
| CES6000000001 | Professional & Business Services |
| CES6500000001 | Education & Health Services |
| CES7000000001 | Leisure & Hospitality |
| CES9091000001 | Federal Government |

### Wages & Hours
| Series ID | Description |
| --- | --- |
| CES0500000003 | Avg Hourly Earnings, All Private (SA) |
| CES0500000002 | Avg Weekly Hours, All Private (SA) |
| CES0500000011 | Avg Overtime Hours, Manufacturing (SA) |

### Participation
| Series ID | Description |
| --- | --- |
| LNS11300000 | Labor Force Participation Rate (SA) |
| LNS12300000 | Employment-Population Ratio (SA) |

## Notes and Constraints

- **Rate limits**: Without a key, the API is permissive but undocumented. The tool adds a 0.5s delay between chunked requests as courtesy.
- **Year chunking**: Without a key, requests are chunked into 10-year windows automatically. With a key, 20-year windows.
- **Data lag**: BLS releases the Employment Situation report on the first Friday of each month for the prior month. The API reflects the latest published data including any revisions.
- **Revisions**: NFP is heavily revised — the first release can differ from the third revision by 50–100k+ jobs. For backtesting signals, note that the data available at time-of-trade differs from what the API returns today.
- **Series IDs**: BLS series IDs are 20 characters. Browse at https://www.bls.gov/data/ or use `--list-series`.

## Common Errors

| Error | Cause | Fix |
| --- | --- | --- |
| `BLS API error: invalid key` | Placeholder key in `.env` | Remove `BLS_API_KEY` or replace with real key |
| Empty DataFrame | Series ID typo or bad year range | Verify series ID at bls.gov/data |
| `REQUEST_NOT_PROCESSED` | Too many series without a key | Reduce batch to 10 or register for a free key |

## Next Steps After Fetching

- Visualize: `tools/chart_macro.py` — pass the CSV path
- Combine with FRED: merge on date index for yield curve + labor dashboard
- Sector analysis: `--preset sectors` shows which industries are driving NFP
