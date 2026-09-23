import os
import pandas as pd

from src.etl.validator import validate_data


# ============================================================
# DAY 03 - DATA QUALITY VALIDATION RUNNER
# ============================================================

RAW_DIR = "data/raw"
OUTPUT_DIR = "output"

# Create output folder if it does not exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# NORMALIZE YEAR COLUMN
# ============================================================

def normalize_year_column(df):
    """
    Normalize different year formats.

    Examples:
        'Mar 2024' -> 2024
        'Mar 2023' -> 2023
        '2024'     -> 2024
        2024       -> 2024
    """

    df = df.copy()

    if "year" in df.columns:

        # Convert year values to string
        df["year"] = df["year"].astype(str).str.strip()

        # Extract 4-digit year
        df["year"] = (
            df["year"]
            .str.extract(r"(\d{4})", expand=False)
        )

        # Convert to numeric
        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

    return df


# ============================================================
# LOAD RAW FILES
# ============================================================

def load_raw_files():
    """
    Load all Excel files from data/raw.

    Returns:
        {table_name: dataframe}
    """

    tables = {}

    if not os.path.exists(RAW_DIR):
        print(f"ERROR: Folder not found: {RAW_DIR}")
        return tables

    for file_name in os.listdir(RAW_DIR):

        if file_name.endswith(".xlsx"):

            file_path = os.path.join(
                RAW_DIR,
                file_name
            )

            table_name = os.path.splitext(
                file_name
            )[0]

            try:

                df = pd.read_excel(
                    file_path
                )

                # Normalize year column
                df = normalize_year_column(df)

                tables[table_name] = df

                print(
                    f"Loaded: {file_name} "
                    f"({df.shape[0]} rows, "
                    f"{df.shape[1]} columns)"
                )

            except Exception as e:

                print(
                    f"ERROR loading "
                    f"{file_name}: {e}"
                )

    return tables


# ============================================================
# RUN VALIDATION
# ============================================================

def run_validation():

    print("=" * 60)
    print("DAY 03 - DATA QUALITY VALIDATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load raw datasets
    # --------------------------------------------------------

    tables = load_raw_files()

    print()
    print(
        f"Total tables loaded: "
        f"{len(tables)}"
    )
    print()

    # --------------------------------------------------------
    # Run DQ validation
    # --------------------------------------------------------

    all_failures = []

    for table_name, df in tables.items():

        print(
            f"Validating: {table_name}"
        )

        try:

            failures = validate_data(
                df,
                table_name
            )

            all_failures.extend(
                failures
            )

            if failures:

                print(
                    f"  -> "
                    f"{len(failures)} "
                    f"validation failure(s)"
                )

            else:

                print(
                    "  -> PASS"
                )

        except Exception as e:

            print(
                f"  -> Validation error: "
                f"{e}"
            )

    # --------------------------------------------------------
    # Create validation failures DataFrame
    # --------------------------------------------------------

    if all_failures:

        failures_df = pd.DataFrame(
            all_failures
        )

    else:

        failures_df = pd.DataFrame(
            columns=[
                "table",
                "rule",
                "severity",
                "message"
            ]
        )

    # --------------------------------------------------------
    # Save validation report
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        "validation_failures.csv"
    )

    failures_df.to_csv(
        output_file,
        index=False
    )

    # --------------------------------------------------------
    # Validation Summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("VALIDATION COMPLETED")
    print("=" * 60)

    print(
        f"Total validation failures: "
        f"{len(failures_df)}"
    )

    print(
        f"Report generated: "
        f"{output_file}"
    )

    # --------------------------------------------------------
    # Summary by severity
    # --------------------------------------------------------

    if not failures_df.empty:

        print()
        print("Failures by severity:")

        print(
            failures_df[
                "severity"
            ].value_counts()
        )

        print()
        print("Failures by DQ rule:")

        print(
            failures_df[
                "rule"
            ]
            .value_counts()
            .sort_index()
        )

        print()
        print("Validation failure details:")

        print(
            failures_df.to_string(
                index=False
            )
        )

    else:

        print()
        print(
            "All data quality checks passed!"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_validation()