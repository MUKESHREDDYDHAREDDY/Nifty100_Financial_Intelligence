from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_dashboard_app_exists():
    """Verify that the Streamlit dashboard application exists."""

    dashboard_path = Path("src/dashboard/app.py")

    assert dashboard_path.exists()
    assert dashboard_path.is_file()


def test_dashboard_company_data_available():
    """Verify that the API provides data required by the dashboard."""

    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["companies"]) == 92

    first_company = data["companies"][0]

    assert "company_id" in first_company
    assert "company_name" in first_company


def test_dashboard_reports_page_exists():
    """Verify that the Reports dashboard page exists."""

    reports_page = Path("src/dashboard/pages/08_reports.py")

    assert reports_page.exists()
    assert reports_page.is_file()
