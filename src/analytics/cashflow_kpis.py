"""
Day 11 - Cash Flow KPIs & Capital Allocation

Implements:
- Free Cash Flow
- CFO Quality Score
- CapEx Intensity
- FCF Conversion Rate
- Capital Allocation Pattern Classification
"""


from typing import Optional


def free_cash_flow(
    operating_activity: Optional[float],
    investing_activity: Optional[float],
) -> Optional[float]:
    """
    Free Cash Flow = Operating Activity + Investing Activity.

    Negative FCF is allowed.
    """

    if operating_activity is None or investing_activity is None:
        return None

    return operating_activity + investing_activity


def cfo_quality_score(
    cfo: Optional[float],
    pat: Optional[float],
) -> Optional[float]:
    """
    CFO Quality Score = CFO / PAT.

    Returns None when PAT is zero or unavailable.
    """

    if cfo is None or pat is None or pat == 0:
        return None

    return cfo / pat


def cfo_quality_label(
    score: Optional[float],
) -> Optional[str]:
    """
    Classify CFO quality.

    > 1.0       = High Quality
    0.5 - 1.0   = Moderate
    < 0.5       = Accrual Risk
    """

    if score is None:
        return None

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_intensity(
    investing_activity: Optional[float],
    sales: Optional[float],
) -> Optional[float]:
    """
    CapEx Intensity = abs(Investing Activity) / Sales * 100.

    Negative investing activity is converted to an absolute value.
    """

    if investing_activity is None or sales is None or sales == 0:
        return None

    return abs(investing_activity) / sales * 100


def capex_intensity_label(
    intensity: Optional[float],
) -> Optional[str]:
    """
    Classify CapEx intensity.

    < 3%       = Asset Light
    3% - 8%     = Moderate
    > 8%        = Capital Intensive
    """

    if intensity is None:
        return None

    if intensity < 3:
        return "Asset Light"

    if intensity <= 8:
        return "Moderate"

    return "Capital Intensive"


def fcf_conversion_rate(
    fcf: Optional[float],
    operating_profit: Optional[float],
) -> Optional[float]:
    """
    FCF Conversion Rate = FCF / Operating Profit * 100.

    Returns None when operating profit is zero or unavailable.
    """

    if (
        fcf is None
        or operating_profit is None
        or operating_profit == 0
    ):
        return None

    return fcf / operating_profit * 100


def capital_allocation_pattern(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_pat_ratio: Optional[float] = None,
) -> Optional[str]:
    """
    Classify capital allocation using the signs of CFO, CFI and CFF.

    Patterns:

    (+,-,-) = Reinvestor
    (+,-,-) with high CFO/PAT = Shareholder Returns
    (+,+,-) = Liquidating Assets
    (-,+,+) = Distress Signal
    (-,-,+) = Growth Funded by Debt
    (+,+,+) = Cash Accumulator
    (-,-,-) = Pre-Revenue
    (+,-,+) = Mixed
    """

    if cfo is None or cfi is None or cff is None:
        return None

    cfo_sign = "+" if cfo > 0 else "-"
    cfi_sign = "+" if cfi > 0 else "-"
    cff_sign = "+" if cff > 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return "Shareholder Returns"
        return "Reinvestor"

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    if pattern == ("+", "-", "+"):
        return "Mixed"

    return None


def sign(value: Optional[float]) -> Optional[str]:
    """
    Return the sign used by the capital allocation output.

    Positive = +
    Zero/negative = -
    """

    if value is None:
        return None

    return "+" if value > 0 else "-"
# ============================================================
# DAY 31 - CASH FLOW INTELLIGENCE
# ============================================================

import sqlite3
import os
import pandas as pd
import numpy as np


DB_PATH = "nifty100.db"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_year(year):
    """Convert year text into a sortable numeric year."""
    if year is None:
        return None

    year = str(year).strip()

    if year.upper() == "TTM":
        return None

    # Extract the first 4-digit year
    import re
    match = re.search(r"(19|20)\d{2}", year)

    if match:
        return int(match.group())

    return None


