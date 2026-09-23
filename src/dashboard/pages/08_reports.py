import pandas as pd
import requests
import streamlit as st

from dashboard.utils.db import get_companies, get_documents

st.title("📄 Annual Reports")
st.markdown("Annual-report repository with year, BSE PDF link and availability status.")

companies = get_companies()

query = st.text_input("Search company or ticker", "")

matches = companies if not query else companies[
    companies["company_name"].str.lower().str.contains(query.lower(), na=False)
    | companies["id"].str.lower().str.contains(query.lower(), na=False)
]

if matches.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

chosen = st.selectbox(
    "Company",
    [f"{x.id} — {x.company_name}" for x in matches.itertuples()]
)

ticker = chosen.split(" — ")[0]
docs = get_documents(ticker)

if docs.empty:
    st.info("No annual-report records are available for this company.")
    st.stop()

# Documents table uses the annual_report column for BSE PDF URLs.
url_col = "annual_report"
year_col = "year"

rows = []

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

for _, r in docs.iterrows():
    year = r[year_col]
    url = r[url_col] if pd.notna(r[url_col]) else None

    status = "Report unavailable"

    if isinstance(url, str) and url.startswith("http"):
        try:
            response = requests.get(
                url,
                headers=headers,
                allow_redirects=True,
                stream=True,
                timeout=10,
            )

            # Only a confirmed HTTP 404 is treated as unavailable.
            if response.status_code == 404:
                status = "Report unavailable"
            else:
                status = "Link available"

            response.close()

        except requests.RequestException:
            # Keep the report clickable when automatic verification
            # is blocked or times out.
            status = "Link available"

    rows.append(
        {
            "Year": year,
            "BSE PDF": url,
            "Status": status,
        }
    )

out = (
    pd.DataFrame(rows)
    .drop_duplicates("Year")
    .sort_values("Year", ascending=False)
)

st.dataframe(
    out,
    use_container_width=True,
    hide_index=True,
)

for _, r in out.iterrows():
    url = r["BSE PDF"]
    year = r["Year"]

    if r["Status"] == "Report unavailable":
        st.error(f"🔴 Report unavailable — {year}")

    elif isinstance(url, str) and url.startswith("http"):
        st.link_button(
            f"📄 {year} Annual Report",
            url,
        )