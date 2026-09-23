"""
Sectors API endpoints.
"""

import sqlite3

from fastapi import APIRouter

from src.api.config import DB_PATH

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("")
def get_sectors():
    """
    Return sector/peer-group summary information.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            pg.peer_group_name AS sector,
            COUNT(DISTINCT pg.company_id) AS company_count
        FROM peer_groups pg
        GROUP BY pg.peer_group_name
        ORDER BY pg.peer_group_name
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    sectors = [dict(row) for row in rows]

    return {
        "count": len(sectors),
        "sectors": sectors,
    }
