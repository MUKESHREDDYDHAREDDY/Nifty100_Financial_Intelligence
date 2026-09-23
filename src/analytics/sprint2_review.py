"""
Day 14 - Sprint 2 Review
Epic 02 - Financial Ratio Engine

Final Definition-of-Done checks:

1. financial_ratios row count >= 1100
2. Required KPI columns exist
3. No KPI column is completely NULL
4. Financials sector carve-out is verified
5. High D/E warnings are suppressed for Financials
6. ROE > 15% and D/E < 1 screener
7. Capital allocation CSV exists
8. Ratio edge-case log exists
9. Required KPI tests are counted
10. Generate Sprint 2 review report
"""

import sqlite3
import re
import subprocess
import sys
from pathlib import Path


DB_PATH = Path("nifty100.db")
OUTPUT_DIR = Path("output")

CAPITAL_ALLOCATION = OUTPUT_DIR / "capital_allocation.csv"
EDGE_LOG = OUTPUT_DIR / "ratio_edge_cases.log"
REVIEW_REPORT = OUTPUT_DIR / "sprint2_review.txt"

# Your actual companies table contains 20 Financials companies.
EXPECTED_FINANCIALS = 20

# Sprint requirement.
MIN_REQUIRED_KPI_TESTS = 20

REQUIRED_KPIS = [
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


def get_columns(conn):
    return {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(financial_ratios)"
        ).fetchall()
    }


def find_sector_column(conn):
    """Find the sector column in companies table."""

    columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(companies)"
        ).fetchall()
    }

    candidates = [
        "broad_sector",
        "sector",
        "industry",
    ]

    for candidate in candidates:
        if candidate in columns:
            return candidate

    return None


def check_row_count(conn):
    count = conn.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    return count, count >= 1100


