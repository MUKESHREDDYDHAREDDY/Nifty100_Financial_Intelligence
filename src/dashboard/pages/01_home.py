import pandas as pd
import streamlit as st
import plotly.express as px

from dashboard.utils.db import get_companies, get_all_ratios, get_market_data, get_sectors

st.title("🏠 Nifty 100 Financial Intelligence")
st.markdown("Market overview and financial analytics dashboard.")

companies = get_companies()
ratios = get_all_ratios()
market = get_market_data()

selected_year = st.sidebar.selectbox("Dashboard Year", list(range(2019, 2025)), index=5)

ratios["_year_num"] = pd.to_numeric(
    ratios["year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce"
)
year_ratios = ratios[ratios["_year_num"] == selected_year].copy()
year_ratios = year_ratios.sort_values(["company_id", "year"]).drop_duplicates("company_id", keep="last")
year_market = market[market["year"] == selected_year].copy()

def med(s):
    x = pd.to_numeric(s, errors="coerce").dropna()
    return None if x.empty else float(x.median())

roe = pd.to_numeric(year_ratios["return_on_equity_pct"], errors="coerce").mean()
pe = med(year_market["pe_ratio"])
de = med(year_ratios["debt_to_equity"])
rev_cagr = med(year_ratios["revenue_cagr_5yr"])
debt_free = int((pd.to_numeric(year_ratios["debt_to_equity"], errors="coerce").fillna(999) == 0).sum())

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Average ROE", "N/A" if pd.isna(roe) else f"{roe:.2f}%")
c2.metric("Median P/E", "N/A" if pe is None else f"{pe:.2f}")
c3.metric("Median D/E", "N/A" if de is None else f"{de:.2f}")
c4.metric("Total Companies", len(companies))
c5.metric("Median Revenue CAGR 5yr", "N/A" if rev_cagr is None else f"{rev_cagr:.2f}%")
c6.metric("Debt-Free Companies", debt_free)

st.divider()
st.subheader("Sector Distribution")
sectors = get_sectors()
st.plotly_chart(px.pie(sectors, names="sector", values="company_count", hole=.45),
                use_container_width=True)

st.subheader("Top 5 Companies by Composite Quality Score")
if "composite_quality_score" in year_ratios.columns:
    top = year_ratios[["company_id","composite_quality_score"]].merge(
        companies[["id","company_name"]], left_on="company_id", right_on="id", how="left"
    ).sort_values("composite_quality_score", ascending=False).head(5)
    top = top.rename(columns={"company_id":"Ticker","company_name":"Company",
                              "composite_quality_score":"Quality Score"})
    st.dataframe(top[["Ticker","Company","Quality Score"]], use_container_width=True, hide_index=True)
else:
    st.info("Composite quality score is not available for this year.")
