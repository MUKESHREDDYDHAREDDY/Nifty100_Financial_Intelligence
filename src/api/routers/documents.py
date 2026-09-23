"""
Documents API endpoints.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.config import DB_PATH

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get("")
def get_documents():
    """
    Return document/annual-report records for all companies.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            d.id,
            d.company_id,
            c.company_name,
            d.year,
            d.annual_report
        FROM documents d
        LEFT JOIN companies c
            ON d.company_id = c.id
        ORDER BY d.company_id, d.year
    """

    try:
        rows = conn.execute(query).fetchall()

    except sqlite3.Error as exc:
        conn.close()

        raise HTTPException(
            status_code=500,
            detail=f"Documents data is unavailable: {exc}",
        )

    conn.close()

    documents = [dict(row) for row in rows]

    return {
        "count": len(documents),
        "documents": documents,
    }


@router.get("/{ticker}")
def get_company_documents(ticker: str):
    """
    Return documents for a specific company.
    """

    ticker = ticker.upper()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    company = conn.execute(
        """
        SELECT id, company_name
        FROM companies
        WHERE id = ?
        """,
        (ticker,),
    ).fetchone()

    if company is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    rows = conn.execute(
        """
        SELECT
            id,
            company_id,
            year,
            annual_report
        FROM documents
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker,),
    ).fetchall()

    conn.close()

    documents = [dict(row) for row in rows]

    return {
        "company_id": ticker,
        "company_name": company["company_name"],
        "count": len(documents),
        "documents": documents,
    }
