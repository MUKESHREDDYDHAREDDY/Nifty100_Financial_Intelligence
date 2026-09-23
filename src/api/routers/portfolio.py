"""
Portfolio API endpoints.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.config import DB_PATH

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


@router.get("")
def get_portfolio():
    """
    Return portfolio summary for all companies.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.broad_sector,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct,
            fr.debt_to_equity,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.operating_profit_margin_pct,
            vs."P/E",
            vs."P/B",
            vs."EV/EBITDA",
            vs.flag AS valuation_flag
        FROM companies c

        LEFT JOIN financial_ratios fr
            ON c.id = fr.company_id
            AND fr.year = 'Mar 2024'

        LEFT JOIN valuation_summary vs
            ON c.id = vs.company_id

        ORDER BY c.id
    """

    try:
        rows = conn.execute(query).fetchall()

    except sqlite3.Error as exc:
        conn.close()

        raise HTTPException(
            status_code=500,
            detail=f"Portfolio data is unavailable: {exc}",
        )

    conn.close()

    companies = [dict(row) for row in rows]

    return {
        "count": len(companies),
        "portfolio": companies,
    }
