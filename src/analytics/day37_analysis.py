"""
Day 37 - Cluster Profiling, Correlation, Outliers and Portfolio Statistics.
"""

import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


DB_PATH = "nifty100.db"

LATEST_YEAR = "Mar 2024"

KPI_COLUMNS = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "interest_coverage",
    "asset_turnover",
    "dividend_payout_ratio_pct",
]
def load_latest_kpis():
    """Load latest-year KPI data for the 92 authoritative companies."""
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id
        FROM companies
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,
            operating_profit_margin_pct,
            net_profit_margin_pct,
            interest_coverage,
            asset_turnover,
            dividend_payout_ratio_pct
        FROM financial_ratios
        WHERE year = 'Mar 2024'
        """,
        conn,
    )

    conn.close()

    # Explicitly restrict ratio records to the 92
    # authoritative company IDs.
    ratios = ratios[
        ratios["company_id"].isin(
            companies["company_id"]
        )
    ].copy()

    # Keep all 92 authoritative companies.
    # Missing Mar 2024 ratios remain NaN.
    df = companies.merge(
        ratios,
        on="company_id",
        how="left",
    )

    return df



def create_correlation_heatmap(df):
    """Create Pearson correlation heatmap for the 10 KPIs."""
    os.makedirs("reports", exist_ok=True)

    numeric = df[KPI_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce",
    )

    correlation = numeric.corr(method="pearson")

    plt.figure(figsize=(12, 10))

    plt.imshow(
        correlation,
        interpolation="nearest",
        aspect="auto",
    )

    plt.colorbar(label="Pearson Correlation")

    plt.xticks(
        range(len(KPI_COLUMNS)),
        KPI_COLUMNS,
        rotation=90,
    )

    plt.yticks(
        range(len(KPI_COLUMNS)),
        KPI_COLUMNS,
    )

    plt.title(
        "Nifty100 Latest-Year KPI Correlation Heatmap"
    )

    # Add correlation values inside cells.
    for i in range(len(KPI_COLUMNS)):
        for j in range(len(KPI_COLUMNS)):
            value = correlation.iloc[i, j]

            if pd.notna(value):
                plt.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                )

    plt.tight_layout()

    plt.savefig(
        "reports/correlation_heatmap.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    return correlation


def create_outlier_report(df):
    """Create broad-sector Z-score outlier report."""
    merged = df.merge(
        pd.read_csv("output/cluster_labels.csv")[
            ["company_id", "cluster_id", "cluster_name"]
        ],
        on="company_id",
        how="left",
    )

    # Get broad sector from companies table.
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            broad_sector
        FROM companies
        """,
        conn,
    )

    conn.close()

    merged = merged.merge(
        companies,
        on="company_id",
        how="left",
    )

    records = []

    for sector, group in merged.groupby(
        "broad_sector",
        dropna=False,
    ):
        for metric in KPI_COLUMNS:
            values = pd.to_numeric(
                group[metric],
                errors="coerce",
            )

            mean = values.mean()
            std = values.std()

            if pd.isna(std) or std == 0:
                z_scores = pd.Series(
                    0.0,
                    index=group.index,
                )
            else:
                z_scores = (values - mean) / std

            for index, z in z_scores.items():
                if pd.notna(z) and abs(z) >= 3:
                    records.append(
                        {
                            "company_id": group.loc[
                                index,
                                "company_id",
                            ],
                            "broad_sector": sector,
                            "metric": metric,
                            "value": values.loc[index],
                            "z_score": z,
                            "outlier_flag": True,
                        }
                    )

    output = pd.DataFrame(
        records,
        columns=[
            "company_id",
            "broad_sector",
            "metric",
            "value",
            "z_score",
            "outlier_flag",
        ],
    )

    os.makedirs("output", exist_ok=True)

    output.to_csv(
        "output/outlier_report.csv",
        index=False,
    )

    return output


def create_portfolio_stats(df):
    """Create P10/P25/P50/P75/P90/Mean/Std statistics."""
    numeric = df[KPI_COLUMNS].apply(
        pd.to_numeric,
        errors="coerce",
    )

    stats = pd.DataFrame(
        {
            "P10": numeric.quantile(0.10),
            "P25": numeric.quantile(0.25),
            "P50": numeric.quantile(0.50),
            "P75": numeric.quantile(0.75),
            "P90": numeric.quantile(0.90),
            "Mean": numeric.mean(),
            "Std": numeric.std(),
        }
    )

    stats.index.name = "metric"

    os.makedirs("output", exist_ok=True)

    stats.to_csv(
        "output/portfolio_stats.csv"
    )

    return stats


def main():
    """Run the complete Day 37 analysis."""
    print("=== DAY 37 - CLUSTER PROFILING & ANALYSIS ===")

    df = load_latest_kpis()

    print("Latest year:", LATEST_YEAR)
    print("Companies with latest-year data:", len(df))

    if df.empty:
        raise ValueError(
            "No data found for the selected latest year."
        )

    # Correlation heatmap.
    correlation = create_correlation_heatmap(df)

    print("\nCorrelation heatmap created:")
    print("reports/correlation_heatmap.png")

    # Outlier analysis.
    outliers = create_outlier_report(df)

    print("\nOutlier report created:")
    print("output/outlier_report.csv")
    print("Outlier records:", len(outliers))

    # Portfolio statistics.
    stats = create_portfolio_stats(df)

    print("\nPortfolio statistics created:")
    print("output/portfolio_stats.csv")

    print("\nPortfolio statistics:")
    print(stats.round(2).to_string())

    print("\n=== DAY 37 COMPLETE ===")


if __name__ == "__main__":
    main()