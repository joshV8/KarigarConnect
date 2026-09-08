from fastapi.testclient import TestClient


def test_calculate_pricing_mathematical_consistency(client: TestClient, auth_headers: dict):
    """Test pricing calculation with Raw material=300, Labour=200, Packaging=50, Margin=20%."""
    # Create a product with specified costs
    create_resp = client.post(
        "/api/v1/products",
        json={
            "name": "Handmade Silk Stole",
            "raw_material_cost": 300.0,
            "labour_cost": 200.0,
            "packaging_cost": 50.0,
        },
        headers=auth_headers,
    )
    product_id = create_resp.json()["id"]

    # Calculate price with 20% margin
    price_resp = client.post(
        f"/api/v1/products/{product_id}/pricing",
        json={"margin_percent": 20.0},
        headers=auth_headers,
    )
    assert price_resp.status_code in [200, 201]
    p = price_resp.json()

    # Base cost = 300 + 200 + 50 = 550
    # Recommended = round(550 * 1.20) = 660.0
    # Min = round(max(550, 660 * 0.85)) = 561.0
    # Max = round(max(660, 660 * 1.25)) = 825.0
    assert p["recommended_price"] == 660.0
    assert p["minimum_price"] == 561.0
    assert p["maximum_price"] == 825.0
    assert "20% artisan profit margin" in p["reason"]


def test_get_current_pricing(client: TestClient, auth_headers: dict):
    """Test retrieving latest calculated price."""
    create_resp = client.post(
        "/api/v1/products",
        json={"name": "Wooden Toy", "raw_material_cost": 100.0, "labour_cost": 50.0},
        headers=auth_headers,
    )
    product_id = create_resp.json()["id"]

    # Compute price
    client.post(f"/api/v1/products/{product_id}/pricing", headers=auth_headers)

    # Get price
    get_resp = client.get(f"/api/v1/products/{product_id}/pricing", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["recommended_price"] is not None


def test_pricing_history_stores_multiple_records(client: TestClient, auth_headers: dict):
    """Test multiple recalculations create separate history entries."""
    create_resp = client.post(
        "/api/v1/products",
        json={"name": "Brass Bell", "raw_material_cost": 200.0, "labour_cost": 100.0},
        headers=auth_headers,
    )
    product_id = create_resp.json()["id"]

    # 1st calculation: 20% margin
    client.post(f"/api/v1/products/{product_id}/pricing", json={"margin_percent": 20.0}, headers=auth_headers)
    # 2nd calculation: 30% margin
    client.post(f"/api/v1/products/{product_id}/pricing", json={"margin_percent": 30.0}, headers=auth_headers)

    # Fetch history
    hist_resp = client.get(f"/api/v1/products/{product_id}/pricing/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2
    # Latest calculation first
    assert history[0]["recommended_price"] > history[1]["recommended_price"]
