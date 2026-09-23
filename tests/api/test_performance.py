import time

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_companies_endpoint_performance():
    """Companies endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/companies")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["count"] == 92
    assert elapsed < 3.0


def test_company_profile_performance():
    """Company profile endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/companies/TCS")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["company"]["company_id"] == "TCS"
    assert elapsed < 3.0


def test_screener_endpoint_performance():
    """Screener endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get(
        "/api/v1/screener",
        params={
            "min_roe": 15,
            "max_de": 1,
            "min_fcf": 0,
        },
    )

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["count"] == 32
    assert elapsed < 3.0


def test_peers_endpoint_performance():
    """Peers endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/peers/TCS")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["company_id"] == "TCS"
    assert response.json()["peer_count"] == 5
    assert elapsed < 3.0


def test_valuation_endpoint_performance():
    """Valuation endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/valuation/TCS")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["company_id"] == "TCS"
    assert "P/E" in response.json()
    assert elapsed < 3.0


def test_portfolio_endpoint_performance():
    """Portfolio endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/portfolio")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["count"] == 92
    assert len(response.json()["portfolio"]) == 92
    assert elapsed < 3.0


def test_documents_endpoint_performance():
    """Documents endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/documents/TCS")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["company_id"] == "TCS"
    assert response.json()["count"] == 16
    assert elapsed < 3.0


def test_sectors_endpoint_performance():
    """Sectors endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/sectors")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["count"] == 11
    assert len(response.json()["sectors"]) == 11
    assert elapsed < 3.0


def test_health_endpoint_performance():
    """Health endpoint should respond within 3 seconds."""

    start = time.perf_counter()

    response = client.get("/api/v1/health")

    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database_status"] == "ok"
    assert elapsed < 3.0
