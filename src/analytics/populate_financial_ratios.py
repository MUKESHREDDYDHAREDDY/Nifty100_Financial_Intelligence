"""
Day 12 - Populate financial_ratios table

Calculates and stores:
- Net Profit Margin
- Operating Profit Margin
- ROE
- D/E
- Interest Coverage
- Asset Turnover
- Free Cash Flow
- CapEx
- EPS
- Book Value Per Share
- Dividend Payout
- Total Debt
- CFO
- 5-Year Revenue CAGR
- 5-Year PAT CAGR
- 5-Year EPS CAGR
- Composite Quality Score
"""

import sqlite3
from pathlib import Path

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
)

from src.analytics.cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr,
)


DB_PATH = Path("nifty100.db")


def add_columns(conn):
    """Add missing Day 12 columns if they do not already exist."""

    existing = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(financial_ratios)"
        ).fetchall()
    }

    columns = {
        "revenue_cagr_5yr": "REAL",
        "revenue_cagr_5yr_flag": "TEXT",
        "pat_cagr_5yr": "REAL",
        "pat_cagr_5yr_flag": "TEXT",
        "eps_cagr_5yr": "REAL",
        "eps_cagr_5yr_flag": "TEXT",
        "composite_quality_score": "REAL",
    }

    for column, datatype in columns.items():
        if column not in existing:
            conn.execute(
                f"ALTER TABLE financial_ratios "
                f"ADD COLUMN {column} {datatype}"
            )

    conn.commit()


def get_years(conn, company_id):
    """Return available historical P&L years for a company.

    TTM is excluded from CAGR calculations because it is not
    a comparable full historical year.
    """

    rows = conn.execute(
        """
        SELECT year
        FROM profitandloss
        WHERE company_id = ?
          AND year != 'TTM'
        ORDER BY id
        """,
        (company_id,),
    ).fetchall()

    return [row[0] for row in rows]


def get_pnl(conn, company_id, year):
    return conn.execute(
        """
        SELECT
            sales,
            operating_profit,
            opm_percentage,
            other_income,
            interest,
            net_profit,
            eps,
            dividend_payout
        FROM profitandloss
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (company_id, year),
    ).fetchone()


def get_bs(conn, company_id, year):
    return conn.execute(
        """
        SELECT
            equity_capital,
            reserves,
            borrowings,
            investments,
            total_assets
        FROM balancesheet
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (company_id, year),
    ).fetchone()


