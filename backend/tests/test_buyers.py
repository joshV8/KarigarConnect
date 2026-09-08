from fastapi.testclient import TestClient
from app.models.buyer import Buyer


def test_list_and_get_buyers_public(client: TestClient, seed_buyers: list[Buyer]):
    """Test public listing and single retrieval of B2B wholesale buyers."""
    list_resp = client.get("/api/v1/buyers")
    assert list_resp.status_code == 200
    buyers = list_resp.json()
    assert len(buyers) >= 3

    buyer_id = buyers[0]["id"]
    get_resp = client.get(f"/api/v1/buyers/{buyer_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == buyer_id


def test_filter_buyers_by_category(client: TestClient, seed_buyers: list[Buyer]):
    """Test filtering buyers by category query parameter."""
    resp = client.get("/api/v1/buyers?category=Textiles")
    assert resp.status_code == 200
    buyers = resp.json()
    assert all("Textiles" in b["category"] for b in buyers)


def test_buyer_matching_algorithm(client: TestClient, auth_headers: dict, seed_buyers: list[Buyer]):
    """Test matching algorithm scores and ranks buyers based on category, material, and price."""
    # Create a Pottery product
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": "Handmade Clay Jug",
            "category": "Pottery",
            "material": "Clay",
            "raw_material_cost": 200.0,
            "labour_cost": 100.0,
            "packaging_cost": 20.0,
        },
        headers=auth_headers,
    )
    product_id = prod_resp.json()["id"]

    # Calculate pricing
    client.post(f"/api/v1/products/{product_id}/pricing", headers=auth_headers)

    # Request matching buyers
    match_resp = client.get(f"/api/v1/products/{product_id}/buyers", headers=auth_headers)
    assert match_resp.status_code == 200
    data = match_resp.json()
    assert data["product_id"] == product_id
    matched_buyers = data["buyers"]
    assert len(matched_buyers) > 0

    # The Pottery buyer (Good Earth Retail) should score highest
    top_buyer = matched_buyers[0]
    assert top_buyer["company"] == "Good Earth Retail"
    assert top_buyer["match_score"] > 50.0
    assert len(top_buyer["match_reasons"]) > 0
