from fastapi.testclient import TestClient


def test_create_valid_product(client: TestClient, auth_headers: dict):
    """Test valid product draft creation."""
    payload = {
        "name": "Handmade Clay Lamp",
        "raw_material_cost": 100.0,
        "labour_cost": 50.0,
        "packaging_cost": 15.0,
        "category": "Pottery",
        "material": "Clay",
    }
    response = client.post("/api/v1/products", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Handmade Clay Lamp"
    assert data["raw_material_cost"] == 100.0
    assert data["status"] == "draft"


def test_create_product_empty_name_rejected(client: TestClient, auth_headers: dict):
    """Test creating product with empty name is rejected with 422."""
    payload = {
        "name": "   ",
        "raw_material_cost": 100.0,
    }
    response = client.post("/api/v1/products", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_create_product_negative_cost_rejected(client: TestClient, auth_headers: dict):
    """Test creating product with negative cost is rejected with 422."""
    payload = {
        "name": "Invalid Item",
        "raw_material_cost": -50.0,
    }
    response = client.post("/api/v1/products", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_list_products_owned_by_user(client: TestClient, auth_headers: dict, auth_headers_b: dict):
    """Test user only lists their own products."""
    # Create product for User A
    client.post("/api/v1/products", json={"name": "Product A", "raw_material_cost": 100.0}, headers=auth_headers)
    # Create product for User B
    client.post("/api/v1/products", json={"name": "Product B", "raw_material_cost": 200.0}, headers=auth_headers_b)

    # User A listing
    resp_a = client.get("/api/v1/products", headers=auth_headers)
    assert resp_a.status_code == 200
    names_a = [p["name"] for p in resp_a.json()]
    assert "Product A" in names_a
    assert "Product B" not in names_a


def test_get_product_by_id(client: TestClient, auth_headers: dict):
    """Test getting single product details."""
    create_resp = client.post("/api/v1/products", json={"name": "Terracotta Vase", "raw_material_cost": 120.0}, headers=auth_headers)
    product_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == product_id


def test_get_nonexistent_product_returns_404(client: TestClient, auth_headers: dict):
    """Test non-existent product ID returns 404."""
    response = client.get("/api/v1/products/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_product(client: TestClient, auth_headers: dict):
    """Test updating product fields."""
    create_resp = client.post("/api/v1/products", json={"name": "Initial Name", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = create_resp.json()["id"]

    update_payload = {"name": "Updated Name", "raw_material_cost": 150.0}
    update_resp = client.put(f"/api/v1/products/{product_id}", json=update_payload, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Name"
    assert update_resp.json()["raw_material_cost"] == 150.0


def test_delete_product(client: TestClient, auth_headers: dict):
    """Test deleting product."""
    create_resp = client.post("/api/v1/products", json={"name": "To Delete", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Ensure it no longer exists
    get_resp = client.get(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_cross_user_product_isolation(client: TestClient, auth_headers: dict, auth_headers_b: dict):
    """Test User B cannot get, update, or delete User A's product."""
    create_resp = client.post("/api/v1/products", json={"name": "User A Product", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = create_resp.json()["id"]

    # User B tries GET
    get_resp = client.get(f"/api/v1/products/{product_id}", headers=auth_headers_b)
    assert get_resp.status_code == 404

    # User B tries PUT
    put_resp = client.put(f"/api/v1/products/{product_id}", json={"name": "Hacked Name"}, headers=auth_headers_b)
    assert put_resp.status_code == 404

    # User B tries DELETE
    del_resp = client.delete(f"/api/v1/products/{product_id}", headers=auth_headers_b)
    assert del_resp.status_code == 404
