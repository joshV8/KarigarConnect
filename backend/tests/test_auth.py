from fastapi.testclient import TestClient


def test_unauthenticated_request_rejected(client: TestClient):
    """Test requests without Bearer token return 401 Unauthorized."""
    resp = client.get("/api/v1/products")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


def test_invalid_token_rejected(client: TestClient):
    """Test requests with explicit invalid/expired token return 401 Unauthorized."""
    resp = client.get("/api/v1/products", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401


def test_get_current_user_profile(client: TestClient, auth_headers: dict):
    """Test /users/me returns authenticated user's profile."""
    resp = client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200
    user = resp.json()
    assert user["name"] is not None
    assert user["firebase_uid"] is not None


def test_update_current_user_profile(client: TestClient, auth_headers: dict):
    """Test updating user profile details via /users/me."""
    update_payload = {
        "name": "Master Craftsman Ramesh",
        "language": "hi",
        "location": "Jaipur, Rajasthan",
    }
    resp = client.put("/api/v1/users/me", json=update_payload, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Master Craftsman Ramesh"


def test_user_ownership_isolation(client: TestClient, auth_headers: dict, auth_headers_b: dict):
    """Test complete tenant boundary between User A and User B."""
    # User A creates a product
    create_a = client.post("/api/v1/products", json={"name": "User A Private Product", "raw_material_cost": 100.0}, headers=auth_headers)
    product_a_id = create_a.json()["id"]

    # User B cannot access User A's product
    resp = client.get(f"/api/v1/products/{product_a_id}", headers=auth_headers_b)
    assert resp.status_code == 404

    # User B cannot delete User A's product
    resp_del = client.delete(f"/api/v1/products/{product_a_id}", headers=auth_headers_b)
    assert resp_del.status_code == 404
