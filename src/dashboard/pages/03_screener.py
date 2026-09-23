import pandas as pd
import streamlit as st

from dashboard.utils.db import get_companies, get_ratios, get_market_data

st.title("🔎 Nifty 100 Screener")
st.markdown("Filter companies using 10 financial and valuation metrics.")

PRESETS = {
    "Quality": dict(
        roe=15.0, de=1.0, fcf=0.0, rev=-100.0, pat=-100.0,
        opm=0.0, pe=999.0, pb=999.0, div=0.0, icr=0.0
    ),
    "Value": dict(
        roe=0.0, de=5.0, fcf=0.0, rev=-100.0, pat=-100.0,
        opm=0.0, pe=20.0, pb=3.0, div=0.0, icr=0.0
    ),
    "Growth": dict(
        roe=10.0, de=3.0, fcf=-999999.0, rev=10.0, pat=10.0,
        opm=0.0, pe=999.0, pb=999.0, div=0.0, icr=0.0
    ),
    "Dividend": dict(
        roe=0.0, de=5.0, fcf=0.0, rev=-100.0, pat=-100.0,
        opm=0.0, pe=999.0, pb=999.0, div=2.0, icr=0.0
    ),
    "Debt-Free": dict(
        roe=0.0, de=0.0, fcf=0.0, rev=-100.0, pat=-100.0,
        opm=0.0, pe=999.0, pb=999.0, div=0.0, icr=0.0
    ),
    "Turnaround": dict(
        roe=5.0, de=5.0, fcf=0.0, rev=0.0, pat=0.0,
        opm=0.0, pe=999.0, pb=999.0, div=0.0, icr=0.0
    ),
}


if "preset" not in st.session_state:
    st.session_state.preset = "Quality"


def slider(label, key, minv, maxv, default):
    return st.sidebar.slider(
        label,
        minv,
        maxv,
        default,
        key=key,
    )


preset = st.sidebar.selectbox(
    "Preset",
    list(PRESETS),
    index=list(PRESETS).index(st.session_state.preset),
)

if preset != st.session_state.preset:
    st.session_state.preset = preset
    st.rerun()


p = PRESETS[preset]

min_roe = slider(
    "ROE minimum (%)",
    "s_roe",
    -50.0,
    200.0,
    float(p["roe"]),
)

max_de = slider(
    "D/E maximum",
    "s_de",
    0.0,
    20.0,
    float(p["de"]),
)

min_fcf = slider(
    "FCF minimum (₹ Cr)",
    "s_fcf",
    -100000.0,
    100000.0,
    float(p["fcf"]),
)

min_rev = slider(
    "Revenue CAGR minimum (%)",
    "s_rev",
    -100.0,
    100.0,
    float(p["rev"]),
)

min_pat = slider(
    "PAT CAGR minimum (%)",
    "s_pat",
    -100.0,
    100.0,
    float(p["pat"]),
)

min_opm = slider(
    "OPM minimum (%)",
    "s_opm",
    -100.0,
    100.0,
    float(p["opm"]),
)

max_pe = slider(
    "P/E maximum",
    "s_pe",
    0.0,
    200.0,
    float(min(p["pe"], 200)),
)

max_pb = slider(
    "P/B maximum",
    "s_pb",
    0.0,
    100.0,
    float(min(p["pb"], 100)),
)

min_div = slider(
    "Dividend Yield minimum (%)",
    "s_div",
    0.0,
    20.0,
    float(p["div"]),
)

min_icr = slider(
    "Interest Coverage minimum",
    "s_icr",
    0.0,
    100.0,
    float(p["icr"]),
)


# ---------------------------------------------------------
# Load company-level data
# ---------------------------------------------------------

companies = get_companies()
market = get_market_data()

latest_market = (
    market.sort_values("year")
    .groupby("company_id", as_index=False)
    .tail(1)
)


# ---------------------------------------------------------
# Build latest financial-ratio record for each company
# ---------------------------------------------------------

rows = []

