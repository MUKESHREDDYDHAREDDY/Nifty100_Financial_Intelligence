import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios, get_pl, get_market_data, get_sectors, get_peers

st.title("🏭 Sector Analysis")
st.markdown("Revenue vs ROE bubble analysis with market-cap sizing and sub-sector colouring.")

companies=get_companies()
groups=get_sectors()["sector"].tolist()
group=st.selectbox("Sector / Peer Group",groups)

members=get_peers(group)[["company_id"]].drop_duplicates()
latest_market=get_market_data().sort_values("year").groupby("company_id",as_index=False).tail(1)

rows=[]
for ticker in members["company_id"]:
    r=get_ratios(ticker)
    p=get_pl(ticker)
    if r.empty: continue
    r["_y"]=pd.to_numeric(r["year"].astype(str).str.extract(r"(\d{4})")[0],errors="coerce")
    r=r.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last")
    rr=r.iloc[-1]
    revenue=None
    if not p.empty:
        p["_y"]=pd.to_numeric(p["year"].astype(str).str.extract(r"(\d{4})")[0],errors="coerce")
        p=p.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last")
        revenue=p.iloc[-1].get("sales")
    rows.append({"company_id":ticker,"roe":rr.get("return_on_equity_pct"),"revenue":revenue})

data=pd.DataFrame(rows).merge(companies,left_on="company_id",right_on="id",how="left")
data=data.merge(latest_market[["company_id","market_cap_crore"]],on="company_id",how="left")
data["revenue"]=pd.to_numeric(data["revenue"],errors="coerce")
data["roe"]=pd.to_numeric(data["roe"],errors="coerce")
data["market_cap_crore"]=pd.to_numeric(data["market_cap_crore"],errors="coerce")

fig=px.scatter(data,x="revenue",y="roe",size="market_cap_crore",color="sub_sector",
               hover_name="company_name",title=f"{group}: Revenue vs ROE")
fig.update_layout(height=550,xaxis_title="Revenue (₹ Cr)",yaxis_title="ROE (%)")
st.plotly_chart(fig,use_container_width=True)

# Sector median KPIs.
k=[]
for ticker in members["company_id"]:
    r=get_ratios(ticker)
    if r.empty: continue
    r["_y"]=pd.to_numeric(r["year"].astype(str).str.extract(r"(\d{4})")[0],errors="coerce")
    r=r.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last")
    if not r.empty: k.append(r.iloc[-1])
if k:
    kd=pd.DataFrame(k)
    mapping={"ROE":"return_on_equity_pct","D/E":"debt_to_equity","NPM":"net_profit_margin_pct","ICR":"interest_coverage"}
    bar=pd.DataFrame({"KPI":list(mapping),"Median":[pd.to_numeric(kd[c],errors="coerce").median() for c in mapping.values()]})
    st.subheader("Sector Median KPI")
    st.plotly_chart(px.bar(bar,x="KPI",y="Median",text_auto=".2f"),use_container_width=True)
