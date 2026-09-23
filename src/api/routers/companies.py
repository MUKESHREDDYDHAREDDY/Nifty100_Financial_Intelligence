"""
Companies API router.
"""

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from src.api.config import DB_PATH

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.get("")
def get_companies(
    sector: str | None = Query(default=None),
    market_cap_category: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    """Return a list of companies with optional filters."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.broad_sector,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        WHERE 1 = 1
    """

    params = []

    # Sector filter
    if sector:
        query += """
            AND (
                c.broad_sector = ?
                OR c.id IN (
                    SELECT company_id
                    FROM peer_groups
                    WHERE peer_group_name = ?
                )
            )
        """

        params.extend([sector, sector])

    # Market-cap filter
    if market_cap_category:
        query += """
            AND c.id IN (
                SELECT company_id
                FROM sectors
                WHERE market_cap_category = ?
            )
        """

        params.append(market_cap_category)

    # Search filter
    if search:
        query += """
            AND (
                c.id LIKE ?
                OR c.company_name LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([search_value, search_value])

    query += """
        ORDER BY c.company_name
    """

    rows = conn.execute(
        query,
        params,
    ).fetchall()

    conn.close()

    return {
        "count": len(rows),
        "companies": [dict(row) for row in rows],
    }


@router.get("/{ticker}")
def get_company(ticker: str):
    """Return the full profile of one company."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    company = conn.execute(
        """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.broad_sector,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        WHERE UPPER(c.id) = UPPER(?)
        """,
        (ticker,),
    ).fetchone()

    if company is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found",
        )

    latest_ratios = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        (company["company_id"],),
    ).fetchone()

    conn.close()

    return {
        "company": dict(company),
        "latest_kpis": (dict(latest_ratios) if latest_ratios else {}),
    }
