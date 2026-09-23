import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARSED_FILE = PROJECT_ROOT / "output" / "analysis_parsed.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"

VALIDATION_FILE = OUTPUT_DIR / "cagr_validation.csv"


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Load parsed NLP values
    # --------------------------------------------------
    parsed = pd.read_csv(PARSED_FILE)

    # Only CAGR metrics that can be compared with
    # the Ratio Engine
    cagr_metrics = {
        "compounded_sales_growth": "revenue_cagr_5yr",
        "compounded_profit_growth": "pat_cagr_5yr",
    }

    parsed = parsed[
        parsed["metric_type"].isin(cagr_metrics.keys())
        & (parsed["period_years"] == 5)
    ].copy()

    # --------------------------------------------------
    # Load Ratio Engine values
    # --------------------------------------------------
    db_path = PROJECT_ROOT / "nifty100.db"

    con = sqlite3.connect(db_path)

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            revenue_cagr_5yr,
            pat_cagr_5yr
        FROM financial_ratios
        WHERE revenue_cagr_5yr IS NOT NULL
           OR pat_cagr_5yr IS NOT NULL
        """,
        con,
    )

    con.close()

    # One company-level Ratio Engine value is sufficient
    # because these CAGR fields are repeated across years.
    ratios = ratios.groupby("company_id", as_index=False).first()

    # --------------------------------------------------
    # Compare values
    # --------------------------------------------------
    results = []

    for _, row in parsed.iterrows():

        company_id = row["company_id"]
        metric_type = row["metric_type"]
        parsed_value = float(row["value_pct"])

        ratio_column = cagr_metrics[metric_type]

        matching = ratios[
            ratios["company_id"] == company_id
        ]

        if matching.empty:
            results.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "parsed_value_pct": parsed_value,
                    "ratio_engine_value_pct": None,
                    "divergence_pct": None,
                    "status": "NO_RATIO_ENGINE_DATA",
                }
            )
            continue

        engine_value = matching.iloc[0][ratio_column]

        if pd.isna(engine_value):
            results.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "parsed_value_pct": parsed_value,
                    "ratio_engine_value_pct": None,
                    "divergence_pct": None,
                    "status": "NO_RATIO_ENGINE_DATA",
                }
            )
            continue

        engine_value = float(engine_value)

        # Absolute percentage-point divergence
        divergence = abs(parsed_value - engine_value)

        status = (
            "MANUAL_REVIEW"
            if divergence > 5
            else "PASS"
        )

        results.append(
            {
                "company_id": company_id,
                "metric_type": metric_type,
                "parsed_value_pct": parsed_value,
                "ratio_engine_value_pct": engine_value,
                "divergence_pct": round(divergence, 2),
                "status": status,
            }
        )

    validation = pd.DataFrame(
        results,
        columns=[
            "company_id",
            "metric_type",
            "parsed_value_pct",
            "ratio_engine_value_pct",
            "divergence_pct",
            "status",
        ],
    )

    validation.to_csv(
        VALIDATION_FILE,
        index=False
    )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------
    print("========================================")
    print("CAGR Cross-Validation")
    print("========================================")
    print(f"Records checked : {len(validation)}")
    print(
        f"PASS            : "
        f"{(validation['status'] == 'PASS').sum()}"
    )
    print(
        f"Manual review   : "
        f"{(validation['status'] == 'MANUAL_REVIEW').sum()}"
    )
    print(
        f"No engine data  : "
        f"{(validation['status'] == 'NO_RATIO_ENGINE_DATA').sum()}"
    )
    print(f"Output          : {VALIDATION_FILE}")
    print("========================================")


if __name__ == "__main__":
    main()