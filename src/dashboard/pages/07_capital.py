import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios

st.title("💰 Capital Allocation Map")
st.markdown("All 92 companies are classified into 8 capital-allocation patterns using latest available FCF, CapEx, leverage and ROE signals.")

companies=get_companies()

rows=[]
for ticker in companies["id"]:
    r=get_ratios(ticker)
    if r.empty: continue
    r["_y"]=pd.to_numeric(r["year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    r=r.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last")
    if r.empty: continue
    x=r.iloc[-1]
    rows.append({
        "company_id":ticker,
        "fcf":x.get("free_cash_flow_cr"),
        "capex":x.get("capex_cr"),
        "de":x.get("debt_to_equity"),
        "roe":x.get("return_on_equity_pct"),
        "cfo":x.get("cash_from_operations_cr"),
    })
d=pd.DataFrame(rows).merge(companies[["id","company_name","broad_sector","sub_sector"]],left_on="company_id",right_on="id",how="left")

def classify(x):
    f,cap,de,roe,cfo=[pd.to_numeric(x.get(k),errors="coerce") for k in ["fcf","capex","de","roe","cfo"]]
    if pd.isna(f): return "Data Limited"
    if de == 0 and f > 0: return "Debt-Free Cash Generator"
    if f > 0 and roe >= 20 and cap >= 0: return "High-Return Reinvestor"
    if f > 0 and cap <= 0: return "Asset-Light Cash Generator"
    if f < 0 and cap > 0 and roe >= 15: return "Growth Investor"
    if de > 2 and f > 0: return "Leveraged Cash Generator"
    if f < 0 and de > 2: return "Leveraged Investment"
    if f >= 0 and roe < 10: return "Low-Return Maintainer"
    return "Balanced Capital Allocator"

d["pattern"]=d.apply(classify,axis=1)
d["treemap_value"]=1
patterns=d.groupby("pattern",as_index=False).agg(company_count=("company_id","nunique"))
fig=px.treemap(d,path=["pattern","company_name"],values="treemap_value",title="Capital Allocation Patterns")
fig.update_layout(height=650)
st.plotly_chart(fig,use_container_width=True)

selected=st.selectbox("Select Pattern",patterns["pattern"].tolist())
st.subheader(f"Companies — {selected}")
st.dataframe(d[d["pattern"]==selected][["company_id","company_name","broad_sector","sub_sector","fcf","capex","de","roe","cfo"]].rename(columns={"company_id":"Ticker"}),use_container_width=True,hide_index=True)
