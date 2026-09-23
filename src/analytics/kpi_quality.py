"""
Day 14 - KPI Quality & Validation

Validates financial ratio data stored in financial_ratios.

Checks:
- Missing KPI values
- Extreme profitability ratios
- Extreme leverage
- Weak interest coverage
- Invalid asset turnover
- CAGR flags
- Overall data-quality summary
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")


KPI_COLUMNS = [
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


def count_rows(conn):
    """Return total financial ratio rows."""

    return conn.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]


def missing_kpi_counts(conn):
    """Return NULL counts for every KPI."""

    result = {}

    for column in KPI_COLUMNS:
        result[column] = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM financial_ratios
            WHERE {column} IS NULL
            """
        ).fetchone()[0]

    return result


def extreme_profitability(conn):
    """
    Identify extreme profitability values.

    NPM/OPM/ROE outside +/-100% are flagged.
    """

    return conn.execute(
        """
        SELECT company_id, year,
               net_profit_margin_pct,
               operating_profit_margin_pct,
               return_on_equity_pct
        FROM financial_ratios
        WHERE
            ABS(net_profit_margin_pct) > 100
            OR ABS(operating_profit_margin_pct) > 100
            OR ABS(return_on_equity_pct) > 100
        ORDER BY company_id, year
        """
    ).fetchall()


def high_leverage(conn):
    """Identify non-Financial companies with D/E above 5."""

    return conn.execute(
        """
        SELECT f.company_id,
               f.year,
               f.debt_to_equity
        FROM financial_ratios f
        LEFT JOIN companies c
            ON f.company_id = c.id
        WHERE f.debt_to_equity > 5
        ORDER BY f.debt_to_equity DESC
        """
    ).fetchall()


def weak_interest_coverage(conn):
    """Identify companies with ICR below 1.5."""

    return conn.execute(
        """
        SELECT company_id,
               year,
               interest_coverage
        FROM financial_ratios
        WHERE interest_coverage IS NOT NULL
          AND interest_coverage < 1.5
        ORDER BY interest_coverage
        """
    ).fetchall()


def invalid_asset_turnover(conn):
    """Identify negative asset turnover values."""

    return conn.execute(
        """
        SELECT company_id,
               year,
               asset_turnover
        FROM financial_ratios
        WHERE asset_turnover IS NOT NULL
          AND asset_turnover < 0
        ORDER BY company_id, year
        """
    ).fetchall()


def cagr_flags(conn):
    """Return rows where CAGR calculations have a flag."""

    return conn.execute(
        """
        SELECT company_id,
               year,
               revenue_cagr_5yr_flag,
               pat_cagr_5yr_flag,
               eps_cagr_5yr_flag
        FROM financial_ratios
        WHERE revenue_cagr_5yr_flag IS NOT NULL
           OR pat_cagr_5yr_flag IS NOT NULL
           OR eps_cagr_5yr_flag IS NOT NULL
        ORDER BY company_id, year
        """
    ).fetchall()


def run_validation():
    """Run all KPI quality checks."""

    conn = sqlite3.connect(DB_PATH)

    try:
        total_rows = count_rows(conn)

        missing = missing_kpi_counts(conn)
        profitability = extreme_profitability(conn)
        leverage = high_leverage(conn)
        weak_icr = weak_interest_coverage(conn)
        invalid_turnover = invalid_asset_turnover(conn)
        flags = cagr_flags(conn)

        print("=" * 70)
        print("DAY 14 - KPI QUALITY & VALIDATION")
        print("=" * 70)

        print(f"Financial ratio rows: {total_rows}")

        if total_rows >= 1100:
            print("Row-count validation: PASS")
        else:
            print("Row-count validation: FAIL")

        print("\nNULL KPI COUNTS")
        print("-" * 70)

        for column, count in missing.items():
            populated = total_rows - count

            print(
                f"{column}: "
                f"{populated}/{total_rows} populated "
                f"({count} NULL)"
            )

        print("\nEXTREME PROFITABILITY")
        print("-" * 70)
        print("Anomalies:", len(profitability))

        print("\nHIGH LEVERAGE")
        print("-" * 70)
        print("Rows with D/E > 5:", len(leverage))

        print("\nWEAK INTEREST COVERAGE")
        print("-" * 70)
        print("Rows with ICR < 1.5:", len(weak_icr))

        print("\nINVALID ASSET TURNOVER")
        print("-" * 70)
        print("Negative values:", len(invalid_turnover))

        print("\nCAGR FLAGS")
        print("-" * 70)
        print("Rows with CAGR flags:", len(flags))

        print("\nVALIDATION SUMMARY")
        print("-" * 70)

        print(
            "Overall:",
            "PASS"
            if total_rows >= 1100
            else "FAIL"
        )

        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    run_validation()