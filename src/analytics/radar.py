from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DB_PATH = Path("nifty100.db")
OUTPUT_DIR = Path("reports/radar_charts")


RADAR_METRICS = {
    "ROE": ("return_on_equity_pct", True),
    "ROCE": ("roce_percentage", True),
    "NPM": ("net_profit_margin_pct", True),
    "D/E": ("debt_to_equity", False),
    "FCF Score": ("free_cash_flow_cr", True),
    "PAT CAGR 5yr": ("pat_cagr_5yr", True),
    "Revenue CAGR 5yr": ("revenue_cagr_5yr", True),
    "Composite Score": ("composite_quality_score", True),
}


def load_radar_data(db_path=DB_PATH):
    """
    Load latest annual financial data and peer-group assignments.
    """

    conn = sqlite3.connect(db_path)

    try:
        query = """
            SELECT
                f.company_id,
                f.year,
                c.company_name,
                c.roce_percentage,
                f.return_on_equity_pct,
                f.net_profit_margin_pct,
                f.debt_to_equity,
                f.free_cash_flow_cr,
                f.pat_cagr_5yr,
                f.revenue_cagr_5yr,
                f.composite_quality_score,
                pg.peer_group_name
            FROM financial_ratios f
            JOIN companies c
                ON f.company_id = c.id
            LEFT JOIN peer_groups pg
                ON f.company_id = pg.company_id
        """

        df = pd.read_sql_query(query, conn)

    finally:
        conn.close()

    # Exclude TTM.
    annual = df[df["year"] != "TTM"].copy()

    # Keep the latest annual record for each company.
    annual = (
        annual
        .sort_values("year")
        .groupby("company_id", sort=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return annual


def normalize_radar_metric(
    series,
    higher_is_better=True,
):
    """
    Normalize a metric to a 0-100 score using
    P10/P90 winsorization.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    p10 = numeric.quantile(0.10)
    p90 = numeric.quantile(0.90)

    if (
        pd.isna(p10)
        or pd.isna(p90)
        or p10 == p90
    ):
        return pd.Series(
            50.0,
            index=series.index,
        )

    clipped = numeric.clip(
        lower=p10,
        upper=p90,
    )

    score = (
        (clipped - p10)
        / (p90 - p10)
        * 100
    )

    if not higher_is_better:
        score = 100 - score

    return score


def create_radar_chart(
    company_row,
    peer_data,
    output_path,
):
    """
    Create one radar chart comparing a company
    with its peer-group average.
    """

    labels = list(RADAR_METRICS.keys())

    company_scores = []
    peer_scores = []

    for metric_name, (
        column_name,
        higher_is_better,
    ) in RADAR_METRICS.items():

        combined = pd.concat(
            [
                peer_data[column_name],
                pd.Series(
                    [company_row[column_name]]
                ),
            ],
            ignore_index=True,
        )

        normalized = normalize_radar_metric(
            combined,
            higher_is_better,
        )

        company_scores.append(
            normalized.iloc[-1]
        )

        peer_scores.append(
            normalized.iloc[:-1].mean()
        )

    # Close the radar polygons.
    company_scores += company_scores[:1]
    peer_scores += peer_scores[:1]

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False,
    ).tolist()

    angles += angles[:1]

    fig = plt.figure(
        figsize=(8, 8)
    )

    ax = fig.add_subplot(
        111,
        polar=True,
    )

    ax.set_ylim(0, 100)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    ax.set_yticks(
        [20, 40, 60, 80, 100]
    )

    ax.set_yticklabels(
        ["20", "40", "60", "80", "100"]
    )

    ax.plot(
        angles,
        company_scores,
        linewidth=2,
        label=company_row["company_id"],
    )

    ax.fill(
        angles,
        company_scores,
        alpha=0.20,
    )

    ax.plot(
        angles,
        peer_scores,
        linestyle="--",
        linewidth=2,
        label="Peer Group Average",
    )

    ax.set_title(
        "{} — {} Radar Chart".format(
            company_row["company_id"],
            company_row["peer_group_name"],
        ),
        pad=25,
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.25, 1.10),
    )

    plt.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)


def generate_radar_charts(
    db_path=DB_PATH,
    output_dir=OUTPUT_DIR,
):
    """
    Generate a radar chart for every company.

    Companies with a peer group are compared with their
    peer-group average.

    Companies without a peer group are compared with
    the Nifty 100 average.

    Returns the number of charts generated.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_radar_data(db_path)

    generated = 0

    # --------------------------------------------------
    # 1. Companies WITH peer groups
    # --------------------------------------------------

    peer_companies = df[
        df["peer_group_name"].notna()
    ].copy()

    for peer_group_name, peer_group in peer_companies.groupby(
        "peer_group_name"
    ):

        for index in peer_group.index:

            company_row = peer_group.loc[index]

            company_id = company_row[
                "company_id"
            ]

            filename = "{}_radar.png".format(
                company_id
            )

            output_path = (
                output_dir / filename
            )

            create_radar_chart(
                company_row,
                peer_group,
                output_path,
            )

            generated += 1

    # --------------------------------------------------
    # 2. Companies WITHOUT peer groups
    #    Compare with Nifty 100 average
    # --------------------------------------------------

    no_peer_companies = df[
        df["peer_group_name"].isna()
    ].copy()

    for index in no_peer_companies.index:

        company_row = no_peer_companies.loc[index]

        company_id = company_row[
            "company_id"
        ]

        filename = "{}_radar.png".format(
            company_id
        )

        output_path = (
            output_dir / filename
        )

        # Use the complete Nifty 100 annual dataset
        # as the reference group.
        create_radar_chart(
            company_row,
            df,
            output_path,
        )

        generated += 1

    return generated