import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios

st.title("📈 Trend Analysis")
companies = get_companies()
query = st.text_input("Search company or ticker", "")
matches = companies if not query else companies[
    companies["company_name"].str.lower().str.contains(query.lower(), na=False)
    | companies["id"].str.lower().str.contains(query.lower(), na=False)
]
if matches.empty:
    st.warning("Ticker not found — please try another")
    st.stop()
chosen = st.selectbox("Company", [f"{x.id} — {x.company_name}" for x in matches.itertuples()])
ticker = chosen.split(" — ")[0]

rat = get_ratios(ticker)
if rat.empty:
    st.info("Data available note: no ratio history is available for this company.")
    st.stop()

rat["_year_num"] = pd.to_numeric(rat["year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
rat = rat.dropna(subset=["_year_num"]).sort_values(["_year_num","year"]).drop_duplicates("_year_num", keep="last").tail(10)

metric_options = {
    "ROE (%)":"return_on_equity_pct",
    "Net Profit Margin (%)":"net_profit_margin_pct",
    "Operating Profit Margin (%)":"operating_profit_margin_pct",
    "Debt / Equity":"debt_to_equity",
    "Interest Coverage":"interest_coverage",
    "Asset Turnover":"asset_turnover",
    "FCF (₹ Cr)":"free_cash_flow_cr",
    "EPS":"earnings_per_share",
    "Book Value / Share":"book_value_per_share",
    "Dividend Payout (%)":"dividend_payout_ratio_pct",
    "Quality Score":"composite_quality_score",
}
available = [k for k,v in metric_options.items() if v in rat.columns]
selected = st.multiselect("Select up to 3 metrics", available, default=available[:2], max_selections=3)

if not selected:
    st.info("Select at least one metric.")
    st.stop()

fig = go.Figure()
for label in selected:
    col = metric_options[label]
    vals = pd.to_numeric(rat[col], errors="coerce")
    fig.add_trace(go.Scatter(x=rat["_year_num"], y=vals, mode="lines+markers", name=label,
                             text=[f"YoY: {((vals.iloc[i]/vals.iloc[i-1])-1)*100:.1f}%" if i>0 and pd.notna(vals.iloc[i]) and pd.notna(vals.iloc[i-1]) and vals.iloc[i-1] != 0 else "YoY: N/A" for i in range(len(vals))],
                             hovertemplate="%{x}<br>%{y:.2f}<br>%{text}<extra></extra>"))
fig.update_layout(height=550, xaxis_title="Year", yaxis_title="Value")
st.plotly_chart(fig, use_container_width=True)
st.dataframe(rat[["_year_num"]+[metric_options[x] for x in selected]].rename(columns={"_year_num":"Year"}), use_container_width=True, hide_index=True)
