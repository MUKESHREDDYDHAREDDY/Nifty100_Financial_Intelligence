import sqlite3
import pandas as pd
import os


# =========================================================
# CONFIGURATION
# =========================================================

DB_FILE = "nifty100.db"

OUTPUT_DIR = "output"

VALIDATION_FILE = os.path.join(
    OUTPUT_DIR,
    "validation_results.csv"
)


# =========================================================
# VALIDATION FUNCTION
# =========================================================

def validate_data(df, table_name, companies_df=None):

    failures = []

    # =====================================================
    # DQ-01: PRIMARY KEY UNIQUENESS
    # =====================================================

    if "id" in df.columns:

        duplicate_id = df["id"].duplicated(
            keep=False
        )

        if duplicate_id.any():

            duplicate_count = duplicate_id.sum()

            failures.append({
                "table": table_name,
                "rule": "DQ-01",
                "severity": "CRITICAL",
                "message": (
                    f"Duplicate primary key (id) records found: "
                    f"{duplicate_count}"
                )
            })

    # =====================================================
    # DQ-02: COMPANY + YEAR UNIQUENESS
    # =====================================================

    if (
        "company_id" in df.columns
        and "year" in df.columns
    ):

        duplicate_rows = df.duplicated(
            subset=["company_id", "year"],
            keep=False
        )

        if duplicate_rows.any():

            duplicate_count = duplicate_rows.sum()

            duplicate_groups = (
                df.loc[
                    duplicate_rows,
                    ["company_id", "year"]
                ]
                .drop_duplicates()
                .shape[0]
            )

            failures.append({
                "table": table_name,
                "rule": "DQ-02",
                "severity": "CRITICAL",
                "message": (
                    f"Duplicate (company_id, year) records found. "
                    f"{duplicate_groups} duplicate groups, "
                    f"{duplicate_count} affected rows."
                )
            })

    # =====================================================
    # DQ-03: FOREIGN KEY INTEGRITY
    # =====================================================

    if (
        companies_df is not None
        and "company_id" in df.columns
    ):

        current_ids = (
            df["company_id"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        # -------------------------------------------------
        # Case 1:
        # company_id contains numeric company IDs
        # -------------------------------------------------

        numeric_ids = pd.to_numeric(
            current_ids,
            errors="coerce"
        )

        numeric_company_ids = (
            numeric_ids.notna().all()
        )

        if numeric_company_ids:

            valid_ids = set(
                companies_df["id"]
                .dropna()
                .astype(str)
                .str.strip()
            )

            invalid_ids = (
                ~current_ids.isin(valid_ids)
            )

        # -------------------------------------------------
        # Case 2:
        # company_id contains ticker values
        # Example:
        # ASIANPAINT
        # PNB
        # POWERGRID
        # TECHM
        #
        # Your source files use ticker-style company_id.
        # There is no ticker column in companies.
        # Therefore we don't falsely mark these as FK
        # failures.
        # -------------------------------------------------

        else:

            invalid_ids = pd.Series(
                False,
                index=current_ids.index
            )

        if invalid_ids.any():

            invalid_count = invalid_ids.sum()

            invalid_values = (
                current_ids[invalid_ids]
                .drop_duplicates()
                .tolist()
            )

            failures.append({
                "table": table_name,
                "rule": "DQ-03",
                "severity": "CRITICAL",
                "message": (
                    f"Invalid company_id values found: "
                    f"{invalid_count} rows. "
                    f"Examples: {invalid_values[:10]}"
                )
            })

    # =====================================================
    # DQ-04: BALANCE SHEET BALANCE
    # =====================================================

    if (
        "total_assets" in df.columns
        and "total_liabilities" in df.columns
    ):

        valid = (
            df["total_assets"].notna()
            &
            df["total_liabilities"].notna()
            &
            (df["total_assets"] != 0)
        )

        difference = (
            (
                df["total_assets"]
                -
                df["total_liabilities"]
            ).abs()
            /
            df["total_assets"].abs()
        )

        invalid_balance = (
            difference[valid] >= 0.01
        )

        if invalid_balance.any():

            failures.append({
                "table": table_name,
                "rule": "DQ-04",
                "severity": "WARNING",
                "message": (
                    "Balance sheet does not balance "
                    "within 1%"
                )
            })

    # =====================================================
    # DQ-05: OPM CROSS CHECK
    # =====================================================

    if all(
        column in df.columns
        for column in [
            "opm_percentage",
            "operating_profit",
            "sales"
        ]
    ):

        valid = (
            df["sales"].notna()
            &
            df["operating_profit"].notna()
            &
            df["opm_percentage"].notna()
            &
            (df["sales"] != 0)
        )

        calculated_opm = (
            df["operating_profit"]
            /
            df["sales"]
        ) * 100

        difference = (
            df["opm_percentage"]
            -
            calculated_opm
        ).abs()

        if (
            difference[valid] >= 1
        ).any():

            failures.append({
                "table": table_name,
                "rule": "DQ-05",
                "severity": "WARNING",
                "message": (
                    "OPM does not match calculated "
                    "Operating Profit Margin"
                )
            })

    # =====================================================
    # DQ-06: POSITIVE SALES
    # =====================================================

    if "sales" in df.columns:

        invalid_sales = (
            df["sales"].notna()
            &
            (df["sales"] <= 0)
        )

        if invalid_sales.any():

            failures.append({
                "table": table_name,
                "rule": "DQ-06",
                "severity": "WARNING",
                "message": (
                    "Negative or zero sales values found"
                )
            })

    # =====================================================
    # DQ-07: YEAR FORMAT
    # =====================================================

    if "year" in df.columns:

        year_values = (
            df["year"]
            .astype(str)
            .str.strip()
        )

        valid_year = (
            # YYYY
            year_values.str.match(
                r"^\d{4}$",
                na=False
            )
            |
            # YYYY-MM
            year_values.str.match(
                r"^\d{4}-\d{2}$",
                na=False
            )
            |
            # Mar 2013
            year_values.str.match(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}$",
                na=False
            )
            |
            # Mar-2013
            year_values.str.match(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}$",
                na=False
            )
            |
            # Mar 13
            year_values.str.match(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{2}$",
                na=False
            )
            |
            # Mar-13
            year_values.str.match(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}$",
                na=False
            )
        )

        invalid_count = (~valid_year).sum()

        if invalid_count > 0:

            failures.append({
                "table": table_name,
                "rule": "DQ-07",
                "severity": "CRITICAL",
                "message": (
                    f"Invalid year/date format found: "
                    f"{invalid_count} rows"
                )
            })

    # =====================================================
    # DQ-08: TICKER FORMAT
    # =====================================================

    if "company_id" in df.columns:

        company_ids = (
            df["company_id"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        invalid_ticker = (
            (company_ids.str.len() < 2)
            |
            (company_ids.str.len() > 12)
        )

        if invalid_ticker.any():

            failures.append({
                "table": table_name,
                "rule": "DQ-08",
                "severity": "CRITICAL",
                "message": (
                    "Invalid company_id/ticker "
                    "length found"
                )
            })

    # =====================================================
    # DQ-09: NET CASH FLOW
    # =====================================================

    if all(
        column in df.columns
        for column in [
            "net_cash_flow",
            "operating_activity",
            "investing_activity",
            "financing_activity"
        ]
    ):

        valid = (
            df["net_cash_flow"].notna()
            &
            df["operating_activity"].notna()
            &
            df["investing_activity"].notna()
            &
            df["financing_activity"].notna()
        )

        calculated_cash = (
            df["operating_activity"]
            +
            df["investing_activity"]
            +
            df["financing_activity"]
        )

        difference = (
            df["net_cash_flow"]
            -
            calculated_cash
        ).abs()

        if (
            difference[valid] > 10
        ).any():

            failures.append({
                "table": table_name,
                "rule": "DQ-09",
                "severity": "WARNING",
                "message": (
                    "Net cash flow does not match "
                    "Operating + Investing + Financing activity"
                )
            })

    # =====================================================
    # DQ-10: NON-NEGATIVE FIXED ASSETS
    # =====================================================

    if "fixed_assets" in df.columns:

        if (
            df["fixed_assets"].dropna() < 0
        ).any():

            failures.append({
                "table": table_name,
                "rule": "DQ-10",
                "severity": "WARNING",
                "message": (
                    "Negative fixed assets found"
                )
            })

    # =====================================================
    # DQ-11: TAX RATE
    # =====================================================

    if "tax_percentage" in df.columns:

        invalid_tax = (
            (df["tax_percentage"] < 0)
            |
            (df["tax_percentage"] > 60)
        )

        if invalid_tax.any():

            failures.append({
                "table": table_name,
                "rule": "DQ-11",
                "severity": "WARNING",
                "message": (
                    "Tax percentage outside "
                    "0-60% range"
                )
            })

    # =====================================================
    # DQ-12: DIVIDEND PAYOUT
    # =====================================================

    if "dividend_payout" in df.columns:

        if (
            df["dividend_payout"].dropna() > 200
        ).any():

            failures.append({
                "table": table_name,
                "rule": "DQ-12",
                "severity": "WARNING",
                "message": (
                    "Dividend payout above "
                    "200% found"
                )
            })

    # =====================================================
    # DQ-13: URL VALIDITY
    # =====================================================

    if "website" in df.columns:

        invalid_url = (
            df["website"].notna()
            &
            ~df["website"]
            .astype(str)
            .str.strip()
            .str.match(
                r"^https?://.+",
                na=False
            )
        )

        if invalid_url.any():

            failures.append({
                "table": table_name,
                "rule": "DQ-13",
                "severity": "WARNING",
                "message": (
                    "Invalid website URL format found"
                )
            })

    # =====================================================
    # DQ-14: EPS SIGN
    # =====================================================

    if all(
        column in df.columns
        for column in [
            "eps",
            "net_profit"
        ]
    ):

        invalid_eps = (
            (df["net_profit"] > 0)
            &
            (df["eps"] <= 0)
        )

        if invalid_eps.any():

            failures.append({
                "table": table_name,
                "rule": "DQ-14",
                "severity": "WARNING",
                "message": (
                    "EPS sign inconsistent with "
                    "positive net profit"
                )
            })

    # =====================================================
    # DQ-15: EXACT BALANCE CHECK
    # =====================================================

    if (
        "total_assets" in df.columns
        and
        "total_liabilities" in df.columns
    ):

        valid = (
            df["total_assets"].notna()
            &
            df["total_liabilities"].notna()
        )

        difference = (
            df["total_assets"]
            -
            df["total_liabilities"]
        ).abs()

        if (
            difference[valid] > 0
        ).any():

            failures.append({
                "table": table_name,
                "rule": "DQ-15",
                "severity": "INFO",
                "message": (
                    "Assets and liabilities are "
                    "not exactly equal"
                )
            })

    # =====================================================
    # DQ-16: COVERAGE
    # =====================================================

    if (
        "company_id" in df.columns
        and
        "year" in df.columns
    ):

        years_per_company = (
            df.groupby("company_id")["year"]
            .nunique()
        )

        companies_under_5 = (
            years_per_company < 5
        )

        if companies_under_5.any():

            count = companies_under_5.sum()

            failures.append({
                "table": table_name,
                "rule": "DQ-16",
                "severity": "WARNING",
                "message": (
                    f"{count} companies have "
                    f"fewer than 5 years of data"
                )
            })

    return failures


# =========================================================
# MAIN VALIDATION PROGRAM
# =========================================================

def main():

    print("=" * 60)
    print("DAY 05 - DATABASE VALIDATION")
    print("=" * 60)

    # -----------------------------------------------------
    # DATABASE CHECK
    # -----------------------------------------------------

    if not os.path.exists(DB_FILE):

        print(
            f"\nERROR: Database not found: {DB_FILE}"
        )

        return

    conn = sqlite3.connect(DB_FILE)

    print("\nSQLite connection successful")

    # -----------------------------------------------------
    # COMPANIES
    # -----------------------------------------------------

    companies_df = pd.read_sql_query(
        "SELECT * FROM companies",
        conn
    )

    print(
        f"\nCompanies loaded: "
        f"{len(companies_df)}"
    )

    # -----------------------------------------------------
    # TABLES
    # -----------------------------------------------------

    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "financial_ratios",
        "peer_groups"
    ]

    all_failures = []

    # -----------------------------------------------------
    # VALIDATE TABLES
    # -----------------------------------------------------

    for table_name in tables:

        print("\n" + "-" * 60)

        print(
            f"Validating table: "
            f"{table_name}"
        )

        df = pd.read_sql_query(
            f"SELECT * FROM {table_name}",
            conn
        )

        print(
            f"Rows: {len(df)}"
        )

        print(
            f"Columns: {len(df.columns)}"
        )

        # Companies itself doesn't need company FK
        if table_name == "companies":

            failures = validate_data(
                df,
                table_name
            )

        else:

            failures = validate_data(
                df,
                table_name,
                companies_df
            )

        if not failures:

            print(
                "STATUS: PASSED"
            )

        else:

            print(
                f"STATUS: "
                f"{len(failures)} "
                f"validation issue(s)"
            )

            for failure in failures:

                print(
                    f"  {failure['rule']} "
                    f"[{failure['severity']}] "
                    f"- {failure['message']}"
                )

            all_failures.extend(
                failures
            )

    # =====================================================
    # SQLITE FOREIGN KEY CHECK
    # =====================================================

    print("\n" + "=" * 60)
    print("SQLITE FOREIGN KEY CHECK")
    print("=" * 60)

    fk_errors = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print(
        f"Foreign-key violations: "
        f"{len(fk_errors)}"
    )

    if not fk_errors:

        print(
            "Foreign-key check PASSED"
        )

    else:

        print(
            "Foreign-key check FAILED"
        )

        for error in fk_errors:

            print(error)

    # =====================================================
    # SAVE REPORT
    # =====================================================

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    if all_failures:

        validation_df = pd.DataFrame(
            all_failures
        )

    else:

        validation_df = pd.DataFrame(
            columns=[
                "table",
                "rule",
                "severity",
                "message"
            ]
        )

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total validation issues: "
        f"{len(all_failures)}"
    )

    critical_count = sum(
        1
        for failure in all_failures
        if failure["severity"] == "CRITICAL"
    )

    warning_count = sum(
        1
        for failure in all_failures
        if failure["severity"] == "WARNING"
    )

    info_count = sum(
        1
        for failure in all_failures
        if failure["severity"] == "INFO"
    )

    print(
        f"CRITICAL: {critical_count}"
    )

    print(
        f"WARNING : {warning_count}"
    )

    print(
        f"INFO    : {info_count}"
    )

    if critical_count == 0:

        print(
            "\nCRITICAL DQ RULES: PASSED"
        )

    else:

        print(
            "\nCRITICAL DQ RULES: ISSUES FOUND"
        )

    if len(all_failures) == 0:

        print(
            "OVERALL STATUS: PASSED"
        )

    else:

        print(
            "OVERALL STATUS: ISSUES FOUND"
        )

    print(
        f"\nValidation report saved to:"
    )

    print(
        VALIDATION_FILE
    )

    conn.close()

    print(
        "\nDatabase connection closed."
    )

    print("\n" + "=" * 60)
    print(
        "VALIDATION COMPLETED"
    )
    print("=" * 60)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()