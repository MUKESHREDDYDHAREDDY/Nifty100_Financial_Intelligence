import re
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "analysis.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURE_FILE = OUTPUT_DIR / "parse_failures.csv"


# ---------------------------------------------------------
# Regex
# ---------------------------------------------------------
PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*(-?[\d.]+)\s*%"
)


# ---------------------------------------------------------
# Target fields
# ---------------------------------------------------------
TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# ---------------------------------------------------------
# Parse one text value
# ---------------------------------------------------------
def parse_metric(value):
    """
    Extract period and percentage from text such as:

        10 Years: 21%
        5 Years: 24%
        3 Years: 17%

    Returns:
        (period_years, value_pct)

    If the text does not match:
        (None, None)
    """

    if pd.isna(value):
        return None, None

    text = str(value).strip()

    match = PATTERN.search(text)

    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


# ---------------------------------------------------------
# Main parser
# ---------------------------------------------------------
def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Header is on Excel row 2, therefore header=1
    df = pd.read_excel(INPUT_FILE, header=1)

    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():

        company_id = row["company_id"]

        for metric in TARGET_FIELDS:

            raw_value = row[metric]

            period_years, value_pct = parse_metric(raw_value)

            if period_years is not None:

                parsed_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "period_years": period_years,
                        "value_pct": value_pct,
                    }
                )

            else:

                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "raw_value": raw_value,
                    }
                )

    # -----------------------------------------------------
    # Save parsed output
    # -----------------------------------------------------
    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    parsed_df.to_csv(PARSED_FILE, index=False)

    # -----------------------------------------------------
    # Save parsing failures
    # -----------------------------------------------------
    failure_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
        ],
    )

    failure_df.to_csv(FAILURE_FILE, index=False)

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------
    print("========================================")
    print("NLP Analysis Parser")
    print("========================================")
    print(f"Input file       : {INPUT_FILE}")
    print(f"Parsed rows      : {len(parsed_df)}")
    print(f"Parse failures   : {len(failure_df)}")
    print(f"Parsed output    : {PARSED_FILE}")
    print(f"Failure output   : {FAILURE_FILE}")
    print("========================================")


if __name__ == "__main__":
    main()