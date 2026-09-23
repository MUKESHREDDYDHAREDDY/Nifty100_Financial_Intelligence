"""
Day 33 - Company Tearsheet Generator

Generates a 2-page PDF tearsheet for one company.

Page 1:
- Company / ticker header
- 6 KPI tiles
- Revenue and Net Profit chart
- ROE / ROCE trend

Page 2:
- Balance Sheet composition
- Cash Flow waterfall
- Pros
- Cons
- Capital Allocation badge
"""

import os
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# PATHS
# ============================================================

DB_PATH = "nifty100.db"

OUTPUT_DIR = "reports/tearsheets"
CHART_DIR = "reports/tearsheets/charts"

VALUATION_FILE = "output/valuation_summary.xlsx"
PROS_CONS_FILE = "output/pros_cons_generated.csv"
CASHFLOW_FILE = "output/cashflow_intelligence.xlsx"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)


# ============================================================
# REPORT STYLES
# ============================================================

NAVY = colors.HexColor("#17365D")
LIGHT_BLUE = colors.HexColor("#D9EAF7")
LIGHT_GREEN = colors.HexColor("#E2F0D9")
LIGHT_RED = colors.HexColor("#FCE4D6")
DARK_GREY = colors.HexColor("#404040")


styles = getSampleStyleSheet()

styles.add(
    ParagraphStyle(
        name="SmallText",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        textColor=DARK_GREY,
    )
)

styles.add(
    ParagraphStyle(
        name="BulletText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        leftIndent=10,
        firstLineIndent=-6,
    )
)

styles.add(
    ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        textColor=NAVY,
        spaceAfter=5,
    )
)


# ============================================================
# DATA HELPERS
# ============================================================


def clean_year(year):
    """Extract numeric year from strings such as Mar 2024."""

    if pd.isna(year):
        return None

    text = str(year).strip()

    if text.upper() == "TTM":
        return None

    import re

    match = re.search(r"(19|20)\d{2}", text)

    if match:
        return int(match.group())

    return None


def prepare_df(df):
    """Remove TTM rows, sort chronologically and handle duplicates."""

    df = df.copy()

    df["year_num"] = df["year"].apply(clean_year)

    df = df[df["year_num"].notna()].copy()

    if "id" in df.columns:
        df = df.sort_values(
            ["company_id", "year_num", "id"]
        )
    else:
        df = df.sort_values(
            ["company_id", "year_num"]
        )

    df = df.drop_duplicates(
        subset=["company_id", "year_num"],
        keep="last",
    )

    return df


def safe_value(value):
    """Convert missing numeric values to None."""

    if pd.isna(value):
        return None

    return float(value)


# ============================================================
# CHART GENERATION
# ============================================================


