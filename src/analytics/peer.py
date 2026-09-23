from pathlib import Path
import sqlite3
import pandas as pd


DB_PATH = Path("nifty100.db")


PEER_METRICS = {
    "ROE": ("return_on_equity_pct", True),
    "ROCE": ("roce", True),
    "NPM": ("net_profit_margin_pct", True),
    "D/E": ("debt_to_equity", False),
    "FCF": ("free_cash_flow_cr", True),
    "PAT CAGR 5yr": ("pat_cagr_5yr", True),
    "Revenue CAGR 5yr": ("revenue_cagr_5yr", True),
    "EPS CAGR 5yr": ("eps_cagr_5yr", True),
    "Interest Coverage": ("interest_coverage", True),
    "Asset Turnover": ("asset_turnover", True),
}


def load_peer_groups(
    conn: sqlite3.Connection,
) -> pd.DataFrame:
    """
    Load peer-group assignments from SQLite.
    """
    return pd.read_sql_query(
        """
        SELECT
            peer_group_name,
            company_id,
            is_benchmark
        FROM peer_groups
        """,
        conn,
    )


def load_peer_data(
    conn: sqlite3.Connection,
) -> pd.DataFrame:
    """
    Load the latest annual financial metrics for companies.
    """

    query = """
        SELECT
            f.company_id,
            f.year,
            c.company_name,
            c.broad_sector,
            c.roce_percentage,
            f.return_on_equity_pct,
            f.net_profit_margin_pct,
            f.debt_to_equity,
            f.free_cash_flow_cr,
            f.pat_cagr_5yr,
            f.revenue_cagr_5yr,
            f.eps_cagr_5yr,
            f.interest_coverage,
            f.asset_turnover
        FROM financial_ratios f
        JOIN companies c
            ON f.company_id = c.id
    """

    df = pd.read_sql_query(query, conn)

    # Use latest annual record for each company.
    annual = df[df["year"] != "TTM"].copy()

    annual = (
        annual
        .sort_values("year")
        .groupby("company_id", sort=False)
        .tail(1)
        .reset_index(drop=True)
    )

    # Use source ROCE from companies table.
    annual["roce"] = annual["roce_percentage"]

    return annual


def calculate_percentile(
    series: pd.Series,
    higher_is_better: bool = True,
) -> pd.Series:
    """
    Calculate SQL-style PERCENT_RANK from 0 to 100.

    Formula:
        (rank - 1) / (n - 1) * 100

    Higher values receive higher percentiles.

    For D/E, lower values are better, so the percentile
    ranking is inverted.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    valid = numeric.notna()
    result = pd.Series(float("nan"), index=series.index)

    n = valid.sum()

    if n == 0:
        return result

    if n == 1:
        result.loc[valid] = 100.0
        return result

    ranks = numeric[valid].rank(
        method="average",
        ascending=True,
    )

    percentile = (
        (ranks - 1)
        / (n - 1)
        * 100
    )

    if not higher_is_better:
        percentile = 100 - percentile

    result.loc[valid] = percentile

    return result


def calculate_peer_percentiles(
    db_path: Path = DB_PATH,
) -> pd.DataFrame:
    """
    Calculate percentile rankings for all peer groups
    across all 10 required metrics.

    Returns one row per:
        company + peer group + metric
    """

    conn = sqlite3.connect(db_path)

    try:
        peer_groups = load_peer_groups(conn)
        financial_data = load_peer_data(conn)
    finally:
        conn.close()

    merged = peer_groups.merge(
        financial_data,
        on="company_id",
        how="left",
    )

    records = []

    for peer_group_name, group in merged.groupby(
        "peer_group_name",
        sort=True,
    ):

        for metric_name, (
            column_name,
            higher_is_better,
        ) in PEER_METRICS.items():

            values = group[column_name]

            percentile = calculate_percentile(
                values,
                higher_is_better=higher_is_better,
            )

            for index in group.index:

                records.append(
                    {
                        "company_id": group.loc[index, "company_id"],
                        "peer_group_name": peer_group_name,
                        "metric": metric_name,
                        "value": group.loc[index, column_name],
                        "percentile_rank": percentile.loc[index],
                        "year": group.loc[index, "year"],
                    }
                )

    return pd.DataFrame(records)

def save_peer_percentiles(
    db_path: Path = DB_PATH,
) -> pd.DataFrame:
    """
    Calculate and save peer percentile rankings
    into the SQLite peer_percentiles table.
    """

    result = calculate_peer_percentiles(db_path)

    conn = sqlite3.connect(db_path)

    try:
        conn.execute(
            "DROP TABLE IF EXISTS peer_percentiles"
        )

        conn.execute(
            """
            CREATE TABLE peer_percentiles (
                company_id TEXT NOT NULL,
                peer_group_name TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL,
                percentile_rank REAL,
                year TEXT
            )
            """
        )

        result.to_sql(
            "peer_percentiles",
            conn,
            if_exists="append",
            index=False,
        )

        conn.commit()

    finally:
        conn.close()

    return result


