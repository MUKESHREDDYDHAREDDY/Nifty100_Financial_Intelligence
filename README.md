# Nifty100 Financial Intelligence

A financial intelligence platform for analyzing NIFTY 100 companies using financial data, KPIs, screening, peer analysis, valuation, clustering, dashboards, and REST APIs.

## Project Overview

The project provides a complete financial analytics workflow covering:

- Data ingestion and validation
- Financial ratio calculation
- Company screening
- Peer-group analysis
- Valuation analysis
- Cash-flow intelligence
- Pros and cons generation
- Company and sector reports
- Machine-learning based company clustering
- Interactive Streamlit dashboard
- FastAPI REST API
- Automated testing and performance validation

## Coverage

- **92 companies**
- **11 peer groups**
- **1,188 financial ratio records**
- **5 company clusters**
- **16 FastAPI endpoint areas**
- **135 automated tests passing**

## Technology Stack

- Python
- SQLite
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Plotly
- Streamlit
- FastAPI
- Uvicorn
- Pytest
- ReportLab
- OpenPyXL

## Machine Learning Clustering

The project applies KMeans clustering to group all 92 companies into five financial archetypes.

### Clustering Features

The following financial features are used:

- Return on Equity (%)
- Debt to Equity
- Revenue CAGR (5-year)
- Free Cash Flow CAGR (5-year)
- Operating Profit Margin (%)

### Preprocessing

Missing feature values are imputed using the sector median.

The features are standardized using `StandardScaler`.

### KMeans Configuration

```text
Number of clusters: 5
Random state: 42

## REST API

The FastAPI service is available under:

```text
/api/v1/