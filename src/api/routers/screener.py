"""
Screener API endpoints.
"""

import sqlite3

from fastapi import APIRouter, Query

from src.api.config import DB_PATH

router = APIRouter(prefix="/screener", tags=["Screener"])


@router.get("")
def screen_companies(
    min_roe: float | None = Query(None),
    max_de: float | None = Query(None),
    min_fcf: float | None = Query(None),
    sector: str | None = Query(None),
    min_rev_cagr_5yr: float | None = Query(None),
    min_pat_cagr_5yr: float | None = Query(None),
    max_pe: float | None = Query(None),
):
    """
    Screen companies using financial and valuation filters.
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
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            mc.pe_ratio
        FROM companies c
        LEFT JOIN financial_ratios fr
            ON c.id = fr.company_id
            AND fr.year = 'Mar 2024'
        LEFT JOIN market_cap mc
            ON c.id = mc.company_id
            AND mc.year = 'Mar 2024'
        WHERE 1 = 1
    """

    params = []

    if min_roe is not None:
        query += " AND c.roe_percentage >= ?"
        params.append(min_roe)

    if max_de is not None:
        query += " AND fr.debt_to_equity <= ?"
        params.append(max_de)

    if min_fcf is not None:
        query += " AND fr.free_cash_flow_cr >= ?"
        params.append(min_fcf)

    if sector:
        query += " AND c.broad_sector = ?"
        params.append(sector)

    if min_rev_cagr_5yr is not None:
        query += " AND fr.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)

    if min_pat_cagr_5yr is not None:
        query += " AND fr.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)

    if max_pe is not None:
        query += " AND mc.pe_ratio <= ?"
        params.append(max_pe)

    query += " ORDER BY c.id"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    companies = [dict(row) for row in rows]

    return {
        "count": len(companies),
        "filters": {
            "min_roe": min_roe,
            "max_de": max_de,
            "min_fcf": min_fcf,
            "sector": sector,
            "min_rev_cagr_5yr": min_rev_cagr_5yr,
            "min_pat_cagr_5yr": min_pat_cagr_5yr,
            "max_pe": max_pe,
        },
        "companies": companies,
    }
