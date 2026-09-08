from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test standard health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "artisan-api"
    assert "version" in data
    assert "environment" in data


def test_database_health_check(client: TestClient):
    """Test database connectivity health check."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_version_check(client: TestClient):
    """Test /version endpoint returns name and version."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_versioned_health_check(client: TestClient):
    """Test versioned /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