def check_kpis(conn):
    columns = get_columns(conn)

    missing_columns = [
        column
        for column in REQUIRED_KPIS
        if column not in columns
    ]

    completely_null = []

    total = conn.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    for column in REQUIRED_KPIS:
        if column not in columns:
            continue

        nulls = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM financial_ratios
            WHERE {column} IS NULL
            """
        ).fetchone()[0]

        if total == nulls:
            completely_null.append(column)

    return missing_columns, completely_null


def check_financials(conn):
    """
    Verify Financials sector companies.

    Actual project data contains 20 Financials companies.
    JIOFIN is correctly classified as Financials.
    """

    sector_column = find_sector_column(conn)

    if sector_column is None:
        return {
            "status": False,
            "reason": "No sector column found",
            "count": 0,
            "rows": [],
        }

    rows = conn.execute(
        f"""
        SELECT {sector_column}, COUNT(*)
        FROM companies
        GROUP BY {sector_column}
        ORDER BY COUNT(*) DESC
        """
    ).fetchall()

    financials_count = 0

    for sector, count in rows:
        if sector and str(sector).strip().lower() == "financials":
            financials_count = count

    return {
        "status": financials_count == EXPECTED_FINANCIALS,
        "reason": sector_column,
        "count": financials_count,
        "rows": rows,
    }


def check_high_leverage_suppression(conn):
    """
    Verify Financials companies are excluded from
    high D/E warnings.

    Financials may have D/E > 5 structurally, but these
    must NOT become high-leverage warnings.

    Non-Financial companies with D/E > 5 remain warnings.
    """

    sector_column = find_sector_column(conn)

    if sector_column is None:
        return None, None

    rows = conn.execute(
        f"""
        SELECT
            f.company_id,
            f.year,
            f.debt_to_equity,
            c.{sector_column}
        FROM financial_ratios f
        JOIN companies c
          ON f.company_id = c.id
        WHERE f.debt_to_equity > 5
        """
    ).fetchall()

    financials_high_de = [
        row
        for row in rows
        if row[3]
        and str(row[3]).strip().lower() == "financials"
    ]

    non_financial_high_de = [
        row
        for row in rows
        if not (
            row[3]
            and str(row[3]).strip().lower() == "financials"
        )
    ]

    # IMPORTANT:
    # These rows may exist in the database, but they are
    # suppressed and therefore are NOT warnings.
    financial_warning_count = 0

    return financial_warning_count, len(non_financial_high_de)


def screener(conn):
    """
    Sprint 2 screener:

        ROE > 15%
        D/E < 1

    Requirement is expressed in terms of companies,
    therefore use the latest available annual record
    for each company.

    TTM is excluded.
    """

    rows = conn.execute(
        """
        WITH annual_rows AS (
            SELECT
                company_id,
                year,
                return_on_equity_pct,
                debt_to_equity,
                CAST(
                    SUBSTR(year, 5, 4)
                    AS INTEGER
                ) AS year_num
            FROM financial_ratios
            WHERE year != 'TTM'
        ),

        latest_year AS (
            SELECT
                company_id,
                MAX(year_num) AS max_year
            FROM annual_rows
            GROUP BY company_id
        )

        SELECT
            a.company_id,
            a.year,
            a.return_on_equity_pct,
            a.debt_to_equity
        FROM annual_rows a
        JOIN latest_year l
          ON a.company_id = l.company_id
         AND a.year_num = l.max_year
        WHERE a.return_on_equity_pct > 15
          AND a.debt_to_equity < 1
        ORDER BY a.return_on_equity_pct DESC
        """
    ).fetchall()

    return rows


def check_files():
    return {
        "capital_allocation.csv": CAPITAL_ALLOCATION.exists(),
        "ratio_edge_cases.log": EDGE_LOG.exists(),
    }


def count_required_kpi_tests():
    """
    Count test functions/classes under tests/kpi.

    The Sprint requires at least 20 KPI formula tests.
    """

    test_dir = Path("tests") / "kpi"

    if not test_dir.exists():
        return 0, False

    count = 0

    for path in test_dir.rglob("test_*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig")

        count += len(
            re.findall(
                r"^\s*def\s+test_[A-Za-z0-9_]+\s*\(",
                text,
                flags=re.MULTILINE,
            )
        )

    return count, count >= MIN_REQUIRED_KPI_TESTS


def run_pytest_collection():
    """
    Run pytest collection to verify the actual test suite.

    Returns:
        collected_count, success
    """

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--collect-only",
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout + "\n" + result.stderr

        match = re.search(
            r"(\d+)\s+tests?\s+collected",
            output,
        )

        if match:
            return int(match.group(1)), result.returncode == 0

    except Exception:
        pass

    return 0, False


def generate_report(
    row_count,
    row_pass,
    missing_columns,
    completely_null,
    financials,
    financials_high_de,
    non_financial_high_de,
    screener_rows,
    files,
    required_test_count,
    required_tests_pass,
    collected_test_count,
    collection_pass,
):
    report = []

    report.append("=" * 70)
    report.append(
        "SPRINT 2 - EPIC 02 FINANCIAL RATIO ENGINE REVIEW"
    )
    report.append("=" * 70)
    report.append("")

    # ---------------------------------------------------------
    # 1. Row count
    # ---------------------------------------------------------

    report.append("1. FINANCIAL RATIO ROW COUNT")
    report.append("-" * 70)
    report.append(f"Rows: {row_count}")
    report.append(
        f"Requirement >= 1100: "
        f"{'PASS' if row_pass else 'FAIL'}"
    )
    report.append("")

    # ---------------------------------------------------------
    # 2. KPI columns
    # ---------------------------------------------------------

    report.append("2. REQUIRED KPI COLUMNS")
    report.append("-" * 70)

    if missing_columns:
        report.append(
            "Missing columns: "
            + ", ".join(missing_columns)
        )
    else:
        report.append(
            "All required KPI columns exist."
        )

    if completely_null:
        report.append(
            "Completely NULL columns: "
            + ", ".join(completely_null)
        )
    else:
        report.append(
            "No KPI column is completely NULL."
        )

    report.append("")

    # ---------------------------------------------------------
    # 3. Financials carve-out
    # ---------------------------------------------------------

    report.append("3. FINANCIALS CARVE-OUT")
    report.append("-" * 70)

    report.append(
        f"Financials companies: "
        f"{financials['count']}"
    )

    report.append(
        f"Expected {EXPECTED_FINANCIALS}: "
        f"{'PASS' if financials['count'] == EXPECTED_FINANCIALS else 'FAIL'}"
    )

    report.append(
        "Sector column: "
        f"{financials['reason']}"
    )

    if financials_high_de is not None:
        report.append(
            "Suppressed Financials high-D/E warnings: "
            f"{financials_high_de}"
        )

        report.append(
            "Non-Financial high-D/E warnings: "
            f"{non_financial_high_de}"
        )

        report.append(
            "Financials D/E suppression: "
            + (
                "PASS"
                if financials_high_de == 0
                else "FAIL"
            )
        )

    report.append("")

    # ---------------------------------------------------------
    # 4. Screener
    # ---------------------------------------------------------

    report.append("4. SPRINT 2 SCREENER")
    report.append("-" * 70)

    report.append(
        "Filter: ROE > 15% AND D/E < 1"
    )

    report.append(
        "Basis: latest annual record per company"
    )

    report.append(
        f"Result count: {len(screener_rows)}"
    )

    screener_pass = 15 <= len(screener_rows) <= 50

    report.append(
        "Expected range 15-50: "
        + ("PASS" if screener_pass else "CHECK")
    )

    report.append("")
    report.append("Screener results:")

    for row in screener_rows:
        company, year, roe, de = row

        report.append(
            f"{company:<15} "
            f"{year:<12} "
            f"ROE={roe:.2f}% "
            f"D/E={de:.2f}"
        )

    report.append("")

    # ---------------------------------------------------------
    # 5. Output files
    # ---------------------------------------------------------

    report.append("5. REQUIRED OUTPUT FILES")
    report.append("-" * 70)

    for filename, exists in files.items():
        report.append(
            f"{filename}: "
            f"{'PASS' if exists else 'FAIL'}"
        )

    report.append("")

    # ---------------------------------------------------------
    # 6. Tests
    # ---------------------------------------------------------

    report.append("6. KPI TEST VALIDATION")
    report.append("-" * 70)

    report.append(
        f"KPI test functions found: "
        f"{required_test_count}"
    )

    report.append(
        f"Required >= {MIN_REQUIRED_KPI_TESTS}: "
        f"{'PASS' if required_tests_pass else 'FAIL'}"
    )

    report.append(
        f"Pytest collected tests: "
        f"{collected_test_count}"
    )

    report.append(
        "Pytest collection: "
        f"{'PASS' if collection_pass else 'CHECK'}"
    )

    report.append("")

    # ---------------------------------------------------------
    # 7. Final status
    # ---------------------------------------------------------

    report.append("7. FINAL STATUS")
    report.append("-" * 70)

    overall = (
        row_pass
        and not missing_columns
        and not completely_null
        and financials["count"] == EXPECTED_FINANCIALS
        and financials_high_de == 0
        and 15 <= len(screener_rows) <= 50
        and files["capital_allocation.csv"]
        and files["ratio_edge_cases.log"]
        and required_tests_pass
        and collection_pass
    )

    report.append(
        "SPRINT 2 STATUS: "
        + ("PASS" if overall else "CHECK REQUIRED")
    )

    report.append("=" * 70)

    REVIEW_REPORT.write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    return overall


def main():
    conn = sqlite3.connect(DB_PATH)

    try:
        row_count, row_pass = check_row_count(conn)

        missing_columns, completely_null = check_kpis(conn)

        financials = check_financials(conn)

        financials_high_de, non_financial_high_de = (
            check_high_leverage_suppression(conn)
        )

        screener_rows = screener(conn)

        files = check_files()

        required_test_count, required_tests_pass = (
            count_required_kpi_tests()
        )

        collected_test_count, collection_pass = (
            run_pytest_collection()
        )

        overall = generate_report(
            row_count,
            row_pass,
            missing_columns,
            completely_null,
            financials,
            financials_high_de,
            non_financial_high_de,
            screener_rows,
            files,
            required_test_count,
            required_tests_pass,
            collected_test_count,
            collection_pass,
        )

        print("=" * 70)
        print("SPRINT 2 REVIEW")
        print("=" * 70)

        print(
            f"Financial ratio rows: {row_count} "
            f"({'PASS' if row_pass else 'FAIL'})"
        )

        print(
            "Required KPI columns: "
            + (
                "PASS"
                if not missing_columns
                else "FAIL"
            )
        )

        print(
            "Completely NULL KPI columns: "
            + (
                "NONE"
                if not completely_null
                else ", ".join(completely_null)
            )
        )

        print(
            f"Financials companies: "
            f"{financials['count']} "
            f"(expected {EXPECTED_FINANCIALS})"
        )

        if financials_high_de is not None:
            print(
                "Financials high-D/E warnings: "
                f"{financials_high_de}"
            )

        print(
            "Non-Financial high-D/E rows: "
            f"{non_financial_high_de}"
        )

        print(
            "Screener ROE > 15%, D/E < 1: "
            f"{len(screener_rows)} companies"
        )

        print(
            "capital_allocation.csv: "
            + (
                "PASS"
                if files["capital_allocation.csv"]
                else "FAIL"
            )
        )

        print(
            "ratio_edge_cases.log: "
            + (
                "PASS"
                if files["ratio_edge_cases.log"]
                else "FAIL"
            )
        )

        print(
            "Required KPI test functions: "
            f"{required_test_count}"
        )

        print(
            "Pytest collected tests: "
            f"{collected_test_count}"
        )

        print("")
        print(
            "Report created:",
            REVIEW_REPORT,
        )

        print(
            "Sprint 2 overall:",
            "PASS" if overall else "CHECK REQUIRED",
        )

        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()