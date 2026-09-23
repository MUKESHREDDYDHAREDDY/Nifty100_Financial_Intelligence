# Sprint 4 — Streamlit Dashboard + Valuation

## Run dashboard

From the project root:

```powershell
& "C:\Users\dhare\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run src/dashboard/app.py
```

Open `http://localhost:8501`.

## Run valuation

```powershell
& "C:\Users\dhare\AppData\Local\Programs\Python\Python311\python.exe" run_valuation.py
```

Expected outputs:

- `output/valuation_summary.xlsx` — 92 companies
- `output/valuation_flags.csv` — Caution and Discount rows

## Valuation rules

- FCF yield = FCF / market cap × 100
- P/E > sector median × 1.5 → Caution
- P/E < sector median × 0.7 → Discount
- Otherwise → Fair

## Important data note

The dashboard's 11 sector groups are sourced from the project's established `peer_percentiles`/peer-group data. The underlying `companies.broad_sector` field contains Financials and Non-Financials.

## Sprint 4 QA

Test:
1. All 8 pages.
2. At least 10 tickers across different business groups.
3. Partial-data companies.
4. Extreme screener filters.
5. Screener CSV headers.
6. Valuation workbook row count and required columns.
7. Profile load time.

This bundle is a replacement/upgrade patch. Back up your current Sprint 4 files before copying.
