"""
Valuation API endpoints.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.config import DB_PATH

router = APIRouter(prefix="/valuation", tags=["Valuation"])


@router.get("")
def get_valuation():
    """
    Return valuation summary for all companies.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            company_id,
            company_name,
            sector,
            "P/E",
            "P/B",
            "EV/EBITDA",
            FCF_yield_pct,
            "5yr_median_PE",
            PE_vs_sector_median_pct,
            flag
        FROM valuation_summary
        ORDER BY company_id
    """

    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error:
        conn.close()
        raise HTTPException(
            status_code=500,
            detail="Valuation data is unavailable",
        )

    conn.close()

    return {
        "count": len(rows),
        "valuations": [dict(row) for row in rows],
    }


@router.get("/{ticker}")
def get_company_valuation(ticker: str):
    """
    Return valuation information for a single company.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            company_id,
            company_name,
            sector,
            "P/E",
            "P/B",
            "EV/EBITDA",
            FCF_yield_pct,
            "5yr_median_PE",
            PE_vs_sector_median_pct,
            flag
        FROM valuation_summary
        WHERE company_id = ?
    """

    row = conn.execute(
        query,
        (ticker.upper(),),
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Valuation data not found",
        )

    return dict(row)
