"""
Day 15 - Screener Filter Engine

Epic 03 - Financial Screener

Loads financial ratios from SQLite and joins:
- companies
- market_cap
- profitandloss

Supports 15 screener metrics.

Special rules:
- D/E filter excludes Financials.
- Debt Free companies pass every ICR minimum.
- Results are sorted by composite quality score.
"""

from pathlib import Path
from typing import Optional

import sqlite3

import pandas as pd
import yaml


DB_PATH = Path("nifty100.db")
CONFIG_PATH = Path("config/screener_config.yaml")


def load_config(
    config_path: Path = CONFIG_PATH,
) -> dict:
    """Load screener configuration."""

    with open(
        config_path,
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file) or {}


def load_screener_data(
    conn: sqlite3.Connection,
) -> pd.DataFrame:
    """
    Load financial ratio data and join
    company, market and P&L information.
    """

    query = """
        SELECT
            f.id,
            f.company_id,
            f.year,

            c.company_name,
            c.broad_sector,

            -- Financial ratios
            f.net_profit_margin_pct,
            f.operating_profit_margin_pct,
            f.return_on_equity_pct,
            f.debt_to_equity,
            f.interest_coverage,
            f.asset_turnover,
            f.free_cash_flow_cr,
            f.capex_cr,
            f.earnings_per_share,
            f.book_value_per_share,
            f.dividend_payout_ratio_pct,
            f.total_debt_cr,
            f.cash_from_operations_cr,

            f.revenue_cagr_5yr,
            f.pat_cagr_5yr,
            f.eps_cagr_5yr,

            f.composite_quality_score,

            -- Market data
            m.market_cap_crore,
            m.pe_ratio,
            m.pb_ratio,
            m.dividend_yield_pct,

            -- P&L data
            p.sales,
            p.net_profit,
            p.eps,
            p.opm_percentage

        FROM financial_ratios f

        JOIN companies c
            ON f.company_id = c.id

        LEFT JOIN market_cap m
        ON f.company_id = m.company_id
   AND (
        CASE
            WHEN f.year = 'TTM' THEN NULL
            ELSE SUBSTR(f.year, -4)
        END
       ) = m.year

        LEFT JOIN profitandloss p
            ON f.company_id = p.company_id
           AND f.year = p.year
    """

    return pd.read_sql_query(query, conn)


