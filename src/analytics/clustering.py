"""
Day 36 - KMeans clustering for Nifty100 Financial Intelligence.

Creates:
    reports/elbow_plot.png
    output/cluster_labels.csv
    output/cluster_profiles.csv
"""

import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


DB_PATH = "nifty100.db"
N_CLUSTERS = 5
RANDOM_STATE = 42

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

def clean_year(value):
    """Convert financial year labels such as Mar-24 or Mar 2024 to a numeric year."""
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    # Four-digit year anywhere in the value, e.g. "Mar 2024", "Dec 2012"
    import re

    match = re.search(r"(20\d{2})", text)
    if match:
        return int(match.group(1))

    # Two-digit year such as "Mar-24" or "Mar-13"
    match = re.search(r"(?:^|[-/ ])(\d{2})$", text)
    if match:
        year = int(match.group(1))

        # Financial data in this project is mainly 2000–2099.
        return 2000 + year

    return np.nan



def calculate_fcf_cagr(cashflow):
    """Calculate five-year FCF CAGR using annual cash-flow records."""
    df = cashflow.copy()

    df["year_num"] = df["year"].apply(clean_year)

    df = df[df["year_num"].notna()].copy()

    df["fcf"] = (
        df["operating_activity"].fillna(0)
        + df["investing_activity"].fillna(0)
    )

    df = (
        df.sort_values(["company_id", "year_num", "id"])
        .drop_duplicates(["company_id", "year_num"], keep="last")
    )

    results = []

    for company_id, group in df.groupby("company_id"):
        group = group.sort_values("year_num")

        if len(group) < 6:
            results.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": np.nan,
                }
            )
            continue

        latest_year = group["year_num"].max()
        start_year = latest_year - 5

        start_rows = group[group["year_num"] == start_year]
        end_rows = group[group["year_num"] == latest_year]

        if start_rows.empty or end_rows.empty:
            results.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": np.nan,
                }
            )
            continue

        start_fcf = start_rows.iloc[-1]["fcf"]
        end_fcf = end_rows.iloc[-1]["fcf"]

        # CAGR is mathematically undefined when the starting
        # or ending FCF is zero/negative.
        if start_fcf <= 0 or end_fcf <= 0:
            cagr = np.nan
        else:
            cagr = (
                ((end_fcf / start_fcf) ** (1 / 5)) - 1
            ) * 100

        results.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(results)


