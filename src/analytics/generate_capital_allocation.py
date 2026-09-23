"""
Day 11 - Capital Allocation Pattern Generator

Generates:
    output/capital_allocation.csv

One unique row is created for every company-year in the cashflow table.

Columns:
    company_id
    year
    cfo_sign
    cfi_sign
    cff_sign
    pattern_label
"""

import csv
import sqlite3
from pathlib import Path

from src.analytics.cashflow_kpis import capital_allocation_pattern


DB_PATH = Path("nifty100.db")
OUTPUT_PATH = Path("output/capital_allocation.csv")


def sign(value):
    """
    Convert cash-flow value to + / - sign.

    Zero is treated as positive.
    Missing values are represented as '-'.
    """
    if value is None:
        return "-"

    return "+" if value >= 0 else "-"


def calculate_cfo_pat_ratio(cfo, pat):
    """
    Calculate CFO / PAT ratio.

    Returns None when PAT is zero or unavailable.
    """
    if cfo is None or pat is None or pat == 0:
        return None

    return cfo / pat


def generate_capital_allocation():

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(DB_PATH)

    try:

        rows = conn.execute(
            """
            SELECT
                cf.company_id,
                cf.year,
                cf.operating_activity,
                cf.investing_activity,
                cf.financing_activity,
                p.net_profit
            FROM cashflow cf

            LEFT JOIN profitandloss p
                ON cf.company_id = p.company_id
                AND cf.year = p.year

            ORDER BY
                cf.company_id,
                cf.id
            """
        ).fetchall()

    finally:
        conn.close()

    # ---------------------------------------------------------
    # Remove duplicate company-year rows
    # ---------------------------------------------------------

    unique_rows = {}

    for (
        company_id,
        year,
        cfo,
        cfi,
        cff,
        pat,
    ) in rows:

        key = (
            company_id,
            year,
        )

        # Keep the first occurrence for each company-year.
        if key not in unique_rows:

            unique_rows[key] = (
                company_id,
                year,
                cfo,
                cfi,
                cff,
                pat,
            )

    output_rows = []

    for (
        company_id,
        year,
        cfo,
        cfi,
        cff,
        pat,
    ) in unique_rows.values():

        cfo_sign = sign(cfo)
        cfi_sign = sign(cfi)
        cff_sign = sign(cff)

        # -----------------------------------------------------
        # CFO / PAT ratio
        # -----------------------------------------------------

        cfo_pat_ratio = calculate_cfo_pat_ratio(
            cfo,
            pat,
        )

        # -----------------------------------------------------
        # Capital allocation pattern
        # -----------------------------------------------------

        pattern_label = capital_allocation_pattern(
            cfo,
            cfi,
            cff,
            cfo_pat_ratio,
        )

        # -----------------------------------------------------
        # Handle unsupported / unknown pattern
        # -----------------------------------------------------

        if pattern_label is None:

            pattern_label = "Mixed"

        output_rows.append(
            [
                company_id,
                year,
                cfo_sign,
                cfi_sign,
                cff_sign,
                pattern_label,
            ]
        )

    # ---------------------------------------------------------
    # Write CSV
    # ---------------------------------------------------------

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "company_id",
                "year",
                "cfo_sign",
                "cfi_sign",
                "cff_sign",
                "pattern_label",
            ]
        )

        writer.writerows(output_rows)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    print("=" * 70)
    print("DAY 11 - CAPITAL ALLOCATION GENERATOR")
    print("=" * 70)

    print(
        f"Created: {OUTPUT_PATH}"
    )

    print(
        f"Rows written: {len(output_rows)}"
    )

    unique_keys = {
        (
            row[0],
            row[1],
        )
        for row in output_rows
    }

    print(
        f"Unique company-year rows: {len(unique_keys)}"
    )

    duplicate_count = (
        len(output_rows)
        - len(unique_keys)
    )

    print(
        f"Duplicate company-year rows: {duplicate_count}"
    )

    null_company = sum(
        1
        for row in output_rows
        if row[0] is None
        or str(row[0]).strip() == ""
    )

    null_year = sum(
        1
        for row in output_rows
        if row[1] is None
        or str(row[1]).strip() == ""
    )

    null_pattern = sum(
        1
        for row in output_rows
        if row[5] is None
        or str(row[5]).strip() == ""
    )

    print(
        f"Missing company_id: {null_company}"
    )

    print(
        f"Missing year: {null_year}"
    )

    print(
        f"Missing pattern_label: {null_pattern}"
    )

    # ---------------------------------------------------------
    # Pattern counts
    # ---------------------------------------------------------

    print("\nPATTERN COUNTS")
    print("-" * 70)

    pattern_counts = {}

    for row in output_rows:

        label = row[5]

        pattern_counts[label] = (
            pattern_counts.get(label, 0) + 1
        )

    for label, count in sorted(
        pattern_counts.items(),
        key=lambda x: (-x[1], str(x[0])),
    ):

        print(
            f"{label}: {count}"
        )

    print("=" * 70)


if __name__ == "__main__":
    generate_capital_allocation()