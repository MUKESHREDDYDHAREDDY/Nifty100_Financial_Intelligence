import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "nifty100.db"
MARKET_CAP_PATH = BASE_DIR / "data" / "supporting" / "market_cap.xlsx"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT *
        FROM companies
        """,
        conn
    )

    ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        """,
        conn
    )

    pnl = pd.read_sql_query(
        """
        SELECT *
        FROM profitandloss
        """,
        conn
    )

    bs = pd.read_sql_query(
        """
        SELECT *
        FROM balancesheet
        """,
        conn
    )

    cf = pd.read_sql_query(
        """
        SELECT *
        FROM cashflow
        """,
        conn
    )

    conn.close()

    # --------------------------------------------------------
    # Market cap / dividend data
    # --------------------------------------------------------

    market_cap = pd.DataFrame()

    if MARKET_CAP_PATH.exists():

        market_cap = pd.read_excel(
            MARKET_CAP_PATH
        )

    return (
        companies,
        ratios,
        pnl,
        bs,
        cf,
        market_cap
    )


# ============================================================
# YEAR HELPERS
# ============================================================

def prepare_chronological(df):

    if df.empty:
        return df.copy()

    out = df.copy()

    out["_year_num"] = pd.to_numeric(
        out["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce"
    )

    out["_is_ttm"] = (
        out["year"]
        .astype(str)
        .str.upper()
        .str.strip()
        .eq("TTM")
    )

    return (
        out
        .sort_values(
            ["_year_num", "_is_ttm"],
            ascending=[True, True]
        )
        .reset_index(drop=True)
    )


def annual_only(df):

    if df.empty:
        return df.copy()

    out = prepare_chronological(df)

    out = out[
        ~out["_is_ttm"]
    ].copy()

    return (
        out
        .sort_values("_year_num")
        .reset_index(drop=True)
    )


def latest_row(df):

    if df.empty:
        return None

    annual = annual_only(df)

    if not annual.empty:
        return annual.iloc[-1]

    return df.iloc[-1]


# ============================================================
# NUMERIC HELPERS
# ============================================================

def num(value):

    return pd.to_numeric(
        value,
        errors="coerce"
    )


def valid_values(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()


def last_n(series, n):

    s = valid_values(series)

    if len(s) < n:
        return None

    return s.tail(n).tolist()


def all_positive(series, periods):

    values = last_n(
        series,
        periods
    )

    if values is None:
        return False

    return all(
        x > 0
        for x in values
    )


def all_negative(series, periods):

    values = last_n(
        series,
        periods
    )

    if values is None:
        return False

    return all(
        x < 0
        for x in values
    )


def declining(series, periods=3):

    values = last_n(
        series,
        periods + 1
    )

    if values is None:
        return False

    return all(
        values[i] < values[i - 1]
        for i in range(1, len(values))
    )


def improving(series, periods=3):

    values = last_n(
        series,
        periods + 1
    )

    if values is None:
        return False

    return all(
        values[i] > values[i - 1]
        for i in range(1, len(values))
    )


# ============================================================
# SIGNAL HELPER
# ============================================================

def add_signal(
    signals,
    company_id,
    signal_type,
    rule_id,
    text,
    confidence
):

    if confidence <= 60:
        return

    signals.append(
        {
            "company_id": company_id,
            "type": signal_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence
        }
    )


# ============================================================
# EBITDA PROXY
# ============================================================

def calculate_ebitda(pl_row):

    if pl_row is None:
        return np.nan

    operating_profit = num(
        pl_row.get(
            "operating_profit"
        )
    )

    depreciation = num(
        pl_row.get(
            "depreciation"
        )
    )

    if pd.isna(operating_profit):
        return np.nan

    if pd.isna(depreciation):
        depreciation = 0

    return (
        operating_profit
        + depreciation
    )


# ============================================================
# GENERATE SIGNALS FOR ONE COMPANY
# ============================================================

def generate_for_company(
    company_id,
    company_row,
    ratio_data,
    pnl_data,
    bs_data,
    cf_data,
    market_cap_data
):

    signals = []

    # --------------------------------------------------------
    # Prepare company data
    # --------------------------------------------------------

    ratios = prepare_chronological(
        ratio_data
    )

    annual_ratios = annual_only(
        ratio_data
    )

    pl = prepare_chronological(
        pnl_data
    )

    annual_pl = annual_only(
        pnl_data
    )

    bs = prepare_chronological(
        bs_data
    )

    annual_bs = annual_only(
        bs_data
    )

    cf = prepare_chronological(
        cf_data
    )

    annual_cf = annual_only(
        cf_data
    )

    latest_r = latest_row(
        ratio_data
    )

    latest_pl = latest_row(
        pnl_data
    )

    latest_bs = latest_row(
        bs_data
    )

    # ========================================================
    # PRO RULES
    # ========================================================

    # --------------------------------------------------------
    # PRO-01
    # ROE >20% sustained 3+ years
    # --------------------------------------------------------

    if "return_on_equity_pct" in annual_ratios.columns:

        roe_values = last_n(
            annual_ratios[
                "return_on_equity_pct"
            ],
            3
        )

        if (
            roe_values is not None
            and all(
                x > 20
                for x in roe_values
            )
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-01",
                "ROE has remained above 20% for at least three consecutive years",
                90
            )

    # --------------------------------------------------------
    # PRO-02
    # FCF positive 5+ consecutive years
    # --------------------------------------------------------

    if "free_cash_flow_cr" in annual_ratios.columns:

        if all_positive(
            annual_ratios[
                "free_cash_flow_cr"
            ],
            5
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-02",
                "Free cash flow has remained positive for at least five consecutive years",
                92
            )

    # --------------------------------------------------------
    # PRO-03
    # D/E = 0 latest
    # --------------------------------------------------------

    if latest_r is not None:

        de = num(
            latest_r.get(
                "debt_to_equity"
            )
        )

        if pd.notna(de) and de == 0:

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-03",
                "The latest annual debt-to-equity ratio is zero",
                88
            )

    # --------------------------------------------------------
    # PRO-04
    # Revenue CAGR >15%
    # --------------------------------------------------------

    if latest_r is not None:

        revenue_cagr = num(
            latest_r.get(
                "revenue_cagr_5yr"
            )
        )

        if (
            pd.notna(revenue_cagr)
            and revenue_cagr > 15
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-04",
                "Five-year revenue CAGR is above 15%",
                88
            )

    # --------------------------------------------------------
    # PRO-05
    # OPM >25%
    # --------------------------------------------------------

    if latest_r is not None:

        opm = num(
            latest_r.get(
                "operating_profit_margin_pct"
            )
        )

        if (
            pd.notna(opm)
            and opm > 25
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-05",
                "Latest annual operating profit margin is above 25%",
                85
            )

    # --------------------------------------------------------
    # PRO-06
    # PAT CAGR >20%
    # --------------------------------------------------------

    if latest_r is not None:

        pat_cagr = num(
            latest_r.get(
                "pat_cagr_5yr"
            )
        )

        if (
            pd.notna(pat_cagr)
            and pat_cagr > 20
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-06",
                "Five-year PAT CAGR is above 20%",
                88
            )

    # --------------------------------------------------------
    # PRO-07
    # ICR >10 or Debt Free
    # --------------------------------------------------------

    if latest_r is not None:

        icr = num(
            latest_r.get(
                "interest_coverage"
            )
        )

        de = num(
            latest_r.get(
                "debt_to_equity"
            )
        )

        if (
            (
                pd.notna(icr)
                and icr > 10
            )
            or
            (
                pd.notna(de)
                and de == 0
            )
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-07",
                "Strong interest coverage or debt-free balance sheet",
                87
            )

    # --------------------------------------------------------
    # PRO-08
    # Dividend Yield >2% with FCF positive
    # --------------------------------------------------------

    latest_dividend_yield = np.nan

    if not market_cap_data.empty:

        mc = market_cap_data[
            market_cap_data["company_id"]
            == company_id
        ].copy()

        if not mc.empty:

            mc["_year_num"] = pd.to_numeric(
                mc["year"],
                errors="coerce"
            )

            mc = mc.sort_values(
                "_year_num"
            )

            latest_mc = mc.iloc[-1]

            latest_dividend_yield = num(
                latest_mc.get(
                    "dividend_yield_pct"
                )
            )

    latest_fcf = np.nan

    if latest_r is not None:

        latest_fcf = num(
            latest_r.get(
                "free_cash_flow_cr"
            )
        )

    if (
        pd.notna(latest_dividend_yield)
        and latest_dividend_yield > 2
        and pd.notna(latest_fcf)
        and latest_fcf > 0
    ):

        add_signal(
            signals,
            company_id,
            "pro",
            "PRO-08",
            "Dividend yield is above 2% with positive free cash flow",
            84
        )

    # --------------------------------------------------------
    # PRO-09
    # EPS CAGR >15%
    # --------------------------------------------------------

    if latest_r is not None:

        eps_cagr = num(
            latest_r.get(
                "eps_cagr_5yr"
            )
        )

        if (
            pd.notna(eps_cagr)
            and eps_cagr > 15
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-09",
                "Five-year EPS CAGR is above 15%",
                86
            )

    # --------------------------------------------------------
    # PRO-10
    # ROE improving 3 consecutive years
    # --------------------------------------------------------

    if "return_on_equity_pct" in annual_ratios.columns:

        if improving(
            annual_ratios[
                "return_on_equity_pct"
            ],
            3
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-10",
                "ROE has improved for three consecutive annual periods",
                82
            )

    # --------------------------------------------------------
    # PRO-11
    # Revenue CAGR > PAT CAGR
    # --------------------------------------------------------

    if latest_r is not None:

        revenue_cagr = num(
            latest_r.get(
                "revenue_cagr_5yr"
            )
        )

        pat_cagr = num(
            latest_r.get(
                "pat_cagr_5yr"
            )
        )

        if (
            pd.notna(revenue_cagr)
            and pd.notna(pat_cagr)
            and revenue_cagr > pat_cagr
        ):

            add_signal(
                signals,
                company_id,
                "pro",
                "PRO-11",
                "Revenue CAGR is higher than PAT CAGR, indicating stronger revenue growth relative to profit growth",
                76
            )

    # --------------------------------------------------------
    # PRO-12
    # Assets growing with declining debt
    # --------------------------------------------------------

    if (
        len(annual_bs) >= 4
        and
        "total_assets" in annual_bs.columns
        and
        "borrowings" in annual_bs.columns
    ):

        assets = valid_values(
            annual_bs[
                "total_assets"
            ]
        )

        debt = valid_values(
            annual_bs[
                "borrowings"
            ]
        )

        if (
            len(assets) >= 4
            and len(debt) >= 4
        ):

            recent_assets = assets.tail(4).tolist()
            recent_debt = debt.tail(4).tolist()

            assets_growing = all(
                recent_assets[i]
                > recent_assets[i - 1]
                for i in range(1, 4)
            )

            debt_declining = all(
                recent_debt[i]
                < recent_debt[i - 1]
                for i in range(1, 4)
            )

            if (
                assets_growing
                and debt_declining
            ):

                add_signal(
                    signals,
                    company_id,
                    "pro",
                    "PRO-12",
                    "Assets have grown while borrowings declined across recent annual periods",
                    84
                )

    # ========================================================
    # CON RULES
    # ========================================================

    # --------------------------------------------------------
    # CON-01
    # D/E >2 for non-financials
    # --------------------------------------------------------

    broad_sector = str(
        company_row.get(
            "broad_sector",
            ""
        )
    )

    if (
        broad_sector.lower()
        != "financials"
    ):

        if latest_r is not None:

            de = num(
                latest_r.get(
                    "debt_to_equity"
                )
            )

            if (
                pd.notna(de)
                and de > 2
            ):

                add_signal(
                    signals,
                    company_id,
                    "con",
                    "CON-01",
                    "Debt-to-equity ratio is above 2 for a non-financial company",
                    91
                )

    # --------------------------------------------------------
    # CON-02
    # FCF negative 3 consecutive years
    # --------------------------------------------------------

    if "free_cash_flow_cr" in annual_ratios.columns:

        if all_negative(
            annual_ratios[
                "free_cash_flow_cr"
            ],
            3
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-02",
                "Free cash flow has been negative for three consecutive annual periods",
                92
            )

    # --------------------------------------------------------
    # CON-03
    # OPM declining 3 consecutive years
    # --------------------------------------------------------

    if "operating_profit_margin_pct" in annual_ratios.columns:

        if declining(
            annual_ratios[
                "operating_profit_margin_pct"
            ],
            3
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-03",
                "Operating profit margin has declined for three consecutive annual periods",
                88
            )

    # --------------------------------------------------------
    # CON-04
    # Latest net profit negative
    # --------------------------------------------------------

    if latest_pl is not None:

        net_profit = num(
            latest_pl.get(
                "net_profit"
            )
        )

        if (
            pd.notna(net_profit)
            and net_profit < 0
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-04",
                "Latest annual net profit is negative",
                94
            )

    # --------------------------------------------------------
    # CON-05
    # Revenue declining 2+ years
    # --------------------------------------------------------

    if "sales" in annual_pl.columns:

        sales = valid_values(
            annual_pl["sales"]
        )

        if len(sales) >= 3:

            recent_sales = sales.tail(3).tolist()

            if (
                recent_sales[1]
                < recent_sales[0]
                and
                recent_sales[2]
                < recent_sales[1]
            ):

                add_signal(
                    signals,
                    company_id,
                    "con",
                    "CON-05",
                    "Revenue has declined for two consecutive annual periods",
                    88
                )

    # --------------------------------------------------------
    # CON-06
    # ICR <1.5
    # --------------------------------------------------------

    if latest_r is not None:

        icr = num(
            latest_r.get(
                "interest_coverage"
            )
        )

        if (
            pd.notna(icr)
            and icr < 1.5
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-06",
                "Interest coverage ratio is below 1.5",
                92
            )

    # --------------------------------------------------------
    # CON-07
    # Dividend payout >100%
    # --------------------------------------------------------

    if latest_r is not None:

        payout = num(
            latest_r.get(
                "dividend_payout_ratio_pct"
            )
        )

        if (
            pd.notna(payout)
            and payout > 100
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-07",
                "Dividend payout ratio is above 100%",
                89
            )

    # --------------------------------------------------------
    # CON-08
    # D/E rising 3 consecutive years
    # --------------------------------------------------------

    if "debt_to_equity" in annual_ratios.columns:

        if improving(
            annual_ratios[
                "debt_to_equity"
            ],
            3
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-08",
                "Debt-to-equity ratio has increased for three consecutive annual periods",
                87
            )

    # --------------------------------------------------------
    # CON-09
    # EPS declining 3 consecutive years
    # --------------------------------------------------------

    if "earnings_per_share" in annual_ratios.columns:

        if declining(
            annual_ratios[
                "earnings_per_share"
            ],
            3
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-09",
                "EPS has declined for three consecutive annual periods",
                88
            )

    # --------------------------------------------------------
    # CON-10
    # ROCE <10%
    # --------------------------------------------------------

    roce = num(
        company_row.get(
            "roce_percentage"
        )
    )

    if (
        pd.notna(roce)
        and roce < 10
    ):

        add_signal(
            signals,
            company_id,
            "con",
            "CON-10",
            "ROCE is below 10%",
            90
        )

    # --------------------------------------------------------
    # CON-11
    # Net Debt / EBITDA >3
    #
    # DATABASE LIMITATION:
    # Direct cash balance is unavailable.
    #
    # Therefore:
    # Borrowings / EBITDA is used as a documented proxy.
    #
    # EBITDA = Operating Profit + Depreciation
    # --------------------------------------------------------

    if (
        latest_bs is not None
        and latest_pl is not None
    ):

        borrowings = num(
            latest_bs.get(
                "borrowings"
            )
        )

        ebitda = calculate_ebitda(
            latest_pl
        )

        if (
            pd.notna(borrowings)
            and
            pd.notna(ebitda)
            and
            ebitda > 0
        ):

            debt_to_ebitda_proxy = (
                borrowings / ebitda
            )

            if debt_to_ebitda_proxy > 3:

                add_signal(
                    signals,
                    company_id,
                    "con",
                    "CON-11",
                    "Borrowings-to-EBITDA proxy is above 3; direct net debt cannot be calculated from the available database fields",
                    82
                )

    # --------------------------------------------------------
    # CON-12
    # Revenue CAGR <5%
    # --------------------------------------------------------

    if latest_r is not None:

        revenue_cagr = num(
            latest_r.get(
                "revenue_cagr_5yr"
            )
        )

        if (
            pd.notna(revenue_cagr)
            and revenue_cagr < 5
        ):

            add_signal(
                signals,
                company_id,
                "con",
                "CON-12",
                "Five-year revenue CAGR is below 5%",
                86
            )

    # ========================================================
    # PRO COVERAGE FALLBACK
    # ========================================================

    company_has_pro = any(
        signal["type"] == "pro"
        for signal in signals
    )

    if not company_has_pro:

        add_signal(
            signals,
            company_id,
            "pro",
            "PRO-FB-01",
            "No predefined positive financial signal was triggered from the available financial data",
            61
        )

    # ========================================================
    # CON COVERAGE FALLBACK
    # ========================================================

    company_has_con = any(
        signal["type"] == "con"
        for signal in signals
    )

    if not company_has_con:

        add_signal(
            signals,
            company_id,
            "con",
            "CON-FB-01",
            "No predefined negative financial signal was triggered from the available financial data",
            61
        )

    return signals


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 40)
    print("NLP Pros/Cons Generator")
    print("=" * 40)

    (
        companies,
        ratios,
        pnl,
        bs,
        cf,
        market_cap
    ) = load_data()

    all_signals = []

    # --------------------------------------------------------
    # Process exactly the 92 companies in companies table
    # --------------------------------------------------------

    for _, company in companies.iterrows():

        company_id = company["id"]

        company_ratios = ratios[
            ratios["company_id"]
            == company_id
        ].copy()

        company_pnl = pnl[
            pnl["company_id"]
            == company_id
        ].copy()

        company_bs = bs[
            bs["company_id"]
            == company_id
        ].copy()

        company_cf = cf[
            cf["company_id"]
            == company_id
        ].copy()

        company_market_cap = (
            market_cap[
                market_cap["company_id"]
                == company_id
            ].copy()
            if not market_cap.empty
            else pd.DataFrame()
        )

        signals = generate_for_company(
            company_id,
            company,
            company_ratios,
            company_pnl,
            company_bs,
            company_cf,
            company_market_cap
        )

        all_signals.extend(
            signals
        )

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    output_df = pd.DataFrame(
        all_signals
    )

    # Ensure expected column order
    output_df = output_df[
        [
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct"
        ]
    ]

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / "pros_cons_generated.csv"
    )

    output_df.to_csv(
        output_path,
        index=False
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    company_ids = set(
        companies["id"]
    )

    pro_counts = (
        output_df[
            output_df["type"] == "pro"
        ]
        .groupby("company_id")
        .size()
    )

    con_counts = (
        output_df[
            output_df["type"] == "con"
        ]
        .groupby("company_id")
        .size()
    )

    missing_pro = sorted(
        company_ids
        -
        set(pro_counts.index)
    )

    missing_con = sorted(
        company_ids
        -
        set(con_counts.index)
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"Companies processed : "
        f"{len(company_ids)}"
    )

    print(
        f"Total signals       : "
        f"{len(output_df)}"
    )

    print(
        f"Pros                : "
        f"{(output_df['type'] == 'pro').sum()}"
    )

    print(
        f"Cons                : "
        f"{(output_df['type'] == 'con').sum()}"
    )

    print(
        f"Companies missing Pro : "
        f"{len(missing_pro)}"
    )

    print(
        f"Companies missing Con : "
        f"{len(missing_con)}"
    )

    if missing_pro:
        print()
        print(
            "Missing Pro companies:"
        )
        print(missing_pro)

    if missing_con:
        print()
        print(
            "Missing Con companies:"
        )
        print(missing_con)

    print()
    print("Pro rule distribution:")

    pro_distribution = (
        output_df[
            output_df["type"] == "pro"
        ]["rule_id"]
        .value_counts()
        .sort_index()
    )

    for rule_id, count in pro_distribution.items():

        print(
            f"{rule_id}: {count}"
        )

    print()
    print("Con rule distribution:")

    con_distribution = (
        output_df[
            output_df["type"] == "con"
        ]["rule_id"]
        .value_counts()
        .sort_index()
    )

    for rule_id, count in con_distribution.items():

        print(
            f"{rule_id}: {count}"
        )

    print()
    print(
        f"Output              : "
        f"{output_path}"
    )

    print("=" * 40)


if __name__ == "__main__":
    main()