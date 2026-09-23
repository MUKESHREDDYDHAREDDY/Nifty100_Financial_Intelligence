import os
import sqlite3
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DB_FILE = "nifty100.db"
RAW_DIR = "data/raw"
AUDIT_FILE = "data/processed/load_audit.csv"


# ============================================================
# 8 COMPANIES TO EXCLUDE
# Based on companies.xlsx - sectors.xlsx comparison
# ============================================================

EXCLUDED_COMPANIES = {
    "ULTRACEMCO",
    "UNIONBANK",
    "UNITDSPR",
    "VBL",
    "VEDL",
    "WIPRO",
    "ZOMATO",
    "ZYDUSLIFE",
}


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

def clean_column_names(df):

    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    return df


# ============================================================
# CHECK WHETHER FILE HAS EXPECTED COLUMNS
# ============================================================

def has_expected_columns(df, expected):

    return set(expected).issubset(set(df.columns))


# ============================================================
# LOAD EXCEL
# ============================================================

def load_excel(file_name):

    path = os.path.join(RAW_DIR, file_name)

    if not os.path.exists(path):

        print(f"WARNING: File not found: {path}")
        return None

    # --------------------------------------------------------
    # Expected headers
    # --------------------------------------------------------

    expected = {

        "companies.xlsx": [
            "id",
            "company_logo",
            "company_name",
            "chart_link",
            "about_company",
            "website",
            "nse_profile",
            "bse_profile",
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage"
        ],

        "profitandloss.xlsx": [
            "id",
            "company_id",
            "year"
        ],

        "balancesheet.xlsx": [
            "id",
            "company_id",
            "year"
        ],

        "cashflow.xlsx": [
            "id",
            "company_id",
            "year"
        ],

        "analysis.xlsx": [
            "id",
            "company_id"
        ],

        "documents.xlsx": [
            "id",
            "company_id",
            "year"
        ],

        "prosandcons.xlsx": [
            "id",
            "company_id"
        ],

        "sectors.xlsx": [
            "id",
            "company_id"
        ],

        "stock_prices.xlsx": [
            "id",
            "company_id",
            "date"
        ],

        "financial_ratios.xlsx": [
            "id",
            "company_id",
            "year"
        ],

        "peer_groups.xlsx": [
            "id",
            "peer_group_name",
            "company_id"
        ],

        "market_cap.xlsx": [
            "id",
            "company_id",
            "year"
        ],
    }

    expected_columns = expected.get(file_name, [])

    # --------------------------------------------------------
    # Try header=0 first
    # --------------------------------------------------------

    df = pd.read_excel(
        path,
        header=0
    )

    df = clean_column_names(df)

    # --------------------------------------------------------
    # If header=0 is wrong, try header=1
    # --------------------------------------------------------

    if not has_expected_columns(
        df,
        expected_columns
    ):

        df2 = pd.read_excel(
            path,
            header=1
        )

        df2 = clean_column_names(df2)

        if has_expected_columns(
            df2,
            expected_columns
        ):

            df = df2

        else:

            # ------------------------------------------------
            # Try header=2 as additional protection
            # ------------------------------------------------

            df3 = pd.read_excel(
                path,
                header=2
            )

            df3 = clean_column_names(df3)

            if has_expected_columns(
                df3,
                expected_columns
            ):

                df = df3

    # --------------------------------------------------------
    # Remove empty rows
    # --------------------------------------------------------

    df = (
        df
        .dropna(how="all")
        .reset_index(drop=True)
    )

    print(
        f"Loaded {file_name}: "
        f"{len(df)} rows, {len(df.columns)} columns"
    )

    print(
        "Columns:",
        list(df.columns)
    )

    return df


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    conn = sqlite3.connect(DB_FILE)

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def table_exists(conn, table_name):

    result = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (table_name,)
    ).fetchone()

    return result is not None


# ============================================================
# CLEAR TABLE
# ============================================================

