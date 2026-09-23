"""
Day 32 - Capital Allocation Analysis

Tasks:
1. Validate capital_allocation.csv coverage
2. Create latest-year distribution summary
3. Add latest capital allocation pattern to cashflow_intelligence.xlsx
4. Generate year-over-year pattern changes
"""

import os
import sqlite3
import pandas as pd


DB_PATH = "nifty100.db"
INPUT_FILE = "output/capital_allocation.csv"
CASHFLOW_FILE = "output/cashflow_intelligence.xlsx"

DISTRIBUTION_FILE = "output/capital_allocation_distribution.csv"
PATTERN_CHANGES_FILE = "output/pattern_changes.csv"

os.makedirs("output", exist_ok=True)


def clean_year(year):
    """Extract numeric year from values such as 'Mar 2024'."""
    if pd.isna(year):
        return None

    text = str(year).strip()

    if text.upper() == "TTM":
        return None

    import re

    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group())

    return None


def main():

    print("=" * 60)
    print("DAY 32 - CAPITAL ALLOCATION ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load authoritative 92-company universe
    # --------------------------------------------------------

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT id AS company_id
        FROM companies
        ORDER BY id
        """,
        conn
    )

    conn.close()

    companies["company_id"] = companies["company_id"].astype(str)

    company_set = set(companies["company_id"])

    print()
    print("Companies in database :", len(company_set))

    # --------------------------------------------------------
    # 2. Load capital allocation CSV
    # --------------------------------------------------------

    allocation = pd.read_csv(INPUT_FILE)

    allocation["company_id"] = allocation["company_id"].astype(str)

    print("Rows in source CSV   :", len(allocation))
    print(
        "Companies in source  :",
        allocation["company_id"].nunique()
    )

    # --------------------------------------------------------
    # 3. Filter to authoritative 92-company universe
    # --------------------------------------------------------

    allocation_92 = allocation[
        allocation["company_id"].isin(company_set)
    ].copy()

    print(
        "Rows for 92 companies:",
        len(allocation_92)
    )

    print(
        "Companies covered    :",
        allocation_92["company_id"].nunique()
    )

    # --------------------------------------------------------
    # 4. Check missing companies
    # --------------------------------------------------------

    covered_set = set(
        allocation_92["company_id"]
    )

    missing_companies = sorted(
        company_set - covered_set
    )

    print()
    print(
        "Companies missing from capital allocation:",
        len(missing_companies)
    )

    if missing_companies:
        print(missing_companies)

    # --------------------------------------------------------
    # 5. Prepare year
    # --------------------------------------------------------

    allocation_92["year_num"] = allocation_92[
        "year"
    ].apply(clean_year)

    allocation_92 = allocation_92[
        allocation_92["year_num"].notna()
    ].copy()

    allocation_92 = allocation_92.sort_values(
        ["company_id", "year_num"]
    )

    # Remove duplicate company/year records
    allocation_92 = allocation_92.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="last"
    )

    # --------------------------------------------------------
    # 6. Latest year for each company
    # --------------------------------------------------------

    latest = (
        allocation_92
        .sort_values(["company_id", "year_num"])
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    print()
    print(
        "Companies with latest pattern:",
        latest["company_id"].nunique()
    )

    # --------------------------------------------------------
    # 7. Latest-year distribution
    # --------------------------------------------------------

    distribution = (
        latest["pattern_label"]
        .value_counts()
        .rename_axis("pattern_label")
        .reset_index(name="company_count")
    )

    distribution["percentage"] = (
        distribution["company_count"]
        / len(latest)
        * 100
    )

    distribution_file = DISTRIBUTION_FILE

    distribution.to_csv(
        distribution_file,
        index=False
    )

    print()
    print("Latest-year distribution:")
    print(distribution.to_string(index=False))

    # --------------------------------------------------------
    # 8. Add latest capital allocation to
    #    cashflow_intelligence.xlsx
    # --------------------------------------------------------

    if os.path.exists(CASHFLOW_FILE):

        cashflow_intel = pd.read_excel(
            CASHFLOW_FILE
        )

        cashflow_intel["company_id"] = (
            cashflow_intel["company_id"]
            .astype(str)
        )

        # Remove old column if it already exists
        if "capital_allocation_label" in cashflow_intel.columns:
            cashflow_intel = cashflow_intel.drop(
                columns=["capital_allocation_label"]
            )

        latest_pattern = latest[
            [
                "company_id",
                "pattern_label"
            ]
        ].rename(
            columns={
                "pattern_label":
                    "capital_allocation_label"
            }
        )

        cashflow_intel = cashflow_intel.merge(
            latest_pattern,
            on="company_id",
            how="left"
        )

        # Put capital allocation column at the end
        cashflow_intel.to_excel(
            CASHFLOW_FILE,
            index=False
        )

        print()
        print(
            "Updated:",
            CASHFLOW_FILE
        )

    else:
        print()
        print(
            "WARNING: cashflow_intelligence.xlsx not found"
        )

    # --------------------------------------------------------
    # 9. Year-over-year pattern changes
    # --------------------------------------------------------

    pattern_data = allocation_92[
        [
            "company_id",
            "year",
            "year_num",
            "pattern_label"
        ]
    ].copy()

    pattern_data = pattern_data.sort_values(
        ["company_id", "year_num"]
    )

    pattern_data["previous_pattern"] = (
        pattern_data
        .groupby("company_id")["pattern_label"]
        .shift(1)
    )

    pattern_data["previous_year"] = (
        pattern_data
        .groupby("company_id")["year"]
        .shift(1)
    )

    changes = pattern_data[
        pattern_data["previous_pattern"].notna()
        & (
            pattern_data["pattern_label"]
            != pattern_data["previous_pattern"]
        )
    ].copy()

    changes["change"] = (
        changes["previous_pattern"]
        + " -> "
        + changes["pattern_label"]
    )

    changes = changes[
        [
            "company_id",
            "previous_year",
            "year",
            "previous_pattern",
            "pattern_label",
            "change"
        ]
    ]

    changes.to_csv(
        PATTERN_CHANGES_FILE,
        index=False
    )

    print()
    print(
        "Year-over-year pattern changes:",
        len(changes)
    )

    print()
    print("Output files:")
    print("1.", os.path.abspath(distribution_file))
    print("2.", os.path.abspath(PATTERN_CHANGES_FILE))
    print("3.", os.path.abspath(CASHFLOW_FILE))

    print("=" * 60)


if __name__ == "__main__":
    main()