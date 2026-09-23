from pathlib import Path
import sqlite3
import pandas as pd

from tearsheet import generate_tearsheet, prepare_df


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports"
TEARSHEET_DIR = OUTPUT_DIR / "tearsheets"
SKIPPED_FILE = PROJECT_ROOT / "output" / "skipped_tearsheets.csv"

VALUTION_FILE = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
PROS_CONS_FILE = PROJECT_ROOT / "output" / "pros_cons_generated.csv"
CASHFLOW_FILE = PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"


# ---------------------------------------------------------
# CREATE DIRECTORIES
# ---------------------------------------------------------
TEARSHEET_DIR.mkdir(parents=True, exist_ok=True)
SKIPPED_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# LOAD ALL DATA
# ---------------------------------------------------------
def load_data():

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name,
            broad_sector,
            roe_percentage,
            roce_percentage
        FROM companies
        """,
        conn
    )

    pl = pd.read_sql_query(
        "SELECT * FROM profitandloss",
        conn
    )

    bs = pd.read_sql_query(
        "SELECT * FROM balancesheet",
        conn
    )

    cf = pd.read_sql_query(
        "SELECT * FROM cashflow",
        conn
    )

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        conn
    )

    conn.close()

    # Prepare data exactly like Day 33
    pl = prepare_df(pl)
    bs = prepare_df(bs)
    cf = prepare_df(cf)
    ratios = prepare_df(ratios)
    conn.close()

    valuation = pd.read_excel(VALUTION_FILE)

    pros_cons = pd.read_csv(PROS_CONS_FILE)

    cashflow_intel = pd.read_excel(CASHFLOW_FILE)

    return (
        companies,
        pl,
        bs,
        cf,
        ratios,
        valuation,
        pros_cons,
        cashflow_intel
    )


# ---------------------------------------------------------
# HISTORICAL YEAR COUNT
# ---------------------------------------------------------
def get_year_counts(pl):

    temp = pl.copy()

    temp["year_clean"] = (
        temp["year"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    temp = temp[
        ~temp["year_clean"].str.contains("TTM", na=False)
    ]

    counts = (
        temp.groupby("company_id")["year_clean"]
        .nunique()
        .to_dict()
    )

    return counts


# ---------------------------------------------------------
# BATCH GENERATION
# ---------------------------------------------------------
def generate_all():

    print("=" * 60)
    print("DAY 34 - BATCH COMPANY TEARSHEETS")
    print("=" * 60)

    (
        companies,
        pl,
        bs,
        cf,
        ratios,
        valuation,
        pros_cons,
        cashflow_intel
    ) = load_data()

    year_counts = get_year_counts(pl)

    generated = []
    skipped = []

    print(f"Companies found: {len(companies)}")
    print()

    for _, company in companies.iterrows():

        company_id = company["company_id"]
        company_name = company["company_name"]

        years = year_counts.get(company_id, 0)

        output_file = (
            TEARSHEET_DIR /
            f"{company_id}_tearsheet.pdf"
        )

        # -------------------------------------------------
        # LESS THAN 3 YEARS
        # -------------------------------------------------
        if years < 3:

            skipped.append({
                "company_id": company_id,
                "company_name": company_name,
                "year_count": years,
                "reason": "Less than 3 years of P&L data"
            })

            print(
                f"SKIPPED: {company_id} - "
                f"{company_name} ({years} years)"
            )

            continue

        # -------------------------------------------------
        # GENERATE PDF
        # -------------------------------------------------
        try:

            generate_tearsheet(
                company_id,
                company,
                pl,
                bs,
                cf,
                ratios,
                valuation,
                pros_cons,
                cashflow_intel
            )

            generated.append(company_id)

            print(
                f"Generated: {company_id}_tearsheet.pdf"
            )

        except Exception as e:

            skipped.append({
                "company_id": company_id,
                "company_name": company_name,
                "year_count": years,
                "reason": f"Generation error: {e}"
            })

            print(
                f"ERROR: {company_id} - "
                f"{company_name}: {e}"
            )

    # -----------------------------------------------------
    # SAVE SKIPPED REPORT
    # -----------------------------------------------------
    pd.DataFrame(skipped).to_csv(
        SKIPPED_FILE,
        index=False
    )

    print()
    print("=" * 60)
    print("BATCH TEARSHEET SUMMARY")
    print("=" * 60)

    print(f"Companies in DB : {len(companies)}")
    print(f"Generated       : {len(generated)}")
    print(f"Skipped         : {len(skipped)}")
    print(f"Skipped report  : {SKIPPED_FILE}")

    print("=" * 60)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    generate_all()