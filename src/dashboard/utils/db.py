import os
import sqlite3
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
DB_PATH = os.path.join(PROJECT_ROOT, "nifty100.db")


def _get_connection():
    return sqlite3.connect(DB_PATH)


def _latest_year_from_table(table_name):
    conn = _get_connection()
    try:
        df = pd.read_sql_query(f"SELECT MAX(year) AS latest_year FROM {table_name}", conn)
        return df.iloc[0]["latest_year"]
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_companies():
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT
                c.id,
                c.company_name,
                COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                s.sub_sector,
                s.index_weight_pct,
                s.market_cap_category,
                c.website,
                c.nse_profile,
                c.bse_profile,
                c.about_company,
                c.face_value,
                c.book_value,
                c.roce_percentage,
                c.roe_percentage
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            ORDER BY c.company_name
            """,
            conn,
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    conn = _get_connection()
    try:
        query = """
            SELECT fr.*, c.company_name,
                   COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                   s.sub_sector
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE (c.company_name = ? OR c.id = ?)
        """
        params = [ticker, ticker]
        if year is not None:
            query += " AND fr.year = ?"
            params.append(year)
        query += " ORDER BY fr.year"
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT pl.*, c.company_name,
                   COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                   s.sub_sector
            FROM profitandloss pl
            JOIN companies c ON pl.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE (c.company_name = ? OR c.id = ?)
            ORDER BY pl.year
            """,
            conn, params=[ticker, ticker]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_bs(ticker):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT bs.*, c.company_name,
                   COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                   s.sub_sector
            FROM balancesheet bs
            JOIN companies c ON bs.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE (c.company_name = ? OR c.id = ?)
            ORDER BY bs.year
            """,
            conn, params=[ticker, ticker]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_cf(ticker):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT cf.*, c.company_name,
                   COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                   s.sub_sector
            FROM cashflow cf
            JOIN companies c ON cf.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE (c.company_name = ? OR c.id = ?)
            ORDER BY cf.year
            """,
            conn, params=[ticker, ticker]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_sectors():
    conn = _get_connection()
    try:
        # The project has 11 established peer groups used as dashboard sector groups.
        return pd.read_sql_query(
            """
            SELECT
                peer_group_name AS sector,
                COUNT(DISTINCT company_id) AS company_count
            FROM peer_percentiles
            GROUP BY peer_group_name
            ORDER BY company_count DESC, peer_group_name
            """,
            conn
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_peers(group_name):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT
                pp.company_id,
                c.company_name,
                COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                s.sub_sector,
                pp.metric,
                pp.value,
                pp.percentile_rank,
                pp.year,
                COALESCE(pg.is_benchmark, 0) AS is_benchmark
            FROM peer_percentiles pp
            JOIN companies c ON pp.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            LEFT JOIN peer_groups pg
              ON pg.peer_group_name = pp.peer_group_name
             AND pg.company_id = pp.company_id
            WHERE pp.peer_group_name = ?
            ORDER BY c.company_name, pp.metric, pp.year
            """,
            conn, params=[group_name]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_valuation(ticker):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT
                mc.*,
                c.company_name,
                COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                s.sub_sector
            FROM market_cap mc
            JOIN companies c ON mc.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE (c.company_name = ? OR c.id = ?)
            ORDER BY mc.year DESC
            """,
            conn, params=[ticker, ticker]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_market_data():
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT mc.*,
                   c.company_name,
                   COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                   s.sub_sector
            FROM market_cap mc
            JOIN companies c ON mc.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            ORDER BY mc.year, c.company_name
            """,
            conn
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT *
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            conn, params=[ticker]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT *
            FROM prosandcons
            WHERE company_id = ?
            ORDER BY id
            """,
            conn, params=[ticker]
        )
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_all_ratios():
    conn = _get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT fr.*, c.company_name,
                   COALESCE(s.broad_sector, c.broad_sector) AS broad_sector,
                   s.sub_sector
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.id
            LEFT JOIN sectors s ON c.id = s.company_id
            ORDER BY fr.company_id, fr.year
            """,
            conn,
        )
    finally:
        conn.close()
