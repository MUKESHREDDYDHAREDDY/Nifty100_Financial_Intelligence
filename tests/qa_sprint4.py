from pathlib import Path
import sqlite3
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"nifty100.db"

def main():
    conn=sqlite3.connect(DB)
    try:
        companies=pd.read_sql_query("SELECT COUNT(*) n FROM companies",conn).iloc[0,0]
        peers=pd.read_sql_query("SELECT COUNT(DISTINCT peer_group_name) n FROM peer_groups",conn).iloc[0,0]
        ratios=pd.read_sql_query("SELECT COUNT(*) n FROM financial_ratios",conn).iloc[0,0]
        fk=pd.read_sql_query("PRAGMA foreign_key_check",conn)
    finally:
        conn.close()
    print("Companies:",companies)
    print("Peer groups:",peers)
    print("Financial ratio rows:",ratios)
    print("Foreign key errors:",len(fk))
    xlsx=ROOT/"output"/"valuation_summary.xlsx"
    if xlsx.exists():
        v=pd.read_excel(xlsx)
        print("Valuation rows:",len(v))
        print("Valuation columns:",list(v.columns))
    else:
        print("Valuation workbook: NOT FOUND")

if __name__=="__main__":
    main()