def get_cf(conn, company_id, year):
    return conn.execute(
        """
        SELECT
            operating_activity,
            investing_activity
        FROM cashflow
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (company_id, year),
    ).fetchone()


def calculate_composite_score(
    npm,
    roe,
    de,
    icr,
    asset_turnover_value,
):
    """
    Simple quality score from available ratio signals.

    This is an internal screening score, not an investment rating.
    """

    score = 0.0
    count = 0

    if npm is not None:
        score += max(min(npm, 30), -30)
        count += 1

    if roe is not None:
        score += max(min(roe, 30), -30)
        count += 1

    if de is not None:
        # Lower leverage is better.
        score += max(0, 10 - (de * 2))
        count += 1

    if icr is not None:
        score += max(min(icr, 10), 0)
        count += 1

    if asset_turnover_value is not None:
        score += max(min(asset_turnover_value * 10, 10), 0)
        count += 1

    if count == 0:
        return None

    return round(score / count, 2)


def calculate_cagr(conn, company_id, years, value_column):
    """
    Calculate 5-year CAGR using the CAGR engine.

    Uses the latest available year and the value approximately
    five years earlier.
    """

    if len(years) < 6:
        return None, "INSUFFICIENT"

    end_year = years[-1]
    start_year = years[-6]

    end_row = conn.execute(
        f"""
        SELECT {value_column}
        FROM profitandloss
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (company_id, end_year),
    ).fetchone()

    start_row = conn.execute(
        f"""
        SELECT {value_column}
        FROM profitandloss
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (company_id, start_year),
    ).fetchone()

    if not end_row or not start_row:
        return None, "INSUFFICIENT"

    start = start_row[0]
    end = end_row[0]

    if start is None or end is None:
        return None, "INSUFFICIENT"

    if start == 0:
        return None, "ZERO_BASE"

    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    if start < 0 and end >= 0:
        return None, "TURNAROUND"

    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"

    try:
        value = ((end / start) ** (1 / 5) - 1) * 100
        return round(value, 4), None
    except (ValueError, ZeroDivisionError):
        return None, "INSUFFICIENT"


def populate():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        add_columns(conn)

        companies = conn.execute(
            "SELECT id FROM companies ORDER BY id"
        ).fetchall()

        inserted = 0
        updated = 0

        for (company_id,) in companies:

            years = get_years(conn, company_id)

            for year in years:

                pnl = get_pnl(conn, company_id, year)
                bs = get_bs(conn, company_id, year)
                cf = get_cf(conn, company_id, year)

                if not pnl:
                    continue

                (
                    sales,
                    operating_profit,
                    source_opm,
                    other_income,
                    interest,
                    net_profit,
                    eps,
                    dividend_payout,
                ) = pnl

                if bs:
                    (
                        equity_capital,
                        reserves,
                        borrowings,
                        investments,
                        total_assets,
                    ) = bs
                else:
                    equity_capital = None
                    reserves = None
                    borrowings = None
                    investments = None
                    total_assets = None

                if cf:
                    operating_activity, investing_activity = cf
                else:
                    operating_activity = None
                    investing_activity = None

                npm = net_profit_margin(net_profit, sales)

                opm = operating_profit_margin(
                    operating_profit,
                    sales,
                )

                roe = return_on_equity(
                    net_profit,
                    equity_capital,
                    reserves,
                )

                de = debt_to_equity(
                    borrowings or 0,
                    equity_capital or 0,
                    reserves or 0,
                )

                icr = interest_coverage_ratio(
                    operating_profit or 0,
                    other_income or 0,
                    interest or 0,
                )

                turnover = asset_turnover(
                    sales,
                    total_assets,
                )

                if operating_activity is not None and investing_activity is not None:
                    fcf = free_cash_flow(
                        operating_activity,
                        investing_activity,
                    )
                else:
                    fcf = None

                capex = (
                    abs(investing_activity)
                    if investing_activity is not None
                    else None
                )

                total_debt = borrowings

                cfo = operating_activity

                revenue_cagr_value, revenue_flag = calculate_cagr(
                    conn,
                    company_id,
                    years,
                    "sales",
                )

                pat_cagr_value, pat_flag = calculate_cagr(
                    conn,
                    company_id,
                    years,
                    "net_profit",
                )

                eps_cagr_value, eps_flag = calculate_cagr(
                    conn,
                    company_id,
                    years,
                    "eps",
                )

                composite_score = calculate_composite_score(
                    npm,
                    roe,
                    de,
                    icr,
                    turnover,
                )

                existing = conn.execute(
                    """
                    SELECT id
                    FROM financial_ratios
                    WHERE company_id = ?
                      AND year = ?
                    LIMIT 1
                    """,
                    (company_id, year),
                ).fetchone()

                values = (
                    npm,
                    opm,
                    roe,
                    de,
                    icr,
                    turnover,
                    fcf,
                    capex,
                    eps,
                    (
                        (equity_capital + reserves)
                        if equity_capital is not None
                        and reserves is not None
                        else None
                    ),
                    dividend_payout,
                    total_debt,
                    cfo,
                    revenue_cagr_value,
                    revenue_flag,
                    pat_cagr_value,
                    pat_flag,
                    eps_cagr_value,
                    eps_flag,
                    composite_score,
                )

                if existing:
                    conn.execute(
                        """
                        UPDATE financial_ratios
                        SET
                            net_profit_margin_pct = ?,
                            operating_profit_margin_pct = ?,
                            return_on_equity_pct = ?,
                            debt_to_equity = ?,
                            interest_coverage = ?,
                            asset_turnover = ?,
                            free_cash_flow_cr = ?,
                            capex_cr = ?,
                            earnings_per_share = ?,
                            book_value_per_share = ?,
                            dividend_payout_ratio_pct = ?,
                            total_debt_cr = ?,
                            cash_from_operations_cr = ?,
                            revenue_cagr_5yr = ?,
                            revenue_cagr_5yr_flag = ?,
                            pat_cagr_5yr = ?,
                            pat_cagr_5yr_flag = ?,
                            eps_cagr_5yr = ?,
                            eps_cagr_5yr_flag = ?,
                            composite_quality_score = ?
                        WHERE company_id = ?
                          AND year = ?
                        """,
                        values + (company_id, year),
                    )

                    updated += 1

                else:
                    conn.execute(
                        """
                        INSERT INTO financial_ratios (
                            company_id,
                            year,
                            net_profit_margin_pct,
                            operating_profit_margin_pct,
                            return_on_equity_pct,
                            debt_to_equity,
                            interest_coverage,
                            asset_turnover,
                            free_cash_flow_cr,
                            capex_cr,
                            earnings_per_share,
                            book_value_per_share,
                            dividend_payout_ratio_pct,
                            total_debt_cr,
                            cash_from_operations_cr,
                            revenue_cagr_5yr,
                            revenue_cagr_5yr_flag,
                            pat_cagr_5yr,
                            pat_cagr_5yr_flag,
                            eps_cagr_5yr,
                            eps_cagr_5yr_flag,
                            composite_quality_score
                        )
                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (company_id, year) + values,
                    )

                    inserted += 1

        conn.commit()

        print("=" * 60)
        print("DAY 12 - FINANCIAL RATIOS POPULATION")
        print("=" * 60)
        print("Companies processed:", len(companies))
        print("Rows inserted:", inserted)
        print("Rows updated:", updated)

        count = conn.execute(
            "SELECT COUNT(*) FROM financial_ratios"
        ).fetchone()[0]

        print("Financial ratios rows:", count)

        print("\nColumn NULL CHECK")

        columns = [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "total_debt_cr",
            "cash_from_operations_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "composite_quality_score",
        ]

        for column in columns:
            total = conn.execute(
                f"SELECT COUNT(*) FROM financial_ratios"
            ).fetchone()[0]

            nulls = conn.execute(
                f"""
                SELECT COUNT(*)
                FROM financial_ratios
                WHERE {column} IS NULL
                """
            ).fetchone()[0]

            print(
                f"{column}: "
                f"{total - nulls}/{total} populated"
            )

        print("=" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    populate()