def create_revenue_profit_chart(pl, company_id):
    """Create Revenue / Net Profit bar chart."""

    data = (
        pl[
            pl["company_id"] == company_id
        ]
        .sort_values("year_num")
        .tail(10)
        .copy()
    )

    if data.empty:
        return None

    path = os.path.join(
        CHART_DIR,
        f"{company_id}_revenue_profit.png",
    )

    x = np.arange(len(data))
    width = 0.38

    fig, ax = plt.subplots(figsize=(7.0, 2.5))

    ax.bar(
        x - width / 2,
        data["sales"],
        width,
        label="Revenue",
    )

    ax.bar(
        x + width / 2,
        data["net_profit"],
        width,
        label="Net Profit",
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        data["year"].astype(str),
        rotation=45,
        ha="right",
        fontsize=7,
    )

    # Dynamic title:
    # 10 years for normal companies,
    # actual available periods for companies such as JIOFIN.
    period_count = len(data)

    if period_count >= 10:
        chart_title = "10-Year Revenue and Net Profit"
    else:
        chart_title = (
            f"Revenue and Net Profit ({period_count} periods)"
        )

    ax.set_title(
        chart_title,
        fontsize=10,
    )

    ax.legend(fontsize=7)

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def create_roe_roce_chart(
    pl,
    company_id,
    company_row,
):
    """Create ROE / ROCE trend chart."""

    data = (
        pl[
            pl["company_id"] == company_id
        ]
        .sort_values("year_num")
        .tail(10)
        .copy()
    )

    if data.empty:
        return None

    # Use company-level ROE/ROCE as fallback/current values.
    roe_value = safe_value(
        company_row["roe_percentage"]
    )

    roce_value = safe_value(
        company_row["roce_percentage"]
    )

    data["roe"] = roe_value
    data["roce"] = roce_value

    path = os.path.join(
        CHART_DIR,
        f"{company_id}_roe_roce.png",
    )

    fig, ax = plt.subplots(figsize=(7.0, 2.3))

    ax.plot(
        data["year"],
        data["roe"],
        marker="o",
        label="ROE",
    )

    ax.plot(
        data["year"],
        data["roce"],
        marker="o",
        label="ROCE",
    )

    ax.set_title(
        "ROE / ROCE",
        fontsize=10,
    )

    ax.set_ylabel("%")

    ax.tick_params(
        axis="x",
        rotation=45,
        labelsize=7,
    )

    ax.legend(fontsize=7)

    ax.grid(
        alpha=0.2,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def create_balance_sheet_chart(
    bs,
    company_id,
):
    """Create stacked balance sheet composition chart."""

    data = (
        bs[
            bs["company_id"] == company_id
        ]
        .sort_values("year_num")
        .tail(10)
        .copy()
    )

    if data.empty:
        return None

    path = os.path.join(
        CHART_DIR,
        f"{company_id}_balance_sheet.png",
    )

    borrowings = data["borrowings"].fillna(0)
    reserves = data["reserves"].fillna(0)

    other_liabilities = data[
        "other_liabilities"
    ].fillna(0)

    fig, ax = plt.subplots(figsize=(7.0, 2.5))

    ax.bar(
        data["year"],
        borrowings,
        label="Borrowings",
    )

    ax.bar(
        data["year"],
        reserves,
        bottom=borrowings,
        label="Reserves",
    )

    ax.bar(
        data["year"],
        other_liabilities,
        bottom=borrowings + reserves,
        label="Other Liabilities",
    )

    ax.set_title(
        "Balance Sheet Composition",
        fontsize=10,
    )

    ax.tick_params(
        axis="x",
        rotation=45,
        labelsize=7,
    )

    ax.legend(fontsize=7)

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


def create_cashflow_chart(
    cf,
    company_id,
):
    """Create latest-year cash flow chart."""

    data = (
        cf[
            cf["company_id"] == company_id
        ]
        .sort_values("year_num")
    )

    if data.empty:
        return None

    latest = data.iloc[-1]

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash",
    ]

    values = [
        latest["operating_activity"],
        latest["investing_activity"],
        latest["financing_activity"],
        latest["net_cash_flow"],
    ]

    path = os.path.join(
        CHART_DIR,
        f"{company_id}_cashflow.png",
    )

    fig, ax = plt.subplots(figsize=(7.0, 2.5))

    ax.bar(
        labels,
        values,
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_title(
        f"Cash Flow - {latest['year']}",
        fontsize=10,
    )

    ax.set_ylabel("₹ crore")

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    return path


# ============================================================
# KPI DATA
# ============================================================


def get_kpis(
    company_id,
    ratios,
    valuation,
    cashflow_intel,
):
    """Return six headline KPIs."""

    ratio = (
        ratios[
            ratios["company_id"] == company_id
        ]
        .sort_values("year_num")
    )

    latest_ratio = (
        ratio.iloc[-1]
        if not ratio.empty
        else None
    )

    val = valuation[
        valuation["company_id"] == company_id
    ]

    val_row = (
        val.iloc[0]
        if not val.empty
        else None
    )

    cf = cashflow_intel[
        cashflow_intel["company_id"] == company_id
    ]

    cf_row = (
        cf.iloc[0]
        if not cf.empty
        else None
    )

    kpis = []

    if latest_ratio is not None:
        kpis.append(
            (
                "ROE",
                latest_ratio.get(
                    "return_on_equity_pct"
                ),
            )
        )

        kpis.append(
            (
                "D/E",
                latest_ratio.get(
                    "debt_to_equity"
                ),
            )
        )

        kpis.append(
            (
                "OPM",
                latest_ratio.get(
                    "operating_profit_margin_pct"
                ),
            )
        )

    else:
        kpis.extend(
            [
                ("ROE", None),
                ("D/E", None),
                ("OPM", None),
            ]
        )

    if val_row is not None:
        kpis.append(
            (
                "P/E",
                val_row.get("P/E"),
            )
        )

        kpis.append(
            (
                "P/B",
                val_row.get("P/B"),
            )
        )

    else:
        kpis.extend(
            [
                ("P/E", None),
                ("P/B", None),
            ]
        )

    if cf_row is not None:
        kpis.append(
            (
                "FCF Conversion",
                cf_row.get(
                    "fcf_conversion_pct"
                ),
            )
        )

    else:
        kpis.append(
            ("FCF Conversion", None)
        )

    return kpis[:6]


# ============================================================
# PDF GENERATOR
# ============================================================


def generate_tearsheet(
    company_id,
    company_row,
    pl,
    bs,
    cf,
    ratios,
    valuation,
    pros_cons,
    cashflow_intel,
):
    """Generate one 2-page company tearsheet."""

    company_name = company_row["company_name"]
    sector = company_row["broad_sector"]

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{company_id}_tearsheet.pdf",
    )

    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    story = []

    # ========================================================
    # PAGE 1 HEADER
    # ========================================================

    header_data = [
        [
            Paragraph(
                f"<b>{company_name}</b><br/>"
                f"<font size='9'>{company_id} | {sector}</font>",
                ParagraphStyle(
                    "Header",
                    fontSize=18,
                    leading=21,
                    textColor=colors.white,
                ),
            )
        ]
    ]

    header = Table(
        header_data,
        colWidths=[185 * mm],
        rowHeights=[22 * mm],
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 5 * mm))

    # ========================================================
    # KPI TILES
    # ========================================================

    kpis = get_kpis(
        company_id,
        ratios,
        valuation,
        cashflow_intel,
    )

    tile_data = []
    row = []

    for label, value in kpis:

        if value is None or pd.isna(value):
            display = "N/A"
        else:
            display = f"{value:.2f}"

        tile = Table(
            [
                [
                    Paragraph(
                        f"<b>{label}</b><br/>"
                        f"<font size='14'>{display}</font>",
                        styles["SmallText"],
                    )
                ]
            ],
            colWidths=[58 * mm],
            rowHeights=[20 * mm],
        )

        tile.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        LIGHT_BLUE,
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        NAVY,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                ]
            )
        )

        row.append(tile)

        if len(row) == 3:
            tile_data.append(row)
            row = []

    if row:
        while len(row) < 3:
            row.append("")

        tile_data.append(row)

    kpi_table = Table(
        tile_data,
        colWidths=[61 * mm] * 3,
        hAlign="CENTER",
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    story.append(kpi_table)
    story.append(Spacer(1, 3 * mm))

    # ========================================================
    # CHARTS
    # ========================================================

    revenue_chart = create_revenue_profit_chart(
        pl,
        company_id,
    )

    if revenue_chart:
        story.append(
            Image(
                revenue_chart,
                width=175 * mm,
                height=63 * mm,
            )
        )

    roe_chart = create_roe_roce_chart(
        pl,
        company_id,
        company_row,
    )

    if roe_chart:
        story.append(
            Image(
                roe_chart,
                width=175 * mm,
                height=55 * mm,
            )
        )

    # ========================================================
    # PAGE 2
    # ========================================================

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Financial Position & Cash Flow",
            styles["SectionTitle"],
        )
    )

    bs_chart = create_balance_sheet_chart(
        bs,
        company_id,
    )

    if bs_chart:
        story.append(
            Image(
                bs_chart,
                width=175 * mm,
                height=60 * mm,
            )
        )

    cf_chart = create_cashflow_chart(
        cf,
        company_id,
    )

    if cf_chart:
        story.append(
            Image(
                cf_chart,
                width=175 * mm,
                height=55 * mm,
            )
        )

    # ========================================================
    # PROS AND CONS
    # ========================================================

    company_pc = pros_cons[
        pros_cons["company_id"] == company_id
    ]

    pros = company_pc[
        company_pc["type"].str.lower() == "pro"
    ].sort_values(
        "confidence_pct",
        ascending=False,
    )

    cons = company_pc[
        company_pc["type"].str.lower() == "con"
    ].sort_values(
        "confidence_pct",
        ascending=False,
    )

    pro_text = "<b>Pros</b><br/>"

    for _, r in pros.head(6).iterrows():
        text = str(r["text"])
        confidence = r["confidence_pct"]

        pro_text += (
            f"• {text} "
            f"<font size='7'>({confidence:.0f}%)</font><br/>"
        )

    if len(pros) == 0:
        pro_text += (
            "• No generated Pros available.<br/>"
        )

    con_text = "<b>Cons</b><br/>"

    for _, r in cons.head(6).iterrows():
        text = str(r["text"])
        confidence = r["confidence_pct"]

        con_text += (
            f"• {text} "
            f"<font size='7'>({confidence:.0f}%)</font><br/>"
        )

    if len(cons) == 0:
        con_text += (
            "• No generated Cons available.<br/>"
        )

    pc_table = Table(
        [
            [
                Paragraph(
                    pro_text,
                    styles["SmallText"],
                ),
                Paragraph(
                    con_text,
                    styles["SmallText"],
                ),
            ]
        ],
        colWidths=[90 * mm, 90 * mm],
    )

    pc_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GREEN,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    LIGHT_RED,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(pc_table)
    story.append(Spacer(1, 4 * mm))

    # ========================================================
    # CAPITAL ALLOCATION
    # ========================================================

    cf_row = cashflow_intel[
        cashflow_intel["company_id"] == company_id
    ]

    if not cf_row.empty:
        pattern = cf_row.iloc[0].get(
            "capital_allocation_label"
        )
    else:
        pattern = None

    if pattern is None or pd.isna(pattern):
        pattern = "Unavailable"

    allocation_table = Table(
        [
            [
                Paragraph(
                    f"<b>Capital Allocation Pattern</b><br/>"
                    f"<font size='12'>{pattern}</font>",
                    styles["SmallText"],
                )
            ]
        ],
        colWidths=[180 * mm],
        rowHeights=[18 * mm],
    )

    allocation_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    NAVY,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(allocation_table)

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(story)

    return output_file


