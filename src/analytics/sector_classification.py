"""
Day 13 - Sector Classification

Adds broad_sector to the companies table.

Financials are treated separately for leverage analysis because
high D/E is structurally normal for banks, NBFCs and insurance
companies.
"""

import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")


# Financial companies in the current 92-company dataset.
# These include banks, NBFCs, insurance companies and financial
# services businesses.
FINANCIALS = {
    "AXISBANK",
    "BAJAJFINSV",
    "BAJFINANCE",
    "BANKBARODA",
    "CANBK",
    "CHOLAFIN",
    "HDFCBANK",
    "HDFCLIFE",
    "ICICIBANK",
    "ICICIGI",
    "ICICIPRULI",
    "INDUSINDBK",
    "JIOFIN",
    "KOTAKBANK",
    "LICI",
    "PFC",
    "PNB",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
}


def add_broad_sector_column(conn):
    """Add broad_sector column if it does not exist."""

    columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(companies)"
        ).fetchall()
    }

    if "broad_sector" not in columns:
        conn.execute(
            """
            ALTER TABLE companies
            ADD COLUMN broad_sector TEXT
            """
        )

        conn.commit()


def classify_companies(conn):
    """Assign broad sectors to all companies."""

    rows = conn.execute(
        "SELECT id FROM companies ORDER BY id"
    ).fetchall()

    updated = 0

    for (company_id,) in rows:

        if company_id in FINANCIALS:
            sector = "Financials"
        else:
            sector = "Non-Financials"

        conn.execute(
            """
            UPDATE companies
            SET broad_sector = ?
            WHERE id = ?
            """,
            (sector, company_id),
        )

        updated += 1

    conn.commit()

    return updated


def validate(conn):
    """Validate sector classification."""

    total = conn.execute(
        "SELECT COUNT(*) FROM companies"
    ).fetchone()[0]

    financials = conn.execute(
        """
        SELECT COUNT(*)
        FROM companies
        WHERE broad_sector = 'Financials'
        """
    ).fetchone()[0]

    non_financials = conn.execute(
        """
        SELECT COUNT(*)
        FROM companies
        WHERE broad_sector = 'Non-Financials'
        """
    ).fetchone()[0]

    nulls = conn.execute(
        """
        SELECT COUNT(*)
        FROM companies
        WHERE broad_sector IS NULL
        """
    ).fetchone()[0]

    print("=" * 70)
    print("SECTOR CLASSIFICATION")
    print("=" * 70)
    print("Total companies:", total)
    print("Financials:", financials)
    print("Non-Financials:", non_financials)
    print("Unclassified:", nulls)

    print("\nFinancial companies:")
    rows = conn.execute(
        """
        SELECT id, company_name
        FROM companies
        WHERE broad_sector = 'Financials'
        ORDER BY id
        """
    ).fetchall()

    for company_id, company_name in rows:
        print(f"  {company_id:15} {company_name}")

    print("=" * 70)

    if total != 92:
        raise RuntimeError(
            f"Expected 92 companies, found {total}"
        )

    if financials != 20:
        raise RuntimeError(
            f"Expected 20 Financials companies, found {financials}"
        )

    if nulls != 0:
        raise RuntimeError(
            f"{nulls} companies have no sector classification"
        )


def main():
    conn = sqlite3.connect(DB_PATH)

    try:
        add_broad_sector_column(conn)
        updated = classify_companies(conn)

        print(f"Companies classified: {updated}")

        validate(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
