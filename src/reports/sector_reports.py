from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.units import mm


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "sector"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE LOAD
# ============================================================

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

    ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        """,
        conn
    )

    peer_groups = pd.read_sql_query(
        """
        SELECT
            company_id,
            peer_group_name
        FROM peer_groups
        """,
        conn
    )

    conn.close()

    return companies, ratios, peer_groups


# ============================================================
# HELPERS
# ============================================================

def clean_year(value):

    if pd.isna(value):
        return np.nan

    text = str(value).strip().upper()

    if "TTM" in text:
        return np.nan

    try:
        return int(text[:4])
    except Exception:
        return np.nan


def prepare_ratios(ratios):

    ratios = ratios.copy()

    ratios["year_num"] = ratios["year"].apply(clean_year)

    ratios = ratios[
        ratios["year_num"].notna()
    ].copy()

    if "id" in ratios.columns:

        ratios = ratios.sort_values(
            ["company_id", "year_num", "id"]
        )

    else:

        ratios = ratios.sort_values(
            ["company_id", "year_num"]
        )

    ratios = ratios.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="last"
    )

    return ratios


def fmt(value, suffix=""):

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return "N/A"


def median_metric(df, column):

    if column not in df.columns:
        return np.nan

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    if values.dropna().empty:
        return np.nan

    return values.median()


# ============================================================
# SECTOR REPORT
# ============================================================

def generate_sector_report(
    sector_name,
    companies,
    ratios,
    peer_groups
):

    sector_companies = peer_groups[
        peer_groups["peer_group_name"] == sector_name
    ].copy()

    sector_companies = sector_companies.merge(
        companies,
        on="company_id",
        how="left"
    )

    company_ids = sector_companies["company_id"].tolist()

    sector_ratios = ratios[
        ratios["company_id"].isin(company_ids)
    ].copy()

    latest = (
        sector_ratios
        .sort_values("year_num")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    safe_name = (
        sector_name
        .replace("&", "and")
        .replace("/", "_")
        .replace(" ", "_")
    )

    output_file = OUTPUT_DIR / f"{safe_name}_report.pdf"

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SectorTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0B1F3A"),
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "SectorSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0B1F3A"),
        spaceBefore=8,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
    )

    story = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            f"{sector_name} — Sector Report",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"{len(sector_companies)} companies covered",
            subtitle_style
        )
    )

    # --------------------------------------------------------
    # MEDIAN KPI SUMMARY
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Sector Median KPI Summary",
            heading_style
        )
    )

    kpi_data = [
        ["KPI", "Sector Median"],
        [
            "ROE (%)",
            fmt(median_metric(latest, "roe_percentage"), "%")
        ],
        [
            "ROCE (%)",
            fmt(median_metric(latest, "roce_percentage"), "%")
        ],
        [
            "Revenue CAGR 5Y (%)",
            fmt(median_metric(latest, "revenue_cagr_5yr"), "%")
        ],
        [
            "PAT CAGR 5Y (%)",
            fmt(median_metric(latest, "pat_cagr_5yr"), "%")
        ],
        [
            "OPM (%)",
            fmt(median_metric(latest, "opm_percentage"), "%")
        ],
        [
            "Debt / Equity",
            fmt(median_metric(latest, "debt_to_equity"))
        ],
        [
            "P/E",
            fmt(median_metric(latest, "pe_ratio"))
        ],
        [
            "P/B",
            fmt(median_metric(latest, "pb_ratio"))
        ],
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[75 * mm, 65 * mm]
    )

    kpi_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0B1F3A")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "RIGHT"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F4F6F8")
                ]
            ),
        ])
    )

    story.append(kpi_table)
    story.append(Spacer(1, 8 * mm))

    # --------------------------------------------------------
    # COMPANY TABLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Company-Level Metrics",
            heading_style
        )
    )

    company_data = [[
        "Ticker",
        "Company",
        "ROE",
        "ROCE",
        "Rev CAGR",
        "PAT CAGR",
        "OPM",
        "D/E",
    ]]

    for _, company in sector_companies.sort_values(
        "company_id"
    ).iterrows():

        cid = company["company_id"]

        row = latest[
            latest["company_id"] == cid
        ]

        if row.empty:
            continue

        r = row.iloc[-1]

        company_data.append([
            str(cid),
            Paragraph(
                str(company["company_name"]),
                body_style
            ),
            fmt(company.get("roe_percentage")),
            fmt(company.get("roce_percentage")),
            fmt(r.get("revenue_cagr_5yr")),
            fmt(r.get("pat_cagr_5yr")),
            fmt(r.get("opm_percentage")),
            fmt(r.get("debt_to_equity")),
        ])

    company_table = Table(
        company_data,
        colWidths=[
            22 * mm,
            50 * mm,
            18 * mm,
            18 * mm,
            20 * mm,
            20 * mm,
            18 * mm,
            18 * mm,
            ],
        repeatRows=1,
    )

    company_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0B1F3A")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                6.5
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "RIGHT"
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F4F6F8")
                ]
            ),
        ])
    )

    story.append(company_table)

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    story.append(Spacer(1, 8 * mm))

    story.append(
        Paragraph(
            "Source: Nifty100 Financial Intelligence SQLite database "
            "and Sprint 2 financial ratio engine.",
            subtitle_style
        )
    )

    doc.build(story)

    return output_file


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 34 - SECTOR REPORT GENERATOR")
    print("=" * 60)

    companies, ratios, peer_groups = load_data()

    ratios = prepare_ratios(ratios)

    sectors = sorted(
        peer_groups["peer_group_name"]
        .dropna()
        .unique()
    )

    print(f"Sector groups found: {len(sectors)}")
    print()

    generated = 0

    for sector in sectors:

        try:

            output_file = generate_sector_report(
                sector,
                companies,
                ratios,
                peer_groups
            )

            generated += 1

            print(
                f"Generated: {output_file.name}"
            )

        except Exception as e:

            print(
                f"ERROR: {sector}: {e}"
            )

    print()
    print("=" * 60)
    print("SECTOR REPORT SUMMARY")
    print("=" * 60)
    print(f"Sectors found : {len(sectors)}")
    print(f"Generated     : {generated}")
    print(f"Output folder : {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()