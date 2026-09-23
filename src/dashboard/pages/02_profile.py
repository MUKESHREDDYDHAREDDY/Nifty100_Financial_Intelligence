import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios, get_pl, get_bs, get_pros_cons

st.title("🏢 Company Profile")
st.markdown("Search by company name or ticker and review financial performance.")

companies = get_companies()
query = st.text_input("Search company or ticker", placeholder="e.g. TCS, INFY")
matches = companies if not query else companies[
    companies["company_name"].str.lower().str.contains(query.lower(), na=False)
    | companies["id"].str.lower().str.contains(query.lower(), na=False)
]
if matches.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

chosen = st.selectbox("Company", [f"{x.id} — {x.company_name}" for x in matches.itertuples()])
ticker = chosen.split(" — ",1)[0]
company = companies[companies["id"] == ticker].iloc[0]

st.subheader(company["company_name"])
a,b,c = st.columns(3)
a.write(f"**Sector:** {company.get('broad_sector') or 'N/A'}")
b.write(f"**Sub-sector:** {company.get('sub_sector') or 'N/A'}")
c.write(f"**NSE Ticker:** {ticker}")
st.write(company.get("about_company") or "About company information is not available.")

rat = get_ratios(ticker)
pl = get_pl(ticker)
bs = get_bs(ticker)

def latest_nonnull(df, col):
    if col not in df.columns: return None
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    return None if s.empty else float(s.iloc[-1])

# Latest annual KPI snapshot.
r = rat.copy()
r["_y"] = pd.to_numeric(r["year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
r = r.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y", keep="last")
annual = r[r["_y"] == r["_y"].max()] if not r.empty else r

roe = latest_nonnull(annual,"return_on_equity_pct")
nmp = latest_nonnull(annual,"net_profit_margin_pct")
de = latest_nonnull(annual,"debt_to_equity")
cagr = latest_nonnull(annual,"revenue_cagr_5yr")
fcf = latest_nonnull(annual,"free_cash_flow_cr")
roce_current = company.get("roce_percentage")

cols = st.columns(6)
for c,(label,val,suf) in zip(cols,[
    ("ROE",roe,"%"),("ROCE",roce_current,"%"),("Net Profit Margin",nmp,"%"),
    ("D/E",de,""),("Revenue CAGR 5yr",cagr,"%"),("FCF",fcf," Cr")
]):
    c.metric(label, "N/A" if val is None or pd.isna(val) else f"{val:,.2f}{suf}")

st.divider()
st.subheader("Revenue and Net Profit — 10 Year View")
if not pl.empty:
    p = pl.copy()
    p["_y"] = pd.to_numeric(p["year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
    p = p.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last").tail(10)
    long = p[["_y","sales","net_profit"]].melt("_y",var_name="Metric",value_name="₹ Cr")
    fig = px.bar(long,x="_y",y="₹ Cr",color="Metric",barmode="group")
    fig.update_layout(height=450,xaxis_title="Year")
    st.plotly_chart(fig,use_container_width=True)

st.subheader("ROE and ROCE — 10 Year View")
if not pl.empty and not bs.empty:
    p = pl.copy()
    b = bs.copy()
    p["_y"] = pd.to_numeric(p["year"].astype(str).str.extract(r"(\d{4})")[0],errors="coerce")
    b["_y"] = pd.to_numeric(b["year"].astype(str).str.extract(r"(\d{4})")[0],errors="coerce")
    p = p.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last")
    b = b.dropna(subset=["_y"]).sort_values(["_y","year"]).drop_duplicates("_y",keep="last")
    m = p.merge(b,on="_y",suffixes=("","_bs")).sort_values("_y").tail(10)
    equity = pd.to_numeric(m["equity_capital"],errors="coerce") + pd.to_numeric(m["reserves"],errors="coerce")
    capital = equity + pd.to_numeric(m["borrowings"],errors="coerce")
    ebit = pd.to_numeric(m["operating_profit"],errors="coerce")
    roe_hist = pd.to_numeric(m["net_profit"],errors="coerce") / equity * 100
    roce_hist = ebit / capital * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["_y"],y=roe_hist,name="ROE",mode="lines+markers"))
    fig.add_trace(go.Scatter(x=m["_y"],y=roce_hist,name="ROCE",mode="lines+markers",yaxis="y2"))
    fig.update_layout(height=450,yaxis_title="ROE (%)",
                      yaxis2=dict(title="ROCE (%)",overlaying="y",side="right"))
    st.plotly_chart(fig,use_container_width=True)
else:
    st.info("Data available note: historical ROE/ROCE data is incomplete for this company.")

st.subheader("Pros & Cons")
try:
    pc = get_pros_cons(ticker)
except Exception:
    pc = pd.DataFrame()

if not pc.empty:
    for _,row in pc.iterrows():
        if pd.notna(row.get("pros")): st.success(f"✓ {row['pros']}")
        if pd.notna(row.get("cons")): st.error(f"✗ {row['cons']}")
else:
    if roe is not None and roe > 20: st.success("✓ Strong ROE above 20%")
    if de is not None and de <= 1: st.success("✓ Conservative leverage")
    if fcf is not None and fcf > 0: st.success("✓ Positive free cash flow")
    if de is not None and de > 2: st.error("✗ High debt-to-equity")
    if fcf is not None and fcf < 0: st.error("✗ Negative free cash flow")
