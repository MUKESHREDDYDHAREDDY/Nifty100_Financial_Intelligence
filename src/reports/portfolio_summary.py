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
CASHFLOW_FILE = PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"

OUTPUT_DIR = PROJECT_ROOT / "reports" / "portfolio"
OUTPUT_FILE = OUTPUT_DIR / "portfolio_summary.pdf"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def fmt(value, suffix=""):

    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return "N/A"


def trend_arrow(values):

    values = pd.to_numeric(
        values,
        errors="coerce"
    ).dropna()

    if len(values) < 2:
        return "→"

    first = float(values.iloc[0])
    last = float(values.iloc[-1])

    if last > first * 1.05:
        return "↑"

    if last < first * 0.95:
        return "↓"

    return "→"


# ============================================================
# LOAD DATA
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

    conn.close()

    cashflow = pd.read_excel(
        CASHFLOW_FILE
    )

    return companies, ratios, cashflow


# ============================================================
# PREPARE RATIOS
# ============================================================

def prepare_ratios(ratios):

    ratios = ratios.copy()

    ratios["year_num"] = ratios["year"].apply(
        clean_year
    )

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


# ============================================================
# CREATE ONE COMPANY PAGE
# ============================================================

def create_company_page(
    company,
    ratios,
    cashflow
):

    company_id = company["company_id"]

    company_ratios = ratios[
        ratios["company_id"] == company_id
    ].sort_values("year_num")

    latest_ratio = (
        company_ratios.iloc[-1]
        if not company_ratios.empty
        else None
    )

    cf_row = cashflow[
        cashflow["company_id"] == company_id
    ]

    latest_cf = (
        cf_row.iloc[-1]
        if not cf_row.empty
        else None
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    story = []

    title_style = ParagraphStyle(
        "PortfolioTitle",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0B1F3A"),
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "PortfolioSubtitle",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=10,
    )

    heading_style = ParagraphStyle(
        "PortfolioHeading",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0B1F3A"),
        spaceBefore=5,
        spaceAfter=5,
    )

    story.append(
        Paragraph(
            f"{company_id} — {company['company_name']}",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Sector: {company['broad_sector']}",
            subtitle_style
        )
    )

    # --------------------------------------------------------
    # KPI VALUES
    # --------------------------------------------------------

    if latest_ratio is not None:

        roe = latest_ratio.get(
            "roe_percentage",
            company.get("roe_percentage")
        )

        debt_equity = latest_ratio.get(
            "debt_to_equity"
        )

        opm = latest_ratio.get(
            "opm_percentage"
        )

        pe = latest_ratio.get(
            "pe_ratio"
        )

        pb = latest_ratio.get(
            "pb_ratio"
        )

        revenue_cagr = latest_ratio.get(
            "revenue_cagr_5yr"
        )

    else:

        roe = company.get("roe_percentage")
        debt_equity = np.nan
        opm = np.nan
        pe = np.nan
        pb = np.nan
        revenue_cagr = np.nan

    fcf_conversion = np.nan
    cfo_label = "N/A"

    if latest_cf is not None:

        fcf_conversion = latest_cf.get(
            "fcf_conversion_pct"
        )

        cfo_label = latest_cf.get(
            "cfo_quality_label",
            "N/A"
        )

    # --------------------------------------------------------
    # KPI TABLE
    # --------------------------------------------------------

    kpi_data = [
        ["ROE", "D/E", "OPM"],
        [
            fmt(roe, "%"),
            fmt(debt_equity),
            fmt(opm, "%"),
        ],
        ["P/E", "P/B", "FCF Conversion"],
        [
            fmt(pe),
            fmt(pb),
            fmt(fcf_conversion, "%"),
        ],
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[
            55 * mm,
            55 * mm,
            55 * mm
        ]
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
                "BACKGROUND",
                (0, 2),
                (-1, 2),
                colors.HexColor("#0B1F3A")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, -1),
                colors.black
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "TEXTCOLOR",
                (0, 2),
                (-1, 2),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                colors.grey
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, 1),
                [
                    colors.white,
                    colors.HexColor("#F4F6F8")
                ]
            ),
            (
                "ROWBACKGROUNDS",
                (0, 3),
                (-1, 3),
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
    # TREND TABLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Key Trend Indicators",
            heading_style
        )
    )

    trend_data = [
        ["Metric", "Trend", "Latest"],
    ]

    trend_columns = [
        ("ROE", "roe_percentage", "%"),
        ("Revenue CAGR 5Y", "revenue_cagr_5yr", "%"),
        ("PAT CAGR 5Y", "pat_cagr_5yr", "%"),
        ("OPM", "opm_percentage", "%"),
        ("D/E", "debt_to_equity", ""),
    ]

    for label, column, suffix in trend_columns:

        if column in company_ratios.columns:

            trend = trend_arrow(
                company_ratios[column]
            )

            latest_value = (
                company_ratios[column].iloc[-1]
                if not company_ratios.empty
                else np.nan
            )

        else:

            trend = "→"
            latest_value = np.nan

        trend_data.append([
            label,
            trend,
            fmt(latest_value, suffix)
        ])

    trend_table = Table(
        trend_data,
        colWidths=[
            75 * mm,
            30 * mm,
            45 * mm
        ]
    )

    trend_table.setStyle(
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
                0.4,
                colors.grey
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER"
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

    story.append(trend_table)
    story.append(Spacer(1, 8 * mm))

    # --------------------------------------------------------
    # CASH FLOW INTELLIGENCE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Cash Flow Intelligence",
            heading_style
        )
    )

    cf_data = [
        ["Metric", "Value"],
        [
            "CFO Quality",
            str(cfo_label)
        ],
        [
            "CapEx Intensity",
            fmt(
                latest_cf.get("capex_intensity_pct")
                if latest_cf is not None
                else np.nan,
                "%"
            )
        ],
        [
            "FCF CAGR 5Y",
            fmt(
                latest_cf.get("fcf_cagr_5yr")
                if latest_cf is not None
                else np.nan,
                "%"
            )
        ],
        [
            "Distress Flag",
            str(
                latest_cf.get("distress_flag")
                if latest_cf is not None
                else "N/A"
            )
        ],
        [
            "Deleveraging Flag",
            str(
                latest_cf.get("deleveraging_flag")
                if latest_cf is not None
                else "N/A"
            )
        ],
        [
            "Capital Allocation",
            str(
                latest_cf.get("capital_allocation_label")
                if latest_cf is not None
                else "N/A"
            )
        ],
    ]

    cf_table = Table(
        cf_data,
        colWidths=[
            75 * mm,
            75 * mm
        ]
    )

    cf_table.setStyle(
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
                0.4,
                colors.grey
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

    story.append(cf_table)

    return story


# ============================================================
# BUILD PORTFOLIO PDF
# ============================================================

def main():

    print("=" * 60)
    print("DAY 35 - PORTFOLIO SUMMARY")
    print("=" * 60)

    companies, ratios, cashflow = load_data()

    ratios = prepare_ratios(ratios)

    companies = companies.sort_values(
        "company_id"
    ).reset_index(drop=True)

    print(
        f"Companies found: {len(companies)}"
    )

    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    generated_pages = 0

    for index, (_, company) in enumerate(
        companies.iterrows()
    ):

        story.extend(
            create_company_page(
                company,
                ratios,
                cashflow
            )
        )

        generated_pages += 1

        if index < len(companies) - 1:
            story.append(PageBreak())

        print(
            f"Added: {company['company_id']}"
        )

    doc.build(story)

    print()
    print("=" * 60)
    print("PORTFOLIO SUMMARY COMPLETE")
    print("=" * 60)
    print(f"Companies : {len(companies)}")
    print(f"Pages     : {generated_pages}")
    print(f"Output    : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()