def clear_table(conn, table_name):

    if not table_exists(
        conn,
        table_name
    ):

        print(
            f"Skipped: {table_name} "
            f"-> table does not exist"
        )

        return

    try:

        conn.execute(
            f"DELETE FROM {table_name}"
        )

        print(
            f"Cleared: {table_name}"
        )

    except sqlite3.Error as e:

        print(
            f"Could not clear {table_name}: {e}"
        )


# ============================================================
# CLEAN COMPANY IDs
# ============================================================

def clean_company_ids(df):

    if "company_id" in df.columns:

        df["company_id"] = (
            df["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if "id" in df.columns:

        df["id"] = (
            df["id"]
            .astype(str)
            .str.strip()
        )

    return df


# ============================================================
# CLEAN YEAR
# IMPORTANT:
# DO NOT REMOVE RECORDS
# ============================================================

def clean_year_column(df, file_name):

    if "year" not in df.columns:

        return df

    # Preserve document years exactly
    if file_name == "documents.xlsx":

        df["year"] = (
            df["year"]
            .astype(str)
            .str.strip()
        )

        return df

    # Do not delete invalid years.
    # Assignment row counts should remain equal
    # to the source files.

    df["year"] = (
        df["year"]
        .astype(str)
        .str.strip()
    )

    return df


# ============================================================
# FILTER ONLY COMPANIES TABLE
# ============================================================

def filter_companies(df):

    if "id" not in df.columns:

        return df

    before = len(df)

    df["id"] = (
        df["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df = df[
        ~df["id"].isin(EXCLUDED_COMPANIES)
    ].copy()

    removed = before - len(df)

    print(
        f"Filtered companies.xlsx: "
        f"removed {removed} companies"
    )

    print(
        "Excluded companies:",
        ", ".join(sorted(EXCLUDED_COMPANIES))
    )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df, table_name, file_name):

    df = clean_company_ids(df)

    df = clean_year_column(
        df,
        file_name
    )

    # --------------------------------------------------------
    # ONLY companies table is reduced from 100 -> 92
    # --------------------------------------------------------

    if table_name == "companies":

        df = filter_companies(df)

        columns = [
            "id",
            "company_logo",
            "company_name",
            "chart_link",
            "about_company",
            "website",
            "nse_profile",
            "bse_profile",
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage"
        ]

    elif table_name == "profitandloss":

        columns = [
            "id",
            "company_id",
            "year",
            "sales",
            "expenses",
            "operating_profit",
            "opm_percentage",
            "other_income",
            "interest",
            "depreciation",
            "profit_before_tax",
            "tax_percentage",
            "net_profit",
            "eps",
            "dividend_payout"
        ]

    elif table_name == "balancesheet":

        columns = [
            "id",
            "company_id",
            "year",
            "equity_capital",
            "reserves",
            "borrowings",
            "other_liabilities",
            "total_liabilities",
            "fixed_assets",
            "cwip",
            "investments",
            "other_asset",
            "total_assets"
        ]

    elif table_name == "cashflow":

        columns = [
            "id",
            "company_id",
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow"
        ]

    elif table_name == "analysis":

        columns = [
            "id",
            "company_id",
            "compounded_sales_growth",
            "compounded_profit_growth",
            "stock_price_cagr",
            "roe"
        ]

    elif table_name == "documents":

        columns = [
            "id",
            "company_id",
            "year",
            "annual_report"
        ]

    elif table_name == "prosandcons":

        columns = [
            "id",
            "company_id",
            "pros",
            "cons"
        ]

    elif table_name == "sectors":

        columns = [
            "id",
            "company_id",
            "broad_sector",
            "sub_sector",
            "index_weight_pct",
            "market_cap_category"
        ]

    elif table_name == "stock_prices":

        columns = [
            "id",
            "company_id",
            "date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
            "adjusted_close"
        ]

    elif table_name == "financial_ratios":

        columns = [
            "id",
            "company_id",
            "year",
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
            "cash_from_operations_cr"
        ]

    elif table_name == "peer_groups":

        columns = [
            "id",
            "peer_group_name",
            "company_id",
            "is_benchmark"
        ]

    elif table_name == "market_cap":

        columns = [
            "id",
            "company_id",
            "year",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct"
        ]

    else:

        raise ValueError(
            f"Unknown table: {table_name}"
        )

    # --------------------------------------------------------
    # Validate columns
    # --------------------------------------------------------

    missing = [
        col for col in columns
        if col not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing columns in {file_name}: {missing}"
        )

    return df[columns].copy()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 05 - FULL DATA LOAD")
    print("=" * 60)

    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    # --------------------------------------------------------
    # Determine valid companies from sectors
    # --------------------------------------------------------

    print(
        "\nDetermining valid companies..."
    )

    sectors_path = os.path.join(
        RAW_DIR,
        "sectors.xlsx"
    )

    sectors_df = pd.read_excel(
        sectors_path,
        header=0
    )

    sectors_df = clean_column_names(
        sectors_df
    )

    valid_companies = set(
        sectors_df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    print(
        f"Valid companies from sectors.xlsx: "
        f"{len(valid_companies)}"
    )

    # --------------------------------------------------------
    # Calculate excluded companies
    # --------------------------------------------------------

    companies_path = os.path.join(
        RAW_DIR,
        "companies.xlsx"
    )

    companies_source = pd.read_excel(
        companies_path,
        header=0
    )

    companies_source = clean_column_names(
        companies_source
    )

    all_companies = set(
        companies_source["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    excluded = sorted(
        all_companies - valid_companies
    )

    print(
        f"Excluded companies: {len(excluded)}"
    )

    print(
        "Excluded companies:"
    )

    print(
        ", ".join(excluded)
    )

    # --------------------------------------------------------
    # Connection
    # --------------------------------------------------------

    conn = get_connection()

    print(
        "\nSQLite connection successful"
    )

    print(
        "Foreign keys:",
        conn.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]
    )

    # ========================================================
    # FILES
    # ========================================================

    files = [

        ("companies.xlsx", "companies"),

        ("profitandloss.xlsx", "profitandloss"),

        ("balancesheet.xlsx", "balancesheet"),

        ("cashflow.xlsx", "cashflow"),

        ("analysis.xlsx", "analysis"),

        ("documents.xlsx", "documents"),

        ("prosandcons.xlsx", "prosandcons"),

        ("sectors.xlsx", "sectors"),

        ("stock_prices.xlsx", "stock_prices"),

        ("financial_ratios.xlsx", "financial_ratios"),

        ("peer_groups.xlsx", "peer_groups"),

        ("market_cap.xlsx", "market_cap"),
    ]

    # ========================================================
    # CLEAR
    # ========================================================

    print(
        "\nClearing existing data..."
    )

    clear_order = [

        "market_cap",
        "financial_ratios",
        "stock_prices",
        "peer_groups",
        "prosandcons",
        "documents",
        "sectors",
        "analysis",
        "cashflow",
        "balancesheet",
        "profitandloss",
        "companies"
    ]

    for table in clear_order:

        clear_table(
            conn,
            table
        )

    conn.commit()

    # ========================================================
    # LOAD
    # ========================================================

    audit = []

    for file_name, table_name in files:

        print(
            "\n" + "-" * 60
        )

        df = load_excel(
            file_name
        )

        if df is None:

            audit.append({

                "file_name": file_name,
                "table_name": table_name,
                "status": "NOT_FOUND",
                "row_count": 0,
                "error": ""

            })

            continue

        try:

            # ------------------------------------------------
            # Skip market_cap if database table doesn't exist
            # ------------------------------------------------

            if not table_exists(
                conn,
                table_name
            ):

                print(
                    f"SKIPPED: Database table "
                    f"'{table_name}' does not exist."
                )

                audit.append({

                    "file_name": file_name,
                    "table_name": table_name,
                    "status": "SKIPPED",
                    "row_count": 0,
                    "error":
                        f"Database table '{table_name}' "
                        f"does not exist."

                })

                continue

            # ------------------------------------------------
            # Prepare
            # ------------------------------------------------

            df = prepare_data(
                df,
                table_name,
                file_name
            )

            # ------------------------------------------------
            # IMPORTANT:
            # Do NOT filter financial tables.
            #
            # The assignment source counts are:
            # P&L = 1276
            # BS = 1312
            # CF = 1187
            # Prices = 5520
            # ------------------------------------------------

            # ------------------------------------------------
            # Insert
            # ------------------------------------------------

            df.to_sql(
                table_name,
                conn,
                if_exists="append",
                index=False
            )

            count = conn.execute(
                f"SELECT COUNT(*) "
                f"FROM {table_name}"
            ).fetchone()[0]

            print(
                f"SUCCESS: {table_name} -> "
                f"{len(df)} rows inserted"
            )

            print(
                f"Database count: {count}"
            )

            audit.append({

                "file_name": file_name,
                "table_name": table_name,
                "status": "LOADED",
                "row_count": len(df),
                "error": ""

            })

        except Exception as e:

            print(
                f"ERROR loading {file_name}: {e}"
            )

            audit.append({

                "file_name": file_name,
                "table_name": table_name,
                "status": "FAILED",
                "row_count": 0,
                "error": str(e)

            })

    conn.commit()

    # ========================================================
    # AUDIT
    # ========================================================

    audit_df = pd.DataFrame(
        audit
    )

    audit_df.to_csv(
        AUDIT_FILE,
        index=False
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "LOAD AUDIT"
    )

    print(
        "=" * 60
    )

    print(
        audit_df.to_string(
            index=False
        )
    )

    print(
        f"\nAudit saved to: {AUDIT_FILE}"
    )

    # ========================================================
    # COMPANY COUNT
    # ========================================================

    company_count = conn.execute(
        "SELECT COUNT(*) FROM companies"
    ).fetchone()[0]

    print(
        f"\nCompanies in database: "
        f"{company_count}"
    )

    # ========================================================
    # CHECK EXCLUDED COMPANIES
    # ========================================================

    placeholders = ",".join(
        ["?"] * len(EXCLUDED_COMPANIES)
    )

    excluded_found = conn.execute(
        f"""
        SELECT id
        FROM companies
        WHERE UPPER(TRIM(id))
        IN ({placeholders})
        """,
        tuple(EXCLUDED_COMPANIES)
    ).fetchall()

    print(
        f"\nExcluded companies found in database: "
        f"{len(excluded_found)}"
    )

    if len(excluded_found) == 0:

        print(
            "All 8 excluded companies "
            "successfully removed."
        )

    else:

        print(
            "WARNING: Excluded companies still exist:"
        )

        print(
            excluded_found
        )

    # ========================================================
    # FOREIGN KEY CHECK
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "SQLITE FOREIGN KEY CHECK"
    )

    print(
        "=" * 60
    )

    fk_errors = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print(
        f"Foreign-key violations: "
        f"{len(fk_errors)}"
    )

    if len(fk_errors) == 0:

        print(
            "Foreign-key check PASSED"
        )

    else:

        print(
            "Foreign-key check FAILED"
        )

        for error in fk_errors:

            print(error)

    # ========================================================
    # FINAL COUNTS
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "FINAL TABLE ROW COUNTS"
    )

    print(
        "=" * 60
    )

    for _, table_name in files:

        if table_exists(
            conn,
            table_name
        ):

            count = conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

            print(
                f"{table_name:<20}{count}"
            )

    # ========================================================
    # CLOSE
    # ========================================================

    conn.close()

    print(
        "\n" + "=" * 60
    )

    print(
        "DAY 05 LOAD COMPLETED"
    )

    print(
        "=" * 60
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()