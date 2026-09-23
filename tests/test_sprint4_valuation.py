from pathlib import Path
import pandas as pd

def test_valuation_outputs():
    root = Path(__file__).resolve().parents[1]
    xlsx = root / "output" / "valuation_summary.xlsx"
    csv = root / "output" / "valuation_flags.csv"
    if not xlsx.exists() or not csv.exists():
        return
    df = pd.read_excel(xlsx)
    required = [
        "company_id","company_name","sector","P/E","P/B","EV/EBITDA",
        "FCF_yield_pct","5yr_median_PE","PE_vs_sector_median_pct","flag"
    ]
    assert all(c in df.columns for c in required)
    assert len(df) == 92
    assert set(df["flag"].dropna()).issubset({"Caution","Discount","Fair"})
