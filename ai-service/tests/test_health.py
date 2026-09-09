"""
Gate 1 tests — AI Service Foundation.

Verifies the service starts and the /health endpoint behaves as specified.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_expected_body():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


def test_root_does_not_404():
    response = client.get("/")
    assert response.status_code == 200
