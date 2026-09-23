"""
Financial statements and ratios API router.
"""

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from src.api.config import DB_PATH

router = APIRouter(
    prefix="/companies",
    tags=["Financials"],
)


def get_company_id(ticker: str):
    """Return the company ID for a ticker."""

    conn = sqlite3.connect(DB_PATH)

    row = conn.execute(
        """
        SELECT id
        FROM companies
        WHERE UPPER(id) = UPPER(?)
        """,
        (ticker,),
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found",
        )

    return row[0]


def get_financial_data(
    table_name: str,
    company_id: str,
    from_year: str | None,
    to_year: str | None,
):
    """Return financial data for a company."""

    allowed_tables = {
        "profitandloss": "profitandloss",
        "balancesheet": "balancesheet",
        "cashflow": "cashflow",
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid table name")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = f"""
        SELECT *
        FROM {allowed_tables[table_name]}
        WHERE company_id = ?
    """

    params = [company_id]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)

    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year"

    rows = conn.execute(
        query,
        params,
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


@router.get("/{ticker}/profit-loss")
def get_profit_loss(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return profit and loss data."""

    company_id = get_company_id(ticker)

    data = get_financial_data(
        "profitandloss",
        company_id,
        from_year,
        to_year,
    )

    return {
        "company_id": company_id,
        "statement": "profit_loss",
        "count": len(data),
        "data": data,
    }


@router.get("/{ticker}/balance-sheet")
def get_balance_sheet(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return balance sheet data."""

    company_id = get_company_id(ticker)

    data = get_financial_data(
        "balancesheet",
        company_id,
        from_year,
        to_year,
    )

    return {
        "company_id": company_id,
        "statement": "balance_sheet",
        "count": len(data),
        "data": data,
    }


@router.get("/{ticker}/cash-flow")
def get_cash_flow(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return cash flow data."""

    company_id = get_company_id(ticker)

    data = get_financial_data(
        "cashflow",
        company_id,
        from_year,
        to_year,
    )

    return {
        "company_id": company_id,
        "statement": "cash_flow",
        "count": len(data),
        "data": data,
    }


@router.get("/{ticker}/ratios")
def get_ratios(
    ticker: str,
    year: str | None = Query(default=None),
):
    """Return financial ratios for a company."""

    company_id = get_company_id(ticker)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """

    params = [company_id]

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year"

    rows = conn.execute(
        query,
        params,
    ).fetchall()

    conn.close()

    data = [dict(row) for row in rows]

    return {
        "company_id": company_id,
        "count": len(data),
        "data": data,
    }
