import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.utils.db import get_sectors, get_peers

st.title("👥 Peer Comparison")
st.markdown("Compare a selected company against its peer-group average.")

groups = get_sectors()["sector"].tolist()
group = st.selectbox("Peer Group", groups)
peers = get_peers(group)

if peers.empty:
    st.info("No peer data available.")
    st.stop()

# Latest record per company and metric.
d = peers.copy()
d["_year"] = pd.to_numeric(d["year"].astype(str).str.extract(r"(\d{4})")[0], errors="coerce")
d = d.sort_values(["company_id","metric","_year","year"]).groupby(["company_id","metric"], as_index=False).tail(1)

companies = sorted(d["company_id"].unique())
benchmark_candidates = d[d["is_benchmark"].astype(bool)]["company_id"].unique().tolist()
benchmark = st.selectbox("Benchmark Company", companies, index=companies.index(benchmark_candidates[0]) if benchmark_candidates else 0)

st.subheader(f"{group} — KPI Comparison")

pivot = d.pivot_table(index=["company_id","company_name","is_benchmark"], columns="metric", values="value", aggfunc="first").reset_index()
pivot.columns.name = None

metric_cols = [c for c in pivot.columns if c not in ["company_id","company_name","is_benchmark"]]
selected_metrics = metric_cols[:8]

bench_row = pivot[pivot["company_id"] == benchmark]
avg_row = pivot[metric_cols].apply(pd.to_numeric, errors="coerce").mean()

fig = go.Figure()
if not bench_row.empty and selected_metrics:
    vals = [float(bench_row.iloc[0].get(m, np.nan)) for m in selected_metrics]
    avgs = [float(avg_row.get(m, np.nan)) for m in selected_metrics]
    # Normalize each metric against peer average for comparable radar shape.
    norm_b, norm_a = [], []
    for v,a in zip(vals,avgs):
        if pd.isna(v) or pd.isna(a) or a == 0:
            norm_b.append(0); norm_a.append(1)
        else:
            norm_b.append(v/a); norm_a.append(1)
    theta = selected_metrics + [selected_metrics[0]]
    fig.add_trace(go.Scatterpolar(r=norm_b+[norm_b[0]], theta=theta, fill="toself", name=benchmark))
    fig.add_trace(go.Scatterpolar(r=norm_a+[1], theta=theta, fill="toself", name="Peer Average"))
fig.update_layout(height=550, polar=dict(radialaxis=dict(visible=True, title="Relative to peer average")))
st.plotly_chart(fig, use_container_width=True)

st.caption("Radar values are normalized to peer average = 1.0 for cross-metric comparability.")

display = pivot.copy()
display["Benchmark"] = display["company_id"].eq(benchmark)
display = display.rename(columns={"company_id":"Ticker","company_name":"Company","is_benchmark":"Source Benchmark"})
st.dataframe(display, use_container_width=True, hide_index=True)

st.subheader("Benchmark Row")
st.dataframe(display[display["Ticker"] == benchmark], use_container_width=True, hide_index=True)
