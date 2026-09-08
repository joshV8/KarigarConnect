from fastapi.testclient import TestClient
from app.models.buyer import Buyer


def test_send_and_list_enquiries(client: TestClient, auth_headers: dict, seed_buyers: list[Buyer]):
    """Test creating an enquiry to a B2B wholesale buyer and retrieving it for the product."""
    # Create product for User A
    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Handmade Silk Saree", "raw_material_cost": 500.0},
        headers=auth_headers,
    )
    product_id = prod_resp.json()["id"]
    buyer_id = seed_buyers[0].id

    # Send enquiry
    enquiry_payload = {
        "product_id": product_id,
        "message": "We have 100 units ready for wholesale procurement.",
    }
    send_resp = client.post(
        f"/api/v1/buyers/{buyer_id}/enquiries",
        json=enquiry_payload,
        headers=auth_headers,
    )
    assert send_resp.status_code == 201
    enq = send_resp.json()
    assert enq["buyer_id"] == buyer_id
    assert enq["product_id"] == product_id
    assert enq["message"] == "We have 100 units ready for wholesale procurement."
    assert enq["status"] == "pending"

    # List enquiries for product
    list_resp = client.get(f"/api/v1/products/{product_id}/enquiries", headers=auth_headers)
    assert list_resp.status_code == 200
    enquiries = list_resp.json()
    assert len(enquiries) == 1
    assert enquiries[0]["id"] == enq["id"]


def test_get_and_update_single_enquiry(client: TestClient, auth_headers: dict, seed_buyers: list[Buyer]):
    """Test retrieving and responding to a single enquiry (status update + artisan response)."""
    # Create product
    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Jaipur Blue Pottery Bowl", "raw_material_cost": 150.0},
        headers=auth_headers,
    )
    product_id = prod_resp.json()["id"]
    buyer_id = seed_buyers[0].id

    # Create enquiry
    enq_resp = client.post(
        f"/api/v1/buyers/{buyer_id}/enquiries",
        json={"product_id": product_id, "message": "Can you provide 50 bowls by next month?"},
        headers=auth_headers,
    )
    enquiry_id = enq_resp.json()["id"]

    # 1. GET /enquiries/{enquiry_id}
    get_resp = client.get(f"/api/v1/enquiries/{enquiry_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == enquiry_id
    assert get_resp.json()["status"] == "pending"

    # 2. PUT /enquiries/{enquiry_id} -> contacted + response
    update_payload = {
        "status": "contacted",
        "artisan_response": "Yes, we can deliver 50 units within 20 days.",
    }
    put_resp = client.put(f"/api/v1/enquiries/{enquiry_id}", json=update_payload, headers=auth_headers)
    assert put_resp.status_code == 200
    updated_enq = put_resp.json()
    assert updated_enq["status"] == "contacted"
    assert updated_enq["artisan_response"] == "Yes, we can deliver 50 units within 20 days."
    assert updated_enq["responded_at"] is not None

    # 3. Transition status to accepted
    accept_resp = client.put(
        f"/api/v1/enquiries/{enquiry_id}",
        json={"status": "accepted"},
        headers=auth_headers,
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"
    # Preserves previous response
    assert accept_resp.json()["artisan_response"] == "Yes, we can deliver 50 units within 20 days."


def test_cross_user_enquiry_isolation(client: TestClient, auth_headers: dict, auth_headers_b: dict, seed_buyers: list[Buyer]):
    """Test User B cannot view or update User A's enquiries."""
    # User A creates product & enquiry
    prod_resp = client.post("/api/v1/products", json={"name": "User A Pot", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]
    buyer_id = seed_buyers[0].id

    enq_resp = client.post(
        f"/api/v1/buyers/{buyer_id}/enquiries",
        json={"product_id": product_id, "message": "Inquiry for user A"},
        headers=auth_headers,
    )
    enquiry_id = enq_resp.json()["id"]

    # User B tries GET /enquiries/{id}
    assert client.get(f"/api/v1/enquiries/{enquiry_id}", headers=auth_headers_b).status_code == 404

    # User B tries PUT /enquiries/{id}
    assert client.put(
        f"/api/v1/enquiries/{enquiry_id}",
        json={"status": "rejected", "artisan_response": "Unauthorized rejection"},
        headers=auth_headers_b,
    ).status_code == 404
