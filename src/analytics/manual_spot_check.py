import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")

# Three companies used for the Sprint 2 manual spot-check
COMPANIES = ["TCS", "RELIANCE", "INFY"]


def get_latest_annual_year(conn, company_id):
    """Return the latest annual year, excluding TTM."""

    row = conn.execute(
        """
        SELECT year
        FROM profitandloss
        WHERE company_id = ?
          AND year != 'TTM'
        ORDER BY CAST(substr(year, 5) AS INTEGER) DESC
        LIMIT 1
        """,
        (company_id,),
    ).fetchone()

    return row[0] if row else None


def calculate_manual_roe(conn, company_id, year):
    """
    ROE = Net Profit /
          (Equity Capital + Reserves) * 100

    Return None when equity is <= 0.
    """

    row = conn.execute(
        """
        SELECT
            pl.net_profit,
            bs.equity_capital,
            bs.reserves
        FROM profitandloss pl
        JOIN balancesheet bs
          ON pl.company_id = bs.company_id
         AND pl.year = bs.year
        WHERE pl.company_id = ?
          AND pl.year = ?
        """,
        (company_id, year),
    ).fetchone()

    if row is None:
        return None

    net_profit, equity_capital, reserves = row

    if (
        net_profit is None
        or equity_capital is None
        or reserves is None
    ):
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def calculate_manual_revenue_cagr(conn, company_id, end_year):
    """
    5-Year Revenue CAGR:

    CAGR = ((End / Start) ^ (1 / 5) - 1) * 100
    """

    try:
        end_year_number = int(end_year.replace("Mar ", ""))
    except (ValueError, AttributeError):
        return None

    start_year = f"Mar {end_year_number - 5}"

    end_row = conn.execute(
        """
        SELECT sales
        FROM profitandloss
        WHERE company_id = ?
          AND year = ?
        """,
        (company_id, end_year),
    ).fetchone()

    start_row = conn.execute(
        """
        SELECT sales
        FROM profitandloss
        WHERE company_id = ?
          AND year = ?
        """,
        (company_id, start_year),
    ).fetchone()

    if end_row is None or start_row is None:
        return None

    end_sales = end_row[0]
    start_sales = start_row[0]

    if end_sales is None or start_sales is None:
        return None

    # CAGR is not valid for zero/negative starting revenue
    if start_sales <= 0 or end_sales <= 0:
        return None

    return ((end_sales / start_sales) ** (1 / 5) - 1) * 100


def get_database_values(conn, company_id, year):
    """Get the values stored in financial_ratios."""

    return conn.execute(
        """
        SELECT
            return_on_equity_pct,
            revenue_cagr_5yr
        FROM financial_ratios
        WHERE company_id = ?
          AND year = ?
        """,
        (company_id, year),
    ).fetchone()


def check_value(label, manual_value, database_value):
    """
    Compare manual calculation with database value.

    Requirement:
    Difference must be <= 0.1 percentage points.
    """

    print(f"\n{label}")

    if manual_value is None:
        print("Manual:   None")
        print(f"Database: {database_value}")
        print("CHECK:    SKIPPED - insufficient/invalid source data")
        return True

    if database_value is None:
        print(f"Manual:   {manual_value:.6f}")
        print("Database: None")
        print("CHECK:    FAIL - database value is NULL")
        return False

    difference = abs(manual_value - database_value)

    print(f"Manual:      {manual_value:.6f}")
    print(f"Database:    {database_value:.6f}")
    print(f"Difference:  {difference:.6f}")

    if difference <= 0.1:
        print("CHECK:       PASS")
        return True

    print("CHECK:       FAIL")
    return False


def main():

    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)

    all_pass = True
    checked_companies = 0

    print("=" * 70)
    print("SPRINT 2 MANUAL SPOT-CHECK")
    print("ROE + 5-YEAR REVENUE CAGR")
    print("=" * 70)

    try:

        for company_id in COMPANIES:

            print("\n" + "-" * 70)
            print(f"COMPANY: {company_id}")

            year = get_latest_annual_year(
                conn,
                company_id,
            )

            if year is None:
                print("No annual financial year found.")
                all_pass = False
                continue

            print(f"Year: {year}")

            database_values = get_database_values(
                conn,
                company_id,
                year,
            )

            if database_values is None:
                print("No financial_ratios row found.")
                all_pass = False
                continue

            checked_companies += 1

            database_roe, database_cagr = database_values

            manual_roe = calculate_manual_roe(
                conn,
                company_id,
                year,
            )

            manual_cagr = calculate_manual_revenue_cagr(
                conn,
                company_id,
                year,
            )

            roe_pass = check_value(
                "ROE",
                manual_roe,
                database_roe,
            )

            cagr_pass = check_value(
                "5-Year Revenue CAGR",
                manual_cagr,
                database_cagr,
            )

            if not roe_pass or not cagr_pass:
                all_pass = False

        print("\n" + "=" * 70)
        print("MANUAL SPOT-CHECK SUMMARY")
        print("=" * 70)

        print(f"Companies checked: {checked_companies}/3")
        print("Required tolerance: <= 0.1 percentage points")

        if checked_companies == 3 and all_pass:
            print("RESULT: PASS")
            print(
                "All 3 companies passed the ROE and "
                "5-year Revenue CAGR checks."
            )
        else:
            print("RESULT: CHECK REQUIRED")

        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()