def apply_screener(
    df: pd.DataFrame,
    thresholds: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Apply screener threshold filters.

    Returns results sorted by composite
    quality score descending.
    """

    result = df.copy()

    if thresholds is None:
        thresholds = {}

    # --------------------------------------------------
    # ROE
    # --------------------------------------------------

    if thresholds.get("roe_min") is not None:
        result = result[
            result["return_on_equity_pct"]
            >= thresholds["roe_min"]
        ]

    # --------------------------------------------------
    # OPM
    # --------------------------------------------------

    if thresholds.get("opm_min") is not None:
        result = result[
            result["operating_profit_margin_pct"]
            >= thresholds["opm_min"]
        ]

    # --------------------------------------------------
    # D/E
    #
    # Financials are excluded from the D/E filter.
    # --------------------------------------------------

    if thresholds.get("de_max") is not None:

        non_financial = (
            result["broad_sector"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            != "financials"
        )

        result = result[
            non_financial
            & (
                result["debt_to_equity"]
                <= thresholds["de_max"]
            )
        ]

    # --------------------------------------------------
    # FCF
    # --------------------------------------------------

    if thresholds.get("fcf_min") is not None:
        result = result[
            result["free_cash_flow_cr"]
            >= thresholds["fcf_min"]
        ]

    # --------------------------------------------------
    # Revenue CAGR 5Y
    # --------------------------------------------------

    if thresholds.get("revenue_cagr_5yr_min") is not None:
        result = result[
            result["revenue_cagr_5yr"]
            >= thresholds["revenue_cagr_5yr_min"]
        ]

    # --------------------------------------------------
    # PAT CAGR 5Y
    # --------------------------------------------------

    if thresholds.get("pat_cagr_5yr_min") is not None:
        result = result[
            result["pat_cagr_5yr"]
            >= thresholds["pat_cagr_5yr_min"]
        ]

    # --------------------------------------------------
    # EPS CAGR 5Y
    # --------------------------------------------------

    if thresholds.get("eps_cagr_min") is not None:
        result = result[
            result["eps_cagr_5yr"]
            >= thresholds["eps_cagr_min"]
        ]

    # --------------------------------------------------
    # P/E
    # --------------------------------------------------

    if thresholds.get("pe_max") is not None:
        result = result[
            result["pe_ratio"]
            <= thresholds["pe_max"]
        ]

    # --------------------------------------------------
    # P/B
    # --------------------------------------------------

    if thresholds.get("pb_max") is not None:
        result = result[
            result["pb_ratio"]
            <= thresholds["pb_max"]
        ]

    # --------------------------------------------------
    # Dividend Yield
    # --------------------------------------------------

    if thresholds.get("dividend_yield_min") is not None:
        result = result[
            result["dividend_yield_pct"]
            >= thresholds["dividend_yield_min"]
        ]
    # --------------------------------------------------
    # Dividend Payout
    # --------------------------------------------------

    if thresholds.get("dividend_payout_max") is not None:
        result = result[
            result["dividend_payout_ratio_pct"]
            < thresholds["dividend_payout_max"]
        ]
    # --------------------------------------------------
    # ICR
    #
    # Debt Free = infinity
    # --------------------------------------------------

    if thresholds.get("icr_min") is not None:

        icr = result["interest_coverage"].copy()

        icr = icr.fillna(float("inf"))

        result = result[
            icr >= thresholds["icr_min"]
        ]

    # --------------------------------------------------
    # Market Cap
    # --------------------------------------------------

    if thresholds.get("market_cap_min") is not None:
        result = result[
            result["market_cap_crore"]
            >= thresholds["market_cap_min"]
        ]

    # --------------------------------------------------
    # Net Profit
    # --------------------------------------------------

    if thresholds.get("net_profit_min") is not None:
        result = result[
            result["net_profit"]
            >= thresholds["net_profit_min"]
        ]

    # --------------------------------------------------
    # Asset Turnover
    # --------------------------------------------------

    if thresholds.get("asset_turnover_min") is not None:
        result = result[
            result["asset_turnover"]
            >= thresholds["asset_turnover_min"]
        ]

    # --------------------------------------------------
    # Sales
    # --------------------------------------------------

    if thresholds.get("sales_min") is not None:
        result = result[
            result["sales"]
            >= thresholds["sales_min"]
        ]

    # --------------------------------------------------
    # Sort
    # --------------------------------------------------

    if "composite_quality_score" in result.columns:

        result = result.sort_values(
            by="composite_quality_score",
            ascending=False,
            na_position="last",
        )

    return result.reset_index(drop=True)

def normalize_metric(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """
    Winsorize a metric at P10/P90 and scale it to 0-100.
    """
    numeric = pd.to_numeric(series, errors="coerce")

    p10 = numeric.quantile(0.10)
    p90 = numeric.quantile(0.90)

    if pd.isna(p10) or pd.isna(p90) or p90 == p10:
        return pd.Series(50.0, index=series.index)

    clipped = numeric.clip(lower=p10, upper=p90)

    score = ((clipped - p10) / (p90 - p10)) * 100

    if not higher_is_better:
        score = 100 - score

    return score

def normalize_by_sector(
    df: pd.DataFrame,
    column: str,
    higher_is_better: bool = True,
) -> pd.Series:
    """
    Winsorize and normalize a metric separately within each broad sector.
    """
    return df.groupby("broad_sector")[column].transform(
        lambda s: normalize_metric(
            s,
            higher_is_better=higher_is_better,
        )
    )
def calculate_profitability_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the 0-100 sector-relative Profitability score.

    Weight:
    - ROE 15%
    - ROCE 10%
    - NPM 10%
    """
    roe_score = normalize_by_sector(
        df,
        "return_on_equity_pct",
        higher_is_better=True,
    )

    roce_score = normalize_by_sector(
        df,
        "roce",
        higher_is_better=True,
    )

    npm_score = normalize_by_sector(
        df,
        "net_profit_margin_pct",
        higher_is_better=True,
    )

    return (
        roe_score * (15 / 35)
        + roce_score * (10 / 35)
        + npm_score * (10 / 35)
    )

def calculate_cash_quality_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the 0-100 sector-relative Cash Quality score.

    Weight:
    - FCF CAGR 15%
    - CFO/PAT ratio 10%
    - FCF positive flag 5%
    """
    fcf_cagr_score = normalize_by_sector(
        df,
        "fcf_cagr_3yr",
        higher_is_better=True,
    )

    cfo_pat_score = normalize_by_sector(
        df,
        "cfo_pat_ratio",
        higher_is_better=True,
    )

    fcf_positive_score = df["fcf_positive_flag"] * 100

    return (
        fcf_cagr_score * (15 / 30)
        + cfo_pat_score * (10 / 30)
        + fcf_positive_score * (5 / 30)
    )

def calculate_growth_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the 0-100 sector-relative Growth score.

    Weight:
    - Revenue CAGR 5yr 10%
    - PAT CAGR 5yr 10%
    """
    revenue_score = normalize_by_sector(
        df,
        "revenue_cagr_5yr",
        higher_is_better=True,
    )

    pat_score = normalize_by_sector(
        df,
        "pat_cagr_5yr",
        higher_is_better=True,
    )

    return (
        revenue_score * 0.5
        + pat_score * 0.5
    )

def calculate_leverage_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the 0-100 sector-relative Leverage score.

    Weight:
    - D/E score 10%
    - Interest Coverage score 5%
    """
    de_score = normalize_by_sector(
        df,
        "debt_to_equity",
        higher_is_better=False,
    )

    icr_score = normalize_by_sector(
        df,
        "interest_coverage",
        higher_is_better=True,
    )

    return (
        de_score * (10 / 15)
        + icr_score * (5 / 15)
    )
def calculate_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the final sector-relative Composite Quality Score (0-100).

    Component weights:
    - Profitability: 35%
    - Cash Quality: 30%
    - Growth: 20%
    - Leverage: 15%

    Missing component scores are excluded and the remaining
    component weights are proportionally reweighted.
    """
    result = df.copy()

    result["profitability_score"] = calculate_profitability_score(result)
    result["cash_quality_score"] = calculate_cash_quality_score(result)
    result["growth_score"] = calculate_growth_score(result)
    result["leverage_score"] = calculate_leverage_score(result)

    component_weights = {
        "profitability_score": 35.0,
        "cash_quality_score": 30.0,
        "growth_score": 20.0,
        "leverage_score": 15.0,
    }

    weighted_sum = pd.Series(0.0, index=result.index)
    available_weight = pd.Series(0.0, index=result.index)

    for column, weight in component_weights.items():
        valid = result[column].notna()
        weighted_sum.loc[valid] += result.loc[valid, column] * weight
        available_weight.loc[valid] += weight

    result["composite_quality_score"] = (
        weighted_sum / available_weight
    )

    result["composite_quality_score"] = (
        result["composite_quality_score"].clip(0, 100)
    )

    return result

def run_preset(
    preset_name: str,
    db_path: Path = DB_PATH,
    config_path: Path = CONFIG_PATH,
) -> pd.DataFrame:
    """
    Run one named screener preset from the YAML configuration.
    """

    config = load_config(config_path)

    presets = config.get("presets", {})

    if preset_name not in presets:
        raise ValueError(
            f"Unknown preset: {preset_name}"
        )

    thresholds = presets[preset_name]

    conn = sqlite3.connect(db_path)

    try:
        df = load_screener_data(conn)
    finally:
        conn.close()

        # Use the latest annual record for each company.
    # Exclude TTM so presets use consistent annual financial data.
    annual = df[df["year"] != "TTM"].copy()
    annual = (
        annual
        .sort_values("year")
        .groupby("company_id", sort=False)
        .tail(1)
    )
        # Calculate 3-year FCF CAGR from Mar 2021 to Mar 2024.
    conn = sqlite3.connect(db_path)
    try:
        fcf_history = pd.read_sql_query(
            """
            SELECT company_id, year, free_cash_flow_cr
            FROM financial_ratios
            WHERE year IN ('Mar 2021', 'Mar 2024')
            """,
            conn,
        )
    finally:
        conn.close()

    fcf_pivot = (
        fcf_history.pivot_table(
            index="company_id",
            columns="year",
            values="free_cash_flow_cr",
            aggfunc="first",
        )
        .dropna()
    )

    # CAGR is meaningful only when both starting and ending FCF are positive.
    fcf_valid = fcf_pivot[
        (fcf_pivot["Mar 2021"] > 0)
        & (fcf_pivot["Mar 2024"] > 0)
    ].copy()

    fcf_valid["fcf_cagr_3yr"] = (
        (fcf_valid["Mar 2024"] / fcf_valid["Mar 2021"]) ** (1 / 3) - 1
    ) * 100

    annual["fcf_cagr_3yr"] = annual["company_id"].map(
        fcf_valid["fcf_cagr_3yr"]
    )
    annual["cfo_pat_ratio"] = (
    annual["cash_from_operations_cr"]
    / annual["net_profit"].replace(0, float("nan"))
    )
    # FCF positive flag for the latest annual year.
    annual["fcf_positive_flag"] = (
        annual["free_cash_flow_cr"] > 0
    ).astype(int)
    # Calculate ROCE for the latest annual year.
    conn = sqlite3.connect(db_path)
    try:
        roce_pnl = pd.read_sql_query(
            """
            SELECT company_id, year, operating_profit
            FROM profitandloss
            """,
            conn,
        )

        roce_bs = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                equity_capital,
                reserves,
                borrowings
            FROM balancesheet
            """,
            conn,
        )
    finally:
        conn.close()
        roce_pnl = (
        roce_pnl[roce_pnl["year"] == "Mar 2024"]
        .drop_duplicates(subset=["company_id", "year"], keep="first")
        .copy()
    )

    roce_bs = (
        roce_bs[roce_bs["year"] == "Mar 2024"]
        .drop_duplicates(subset=["company_id", "year"], keep="first")
        .copy()
    )

    roce_data = roce_pnl.merge(
        roce_bs,
        on=["company_id", "year"],
        how="inner",
    )

    roce_data["capital_employed"] = (
        roce_data["equity_capital"]
        + roce_data["reserves"]
        + roce_data["borrowings"]
    )

    roce_data["roce"] = (
        roce_data["operating_profit"]
        / roce_data["capital_employed"].replace(0, float("nan"))
    ) * 100

    annual["roce"] = annual["company_id"].map(
        roce_data.set_index("company_id")["roce"]
    )

    # Special logic for Turnaround Watch
    if preset_name == "turnaround_watch":
        conn = sqlite3.connect(db_path)
        try:
            pnl = pd.read_sql_query(
                """
                SELECT company_id, year, sales
                FROM profitandloss
                WHERE year IN ('Mar 2021', 'Mar 2024')
                """,
                conn,
            )

            de = pd.read_sql_query(
                """
                SELECT company_id, year, debt_to_equity
                FROM financial_ratios
                WHERE year IN ('Mar 2022', 'Mar 2023', 'Mar 2024')
                """,
                conn,
            )
        finally:
            conn.close()

        # Calculate 3-year Revenue CAGR
        sales = (
            pnl.pivot_table(
                index="company_id",
                columns="year",
                values="sales",
                aggfunc="first",
            )
            .dropna()
        )

        sales["revenue_cagr_3yr"] = (
            (sales["Mar 2024"] / sales["Mar 2021"]) ** (1 / 3) - 1
        ) * 100

        # Check D/E declined for both years
        de_pivot = (
            de.pivot_table(
                index="company_id",
                columns="year",
                values="debt_to_equity",
                aggfunc="first",
            )
            .dropna()
        )

        declining_de = de_pivot[
            (de_pivot["Mar 2023"] < de_pivot["Mar 2022"])
            & (de_pivot["Mar 2024"] < de_pivot["Mar 2023"])
        ].index

        # Add 3-year CAGR to latest annual records
        annual["revenue_cagr_3yr"] = annual["company_id"].map(
            sales["revenue_cagr_3yr"]
        )

        # Keep only companies with declining D/E
        annual = annual[annual["company_id"].isin(declining_de)]

        # Turnaround Watch: 3-year Revenue CAGR > 10%
        # and positive latest-year FCF
        annual = annual[
            (annual["revenue_cagr_3yr"] > thresholds.get("revenue_cagr_3yr_min", 10))
            & (annual["free_cash_flow_cr"] > thresholds.get("fcf_min", 0))
        ]
        result = annual.copy()
        result = calculate_composite_score(result)
        return result.sort_values(
        by="composite_quality_score",
        ascending=False,
        na_position="last",
        ).reset_index(drop=True)
    result = apply_screener(annual, thresholds)
    result = calculate_composite_score(result)
    return result.sort_values(
    by="composite_quality_score",
    ascending=False,
    na_position="last",
    ).reset_index(drop=True)

def run_screener(
    thresholds: Optional[dict] = None,
    db_path: Path = DB_PATH,
    config_path: Path = CONFIG_PATH,
) -> pd.DataFrame:
    """Run screener using SQLite and YAML configuration."""

    config = load_config(config_path)

    if thresholds is None:
        thresholds = config.get(
            "filters",
            {},
        )

    conn = sqlite3.connect(db_path)

    try:

        df = load_screener_data(conn)

    finally:

        conn.close()

    return apply_screener(
        df,
        thresholds,
    )


if __name__ == "__main__":

    result = run_screener()

    print("=" * 70)
    print("DAY 15 - SCREENER FILTER ENGINE")
    print("=" * 70)

    print(
        f"Rows returned: {len(result)}"
    )

    print(
        f"Companies returned: "
        f"{result['company_id'].nunique()}"
    )

    print()

    columns = [
        "company_id",
        "year",
        "company_name",
        "broad_sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "market_cap_crore",
        "composite_quality_score",
    ]

    available = [
        column
        for column in columns
        if column in result.columns
    ]

    if result.empty:
        print("No results.")

    else:
        print(
            result[available]
            .head(20)
            .to_string(index=False)
        )
def export_screener_output(
    db_path: Path = DB_PATH,
    config_path: Path = CONFIG_PATH,
    output_path: Path = Path("output/screener_output.xlsx"),
) -> None:
    """
    Export all six preset screener results to one Excel workbook.
    """

    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment

    output_path.parent.mkdir(parents=True, exist_ok=True)

    presets = [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ]

    preset_labels = {
        "quality_compounder": "Quality Compounder",
        "value_pick": "Value Pick",
        "growth_accelerator": "Growth Accelerator",
        "dividend_champion": "Dividend Champion",
        "debt_free_blue_chip": "Debt-Free Blue Chip",
        "turnaround_watch": "Turnaround Watch",
    }

    kpi_columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "return_on_equity_pct",
        "roce",
        "net_profit_margin_pct",
        "free_cash_flow_cr",
        "fcf_cagr_3yr",
        "cash_from_operations_cr",
        "cfo_pat_ratio",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "composite_quality_score",
    ]

    workbook = Workbook()

    # Remove the default sheet.
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    for preset in presets:
        result = run_preset(
            preset,
            db_path=db_path,
            config_path=config_path,
        )

        available_columns = [
            column for column in kpi_columns
            if column in result.columns
        ]

        export_df = result[available_columns].copy()

        sheet_name = preset_labels[preset][:31]
        worksheet = workbook.create_sheet(title=sheet_name)

        # Write headers.
        for column_index, column_name in enumerate(
            export_df.columns,
            start=1,
        ):
            cell = worksheet.cell(
                row=1,
                column=column_index,
                value=column_name,
            )
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Write data.
        for row_index, row in enumerate(
            export_df.itertuples(index=False),
            start=2,
        ):
            for column_index, value in enumerate(
                row,
                start=1,
            ):
                worksheet.cell(
                    row=row_index,
                    column=column_index,
                    value=value,
                )

        # Freeze header row.
        worksheet.freeze_panes = "A2"

        # Add autofilter.
        worksheet.auto_filter.ref = worksheet.dimensions

        # Reasonable column widths.
        for column_cells in worksheet.columns:
            column_letter = column_cells[0].column_letter
            worksheet.column_dimensions[column_letter].width = 18

        # Highlight composite score column.
        if "composite_quality_score" in export_df.columns:
            score_column = (
                list(export_df.columns).index(
                    "composite_quality_score"
                )
                + 1
            )

            for row_index in range(2, worksheet.max_row + 1):
                cell = worksheet.cell(
                    row=row_index,
                    column=score_column,
                )

                if cell.value is not None:
                    cell.number_format = "0.00"

        # Add preset threshold coloring.
        thresholds = load_config(config_path).get(
            "presets",
            {},
        ).get(preset, {})

        column_map = {
            "roe_min": "return_on_equity_pct",
            "opm_min": "operating_profit_margin_pct",
            "de_max": "debt_to_equity",
            "fcf_min": "free_cash_flow_cr",
            "revenue_cagr_5yr_min": "revenue_cagr_5yr",
            "pat_cagr_5yr_min": "pat_cagr_5yr",
            "eps_cagr_min": "eps_cagr_5yr",
            "pe_max": "pe_ratio",
            "pb_max": "pb_ratio",
            "dividend_yield_min": "dividend_yield_pct",
            "dividend_payout_max": "dividend_payout_ratio_pct",
            "icr_min": "interest_coverage",
            "market_cap_min": "market_cap_crore",
            "net_profit_min": "net_profit",
            "asset_turnover_min": "asset_turnover",
            "sales_min": "sales",
        }

        green_fill = PatternFill(
            fill_type="solid",
            fgColor="C6EFCE",
        )

        red_fill = PatternFill(
            fill_type="solid",
            fgColor="FFC7CE",
        )

        for threshold_name, threshold_value in thresholds.items():

            if threshold_value is None:
                continue

            column_name = column_map.get(threshold_name)

            if column_name not in export_df.columns:
                continue

            column_index = (
                list(export_df.columns).index(column_name)
                + 1
            )

            for row_index in range(2, worksheet.max_row + 1):
                cell = worksheet.cell(
                    row=row_index,
                    column=column_index,
                )

                if cell.value is None:
                    continue

                try:
                    numeric_value = float(cell.value)
                except (TypeError, ValueError):
                    continue

                if threshold_name.endswith("_min"):
                    passes = numeric_value >= threshold_value
                elif threshold_name.endswith("_max"):
                    passes = numeric_value <= threshold_value
                else:
                    passes = True

                cell.fill = (
                    green_fill if passes else red_fill
                )

    workbook.save(output_path)