for ticker in companies["id"]:
    ratios = get_ratios(ticker)

    if ratios.empty:
        continue

    d = ratios.copy()

    d["_year"] = pd.to_numeric(
        d["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    d = (
        d.dropna(subset=["_year"])
        .sort_values(["_year", "year"])
        .drop_duplicates("_year", keep="last")
    )

    if d.empty:
        continue

    # Latest annual record
    row = d.iloc[-1].to_dict()
    row["company_id"] = ticker

    rows.append(row)


rat = pd.DataFrame(rows)


# ---------------------------------------------------------
# Merge data
# ---------------------------------------------------------

data = companies.merge(
    rat,
    left_on="id",
    right_on="company_id",
    how="left",
    suffixes=("", "_ratio"),
)

data = data.merge(
    latest_market[
        [
            "company_id",
            "pe_ratio",
            "pb_ratio",
            "dividend_yield_pct",
        ]
    ],
    left_on="id",
    right_on="company_id",
    how="left",
    suffixes=("", "_mkt"),
)


# ---------------------------------------------------------
# IMPORTANT:
# Use the company-level ROE for Screener ROE.
#
# The financial_ratios table contains extreme ROE values
# for a few companies because of unusual/small equity bases.
# Using companies.roe_percentage keeps the displayed ROE
# and filter consistent with the Profile data.
# ---------------------------------------------------------

data["roe_screener"] = pd.to_numeric(
    data["roe_percentage"],
    errors="coerce",
)


# ---------------------------------------------------------
# Apply filters
# ---------------------------------------------------------

conditions = (
    data["roe_screener"].ge(min_roe)
    & data["roe_screener"].notna()
    & pd.to_numeric(
        data["debt_to_equity"],
        errors="coerce",
    ).le(max_de)
    & pd.to_numeric(
        data["free_cash_flow_cr"],
        errors="coerce",
    ).ge(min_fcf)
    & pd.to_numeric(
        data["revenue_cagr_5yr"],
        errors="coerce",
    ).ge(min_rev)
    & pd.to_numeric(
        data["pat_cagr_5yr"],
        errors="coerce",
    ).ge(min_pat)
    & pd.to_numeric(
        data["operating_profit_margin_pct"],
        errors="coerce",
    ).ge(min_opm)
    & pd.to_numeric(
        data["pe_ratio"],
        errors="coerce",
    ).le(max_pe)
    & pd.to_numeric(
        data["pb_ratio"],
        errors="coerce",
    ).le(max_pb)
    & pd.to_numeric(
        data["dividend_yield_pct"],
        errors="coerce",
    ).ge(min_div)
    & pd.to_numeric(
        data["interest_coverage"],
        errors="coerce",
    ).ge(min_icr)
)


result = data.loc[conditions].copy()


# ---------------------------------------------------------
# Composite score
# ---------------------------------------------------------

result["Quality Score"] = pd.to_numeric(
    result["composite_quality_score"],
    errors="coerce",
)


# ---------------------------------------------------------
# Output columns
# ---------------------------------------------------------

visible = [
    ("id", "Company ID"),
    ("company_name", "Company"),
    ("broad_sector", "Sector"),
    ("Quality Score", "Composite Score"),
    ("roe_screener", "ROE (%)"),
    ("debt_to_equity", "D/E"),
    ("free_cash_flow_cr", "FCF (₹ Cr)"),
    ("revenue_cagr_5yr", "Revenue CAGR 5yr (%)"),
    ("pat_cagr_5yr", "PAT CAGR 5yr (%)"),
    ("operating_profit_margin_pct", "OPM (%)"),
    ("pe_ratio", "P/E"),
    ("pb_ratio", "P/B"),
    ("dividend_yield_pct", "Dividend Yield (%)"),
    ("interest_coverage", "ICR"),
]


available_columns = [
    column
    for column, _ in visible
    if column in result.columns
]

out = result[available_columns].copy()

out.columns = [
    label
    for column, label in visible
    if column in result.columns
]


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

st.subheader("Screening Results")

st.write(
    f"**{len(out)} companies match your filters** "
    f"out of {len(companies)} screened."
)

if out.empty:
    st.info(
        "No companies match the selected filters. "
        "Try relaxing one or more criteria."
    )
else:
    st.dataframe(
        out,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# CSV export
# ---------------------------------------------------------

st.download_button(
    "📥 Download Screener CSV",
    out.to_csv(index=False).encode("utf-8"),
    "nifty100_screener_results.csv",
    "text/csv",
)