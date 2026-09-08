from fastapi.testclient import TestClient


def test_create_and_get_catalog(client: TestClient, auth_headers: dict):
    """Test creating and retrieving a digital catalog."""
    payload = {
        "title": "Spring Pottery Collection",
        "description": "Artisan handmade terracotta creations",
    }
    create_resp = client.post("/api/v1/catalogs", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    cat = create_resp.json()
    assert cat["title"] == "Spring Pottery Collection"
    catalog_id = cat["id"]

    get_resp = client.get(f"/api/v1/catalogs/{catalog_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == catalog_id


def test_add_and_remove_product_from_catalog(client: TestClient, auth_headers: dict):
    """Test associating and removing a product from a catalog."""
    # Create product
    prod_resp = client.post("/api/v1/products", json={"name": "Vase", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    # Create catalog
    cat_resp = client.post("/api/v1/catalogs", json={"title": "Vases Catalog"}, headers=auth_headers)
    catalog_id = cat_resp.json()["id"]

    # Add product to catalog
    add_resp = client.post(f"/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=auth_headers)
    assert add_resp.status_code == 200
    cat_data = add_resp.json()
    assert len(cat_data["products"]) == 1
    assert cat_data["products"][0]["id"] == product_id

    # Add duplicate product (should return 409 Conflict per uniqueness constraint)
    add_dup = client.post(f"/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=auth_headers)
    assert add_dup.status_code == 409

    # Remove product from catalog
    rem_resp = client.delete(f"/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=auth_headers)
    assert rem_resp.status_code == 200
    assert len(rem_resp.json()["products"]) == 0


def test_update_and_delete_catalog(client: TestClient, auth_headers: dict):
    """Test updating and deleting a catalog."""
    create_resp = client.post("/api/v1/catalogs", json={"title": "Old Title"}, headers=auth_headers)
    catalog_id = create_resp.json()["id"]

    # Update
    update_resp = client.put(f"/api/v1/catalogs/{catalog_id}", json={"title": "New Title"}, headers=auth_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New Title"

    # Delete
    del_resp = client.delete(f"/api/v1/catalogs/{catalog_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # Ensure deleted
    get_resp = client.get(f"/api/v1/catalogs/{catalog_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_cross_user_catalog_isolation(client: TestClient, auth_headers: dict, auth_headers_b: dict):
    """Test User B cannot get, update, or delete User A's catalog."""
    create_resp = client.post("/api/v1/catalogs", json={"title": "User A Catalog"}, headers=auth_headers)
    catalog_id = create_resp.json()["id"]

    # User B tries GET
    assert client.get(f"/api/v1/catalogs/{catalog_id}", headers=auth_headers_b).status_code == 404

    # User B tries PUT
    assert client.put(f"/api/v1/catalogs/{catalog_id}", json={"title": "Hacked"}, headers=auth_headers_b).status_code == 404

    # User B tries DELETE
    assert client.delete(f"/api/v1/catalogs/{catalog_id}", headers=auth_headers_b).status_code == 404