# ============================================================
# TEST GENERATOR
# ============================================================


def main():

    print("=" * 60)
    print("DAY 33 - COMPANY TEARSHEET GENERATOR")
    print("=" * 60)

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
        conn,
    )

    pl = pd.read_sql_query(
        """
        SELECT *
        FROM profitandloss
        """,
        conn,
    )

    bs = pd.read_sql_query(
        """
        SELECT *
        FROM balancesheet
        """,
        conn,
    )

    cf = pd.read_sql_query(
        """
        SELECT *
        FROM cashflow
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        """,
        conn,
    )

    conn.close()

    pl = prepare_df(pl)
    bs = prepare_df(bs)
    cf = prepare_df(cf)
    ratios = prepare_df(ratios)

    valuation = pd.read_excel(
        VALUATION_FILE
    )

    pros_cons = pd.read_csv(
        PROS_CONS_FILE
    )

    cashflow_intel = pd.read_excel(
        CASHFLOW_FILE
    )

    # ========================================================
    # TEST COMPANIES
    # ========================================================

    test_companies = [
        "TCS",
        "HDFCBANK",
        "RELIANCE",
        "SUNPHARMA",
        "TATASTEEL",
        "JIOFIN",
    ]

    print()
    print("Generating test tearsheets...")

    generated = []

    for company_id in test_companies:

        company_match = companies[
            companies["company_id"] == company_id
        ]

        if company_match.empty:
            print(
                f"SKIP {company_id}: company not found"
            )
            continue

        company_row = company_match.iloc[0]

        pl_company = pl[
            pl["company_id"] == company_id
        ]

        bs_company = bs[
            bs["company_id"] == company_id
        ]

        cf_company = cf[
            cf["company_id"] == company_id
        ]

        if len(pl_company) < 2:
            print(
        f"SKIP {company_id}: insufficient P&L data"
        )
            continue

        output_file = generate_tearsheet(
            company_id,
            company_row,
            pl_company,
            bs_company,
            cf_company,
            ratios,
            valuation,
            pros_cons,
            cashflow_intel,
        )

        generated.append(output_file)

        print(
            f"Generated: {output_file}"
        )

    print()
    print(
        "Test tearsheets generated:",
        len(generated),
    )

    print("=" * 60)


if __name__ == "__main__":
    main()