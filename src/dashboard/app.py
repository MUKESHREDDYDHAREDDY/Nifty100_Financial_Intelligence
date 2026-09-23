import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Nifty 100 Financial Intelligence")
st.markdown(
    "Analyst dashboard for company profiles, screening, peer analysis, trends, "
    "sectors, capital allocation, annual reports and valuation."
)
st.info("Use the sidebar to open one of the 8 dashboard screens.")