def load_data():
    """Load clustering inputs from the SQLite database."""
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name,
            broad_sector
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
            operating_profit_margin_pct
        FROM financial_ratios
        """,
        conn,
    )

    cashflow = pd.read_sql_query(
        """
        SELECT
            id,
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        """,
        conn,
    )

    conn.close()

    return companies, ratios, cashflow


def prepare_latest_ratios(ratios):
    """Select the latest available ratio record for each company."""
    df = ratios.copy()

    df["year_num"] = df["year"].apply(clean_year)

    df = df[df["year_num"].notna()].copy()

    df = (
        df.sort_values(["company_id", "year_num"])
        .drop_duplicates("company_id", keep="last")
    )

    return df


def impute_sector_median(df):
    """Fill missing clustering metrics using broad-sector medians."""
    result = df.copy()

    for feature in FEATURES:
        result[feature] = pd.to_numeric(
            result[feature], errors="coerce"
        )

        result[feature] = result.groupby(
            "broad_sector"
        )[feature].transform(
            lambda x: x.fillna(x.median())
        )

        # If an entire sector is missing a feature, use the
        # overall median as a final fallback.
        result[feature] = result[feature].fillna(
            result[feature].median()
        )

    return result


def generate_elbow_plot(X):
    """Generate the KMeans elbow plot for k=2 through k=10."""
    inertias = []
    ks = range(2, 11)

    for k in ks:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20,
        )

        model.fit(X)
        inertias.append(model.inertia_)

    os.makedirs("reports", exist_ok=True)

    plt.figure(figsize=(9, 6))
    plt.plot(list(ks), inertias, marker="o")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")
    plt.xticks(list(ks))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(
        "reports/elbow_plot.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    return dict(zip(ks, inertias))


def assign_cluster_names(profile):
    """Assign five descriptive archetype names to all clusters."""
    score = profile.copy()

    for column in FEATURES:
        score[column] = pd.to_numeric(
            score[column],
            errors="coerce"
        )

    # Overall quality score:
    # higher ROE, growth, margins and FCF growth are positive;
    # higher debt-to-equity is negative.
    score["quality_score"] = (
        score["return_on_equity_pct"].rank(pct=True)
        + score["revenue_cagr_5yr"].rank(pct=True)
        + score["operating_profit_margin_pct"].rank(pct=True)
        + score["fcf_cagr_5yr"].rank(pct=True)
        - score["debt_to_equity"].rank(pct=True)
    )

    names = {}

    remaining = set(score.index)

    # 1. Highest overall quality
    quality_cluster = score["quality_score"].idxmax()
    names[quality_cluster] = "High-Quality Compounders"
    remaining.discard(quality_cluster)

    # 2. Highest growth
    growth_candidates = score.loc[
        list(remaining),
        "revenue_cagr_5yr"
    ]

    if not growth_candidates.empty:
        growth_cluster = growth_candidates.idxmax()
        names[growth_cluster] = "Emerging Growth"
        remaining.discard(growth_cluster)

    # 3. Highest debt
    debt_candidates = score.loc[
        list(remaining),
        "debt_to_equity"
    ]

    if not debt_candidates.empty:
        debt_cluster = debt_candidates.idxmax()
        names[debt_cluster] = "Distressed or Turnaround"
        remaining.discard(debt_cluster)

    # 4. Highest operating margin
    margin_candidates = score.loc[
        list(remaining),
        "operating_profit_margin_pct"
    ]

    if not margin_candidates.empty:
        margin_cluster = margin_candidates.idxmax()
        names[margin_cluster] = "Defensive Dividend Payers"
        remaining.discard(margin_cluster)

    # 5. Final remaining cluster
    for cluster_id in remaining:
        names[cluster_id] = "Value Cyclicals"

    return names


def main():
    """Run the complete Day 36 clustering pipeline."""
    print("=== DAY 36 - KMEANS CLUSTERING ===")

    companies, ratios, cashflow = load_data()

    print("Companies loaded:", len(companies))

    fcf = calculate_fcf_cagr(cashflow)

    latest_ratios = prepare_latest_ratios(ratios)

    data = companies.merge(
        latest_ratios[
            [
                "company_id",
                "return_on_equity_pct",
                "debt_to_equity",
                "revenue_cagr_5yr",
                "operating_profit_margin_pct",
            ]
        ],
        on="company_id",
        how="left",
    )

    data = data.merge(
        fcf,
        on="company_id",
        how="left",
    )

    print("Companies before imputation:", len(data))

    # Sector-median imputation
    data = impute_sector_median(data)

    # Confirm no missing clustering values remain.
    missing = data[FEATURES].isna().sum().sum()

    print("Missing feature values after imputation:", missing)

    X = data[FEATURES].astype(float)

    # StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Features scaled successfully.")

    # Elbow plot
    inertias = generate_elbow_plot(X_scaled)

    print("\nElbow plot created:")
    print("reports/elbow_plot.png")

    for k, inertia in inertias.items():
        print(f"k={k}: inertia={inertia:.2f}")

    # Final KMeans model
    model = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    cluster_ids = model.fit_predict(X_scaled)

    # Distance from assigned centroid
    distances = np.linalg.norm(
        X_scaled - model.cluster_centers_[cluster_ids],
        axis=1,
    )

    data["cluster_id"] = cluster_ids
    data["distance_from_centroid"] = distances

    # Cluster profile
    profile = (
        data.groupby("cluster_id")[FEATURES]
        .agg(["mean", "median"])
    )

    profile.to_csv(
        "output/cluster_profiles.csv"
    )

    # Convert multi-index columns to readable names.
    profile_mean = (
        data.groupby("cluster_id")[FEATURES]
        .mean()
    )

    cluster_names = assign_cluster_names(
        profile_mean
    )

    data["cluster_name"] = data["cluster_id"].map(
        cluster_names
    )

    output = data[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].copy()

    os.makedirs("output", exist_ok=True)

    output.to_csv(
        "output/cluster_labels.csv",
        index=False,
    )

    print("\n=== CLUSTER RESULTS ===")
    print(
        output["cluster_id"]
        .value_counts()
        .sort_index()
    )

    print("\nCluster names:")
    for cluster_id in sorted(cluster_names):
        print(
            cluster_id,
            "->",
            cluster_names[cluster_id],
        )

    print("\nOutput:")
    print("output/cluster_labels.csv")
    print("output/cluster_profiles.csv")

    print("\nCompanies clustered:", len(output))
    print(
        "Unique clusters:",
        output["cluster_id"].nunique(),
    )

    print("\n=== DAY 36 COMPLETE ===")


if __name__ == "__main__":
    main()