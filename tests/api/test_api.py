from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Nifty100 Financial Intelligence API"
    assert data["version"] == "1.0.0"
    assert data["docs"] == "/docs"


def test_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["database_status"] == "ok"


def test_companies():
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["companies"]) == 92


def test_company_tcs():
    response = client.get("/api/v1/companies/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company"]["company_id"] == "TCS"
    assert data["company"]["company_name"] == "Tata Consultancy Services Ltd"

    assert "latest_kpis" in data


def test_company_not_found():
    response = client.get("/api/v1/companies/INVALID123")

    assert response.status_code == 404


def test_tcs_profit_loss():
    response = client.get("/api/v1/companies/TCS/profit-loss")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == 13
    assert len(data["data"]) == 13


def test_tcs_balance_sheet():
    response = client.get("/api/v1/companies/TCS/balance-sheet")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == 13
    assert len(data["data"]) == 13


def test_tcs_cash_flow():
    response = client.get("/api/v1/companies/TCS/cash-flow")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == 24
    assert len(data["data"]) == 24


def test_tcs_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["count"] == 13
    assert len(data["data"]) == 13


def test_screener_all_companies():
    response = client.get("/api/v1/screener")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["companies"]) == 92


def test_screener_quality_filters():
    response = client.get(
        "/api/v1/screener",
        params={
            "min_roe": 15,
            "max_de": 1,
            "min_fcf": 0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 32
    assert len(data["companies"]) == 32


def test_screener_financial_sector():
    response = client.get(
        "/api/v1/screener",
        params={
            "sector": "Financials",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 20
    assert len(data["companies"]) == 20


def test_sectors():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 11
    assert len(data["sectors"]) == 11


def test_peer_groups():
    response = client.get("/api/v1/peers")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 11
    assert len(data["peer_groups"]) == 11


def test_tcs_peers():
    response = client.get("/api/v1/peers/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["company_name"] == "Tata Consultancy Services Ltd"
    assert data["peer_count"] == 5
    assert len(data["peers"]) == 5


def test_peer_company_not_found():
    response = client.get("/api/v1/peers/INVALID123")

    assert response.status_code == 404


def test_valuation_all_companies():
    response = client.get("/api/v1/valuation")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["valuations"]) == 92


def test_valuation_tcs():
    response = client.get("/api/v1/valuation/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["company_name"] == "Tata Consultancy Services Ltd"

    assert "P/E" in data
    assert "P/B" in data
    assert "EV/EBITDA" in data
    assert "flag" in data


def test_valuation_company_not_found():
    response = client.get("/api/v1/valuation/INVALID123")

    assert response.status_code == 404


def test_portfolio():
    response = client.get("/api/v1/portfolio")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["portfolio"]) == 92


def test_portfolio_contains_tcs():
    response = client.get("/api/v1/portfolio")

    assert response.status_code == 200

    data = response.json()

    tcs = next(
        company for company in data["portfolio"] if company["company_id"] == "TCS"
    )

    assert tcs["company_name"] == "Tata Consultancy Services Ltd"
    assert "valuation_flag" in tcs


def test_documents():
    response = client.get("/api/v1/documents")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1585
    assert len(data["documents"]) == 1585


def test_tcs_documents():
    response = client.get("/api/v1/documents/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert data["company_name"] == "Tata Consultancy Services Ltd"
    assert data["count"] == 16
    assert len(data["documents"]) == 16


def test_documents_company_not_found():
    response = client.get("/api/v1/documents/INVALID123")

    assert response.status_code == 404
