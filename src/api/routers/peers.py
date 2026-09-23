"""
Peers API endpoints.
"""

import sqlite3

from fastapi import APIRouter, HTTPException

from src.api.config import DB_PATH

router = APIRouter(prefix="/peers", tags=["Peers"])


@router.get("")
def get_peer_groups():
    """
    Return all peer groups with company counts.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            peer_group_name,
            COUNT(DISTINCT company_id) AS company_count
        FROM peer_groups
        GROUP BY peer_group_name
        ORDER BY peer_group_name
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    return {
        "count": len(rows),
        "peer_groups": [dict(row) for row in rows],
    }


@router.get("/{ticker}")
def get_company_peers(ticker: str):
    """
    Return the peer group and peer companies for a ticker.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    company = conn.execute(
        """
        SELECT id, company_name
        FROM companies
        WHERE id = ?
        """,
        (ticker.upper(),),
    ).fetchone()

    if company is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Company not found")

    peer_groups = conn.execute(
        """
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        WHERE company_id = ?
        """,
        (ticker.upper(),),
    ).fetchall()

    if not peer_groups:
        conn.close()
        return {
            "company_id": ticker.upper(),
            "company_name": company["company_name"],
            "peer_groups": [],
            "peers": [],
        }

    group_names = [row["peer_group_name"] for row in peer_groups]

    placeholders = ",".join("?" for _ in group_names)

    peers = conn.execute(
        f"""
        SELECT
            pg.company_id,
            c.company_name,
            pg.peer_group_name
        FROM peer_groups pg
        JOIN companies c
            ON c.id = pg.company_id
        WHERE pg.peer_group_name IN ({placeholders})
        ORDER BY pg.peer_group_name, pg.company_id
        """,
        group_names,
    ).fetchall()

    conn.close()

    return {
        "company_id": ticker.upper(),
        "company_name": company["company_name"],
        "peer_groups": group_names,
        "peer_count": len(peers),
        "peers": [dict(row) for row in peers],
    }