def prepare_data(df):
    """
    Prepare financial data:
    - remove TTM rows
    - create numeric year
    - remove duplicate company/year rows
    - sort chronologically
    """

    df = df.copy()

    df["year_num"] = df["year"].apply(clean_year)

    # Remove TTM / rows without a valid year
    df = df[df["year_num"].notna()].copy()

    # Sort so the latest row can be selected consistently
    df = df.sort_values(
        ["company_id", "year_num", "id"]
    )

    # Keep the last record when duplicate company/year rows exist.
    df = df.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="last"
    )

    return df


def calculate_fcf_cagr(fcf_values):
    """
    Calculate 5-year FCF CAGR.

    Requires positive beginning and ending FCF.
    """

    if len(fcf_values) < 6:
        return None

    start = fcf_values.iloc[0]
    end = fcf_values.iloc[-1]

    if pd.isna(start) or pd.isna(end):
        return None

    if start <= 0 or end <= 0:
        return None

    return ((end / start) ** (1 / 5) - 1) * 100


def main():

    print("=" * 50)
    print("DAY 31 - CASH FLOW INTELLIGENCE")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name,
            broad_sector
        FROM companies
        ORDER BY id
        """,
        conn
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            id,
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        """,
        conn
    )

    pnl = pd.read_sql_query(
        """
        SELECT
            id,
            company_id,
            year,
            sales,
            operating_profit,
            depreciation,
            net_profit
        FROM profitandloss
        """,
        conn
    )

    balance = pd.read_sql_query(
        """
        SELECT
            id,
            company_id,
            year,
            borrowings
        FROM balancesheet
        """,
        conn
    )

    conn.close()

    # --------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------

    cashflow = prepare_data(cashflow)
    pnl = prepare_data(pnl)
    balance = prepare_data(balance)

    print(f"Companies found : {len(companies)}")
    print(f"Cashflow rows   : {len(cashflow)}")
    print(f"P&L rows        : {len(pnl)}")
    print(f"BS rows         : {len(balance)}")

    results = []
    distress_rows = []

    # --------------------------------------------------------
    # Process every company
    # --------------------------------------------------------

    for _, company in companies.iterrows():

        company_id = company["company_id"]
        sector = company["broad_sector"]

        cf = cashflow[
            cashflow["company_id"] == company_id
        ].copy()

        pl = pnl[
            pnl["company_id"] == company_id
        ].copy()

        bs = balance[
            balance["company_id"] == company_id
        ].copy()

        if cf.empty:
            results.append({
                "company_id": company_id,
                "sector": sector,
                "cfo_quality_score": None,
                "cfo_quality_label": None,
                "capex_intensity_pct": None,
                "capex_label": None,
                "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None,
                "distress_flag": False,
                "deleveraging_flag": False,
                "capital_allocation_label": None,
            })
            continue

        # ----------------------------------------------------
        # Merge Cash Flow + P&L
        # ----------------------------------------------------

        merged = cf.merge(
            pl[
                [
                    "company_id",
                    "year_num",
                    "sales",
                    "operating_profit",
                    "depreciation",
                    "net_profit",
                ]
            ],
            on=["company_id", "year_num"],
            how="left"
        )

        # ----------------------------------------------------
        # Latest annual row
        # ----------------------------------------------------

        latest = merged.sort_values(
            "year_num"
        ).iloc[-1]

        cfo_latest = latest["operating_activity"]
        cfi_latest = latest["investing_activity"]
        cff_latest = latest["financing_activity"]

        pat_latest = latest["net_profit"]
        sales_latest = latest["sales"]
        op_profit_latest = latest["operating_profit"]

        # ----------------------------------------------------
        # CFO Quality - 5 year average
        # ----------------------------------------------------

        merged["cfo_pat_ratio"] = np.where(
            merged["net_profit"].notna()
            & (merged["net_profit"] != 0),
            merged["operating_activity"]
            / merged["net_profit"],
            np.nan
        )

        recent_5 = merged.sort_values(
            "year_num"
        ).tail(5)

        valid_cfo_ratios = recent_5[
            "cfo_pat_ratio"
        ].dropna()

        if len(valid_cfo_ratios) > 0:
            cfo_score = valid_cfo_ratios.mean()
        else:
            cfo_score = None

        cfo_label = cfo_quality_label(cfo_score)

        # ----------------------------------------------------
        # CapEx Intensity
        # ----------------------------------------------------

        capex_pct = capex_intensity(
            cfi_latest,
            sales_latest
        )

        capex_label = capex_intensity_label(
            capex_pct
        )

        # ----------------------------------------------------
        # FCF
        # ----------------------------------------------------

        merged["fcf"] = (
            merged["operating_activity"]
            + merged["investing_activity"]
        )

        recent_6 = merged.sort_values(
            "year_num"
        ).tail(6)

        fcf_cagr = calculate_fcf_cagr(
            recent_6["fcf"].reset_index(drop=True)
        )

        # ----------------------------------------------------
        # FCF Conversion
        # ----------------------------------------------------

        latest_fcf = latest["operating_activity"] + latest[
            "investing_activity"
        ]

        fcf_conversion = fcf_conversion_rate(
            latest_fcf,
            op_profit_latest
        )

        # ----------------------------------------------------
        # Distress Flag
        # CFO < 0 AND CFF > 0
        # ----------------------------------------------------

        distress_flag = (
            pd.notna(cfo_latest)
            and pd.notna(cff_latest)
            and cfo_latest < 0
            and cff_latest > 0
        )

        if distress_flag:
            distress_rows.append({
                "company_id": company_id,
                "year": latest["year"],
                "cfo": cfo_latest,
                "cff": cff_latest,
                "latest_net_profit": pat_latest,
            })

        # ----------------------------------------------------
        # Deleveraging Flag
        # Latest CFF < 0 AND borrowings declining YoY
        # ----------------------------------------------------

        deleveraging_flag = False

        if not bs.empty and len(bs) >= 2:

            bs_sorted = bs.sort_values(
                "year_num"
            )

            latest_bs = bs_sorted.iloc[-1]
            previous_bs = bs_sorted.iloc[-2]

            latest_borrowings = latest_bs["borrowings"]
            previous_borrowings = previous_bs["borrowings"]

            if (
                pd.notna(cff_latest)
                and cff_latest < 0
                and pd.notna(latest_borrowings)
                and pd.notna(previous_borrowings)
                and latest_borrowings < previous_borrowings
            ):
                deleveraging_flag = True

        # ----------------------------------------------------
        # Capital Allocation Pattern
        # ----------------------------------------------------

        capital_label = capital_allocation_pattern(
            cfo_latest,
            cfi_latest,
            cff_latest,
            cfo_score
        )

        results.append({
            "company_id": company_id,
            "sector": sector,
            "cfo_quality_score": cfo_score,
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": capex_pct,
            "capex_label": capex_label,
            "fcf_cagr_5yr": fcf_cagr,
            "fcf_conversion_pct": fcf_conversion,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": capital_label,
        })

    # --------------------------------------------------------
    # Create output
    # --------------------------------------------------------

    result_df = pd.DataFrame(results)

    required_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    result_df = result_df[required_columns]

    output_file = os.path.join(
        OUTPUT_DIR,
        "cashflow_intelligence.xlsx"
    )

    result_df.to_excel(
        output_file,
        index=False
    )

    # --------------------------------------------------------
    # Distress alerts
    # --------------------------------------------------------

    distress_df = pd.DataFrame(
        distress_rows,
        columns=[
            "company_id",
            "year",
            "cfo",
            "cff",
            "latest_net_profit",
        ]
    )

    distress_file = os.path.join(
        OUTPUT_DIR,
        "distress_alerts.csv"
    )

    distress_df.to_csv(
        distress_file,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("Companies processed :", len(result_df))
    print(
        "Distress flags      :",
        int(result_df["distress_flag"].sum())
    )
    print(
        "Deleveraging flags  :",
        int(result_df["deleveraging_flag"].sum())
    )
    print()
    print("CFO Quality:")
    print(
        result_df["cfo_quality_label"]
        .value_counts(dropna=False)
    )

    print()
    print("CapEx Intensity:")
    print(
        result_df["capex_label"]
        .value_counts(dropna=False)
    )

    print()
    print("Capital Allocation:")
    print(
        result_df["capital_allocation_label"]
        .value_counts(dropna=False)
    )

    print()
    print("Output :", os.path.abspath(output_file))
    print("Output :", os.path.abspath(distress_file))
    print("=" * 50)


if __name__ == "__main__":
    main()