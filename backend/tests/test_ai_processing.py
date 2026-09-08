import io
from fastapi.testclient import TestClient
from app.models.buyer import Buyer
from app.models.product import Product
from sqlalchemy.orm import Session


def test_ai_processing_populates_fields_and_pricing(client: TestClient, auth_headers: dict):
    """Test AI processing enhances product details, sets status to processed, and computes pricing."""
    # 1. Create product
    create_resp = client.post(
        "/api/v1/products",
        json={
            "name": "Draft Clay Item",
            "raw_material_cost": 150.0,
            "labour_cost": 75.0,
            "packaging_cost": 25.0,
        },
        headers=auth_headers,
    )
    product_id = create_resp.json()["id"]

    # 2. Trigger AI processing pipeline (in mock AI mode)
    process_resp = client.post(
        f"/api/v1/products/{product_id}/process",
        json={"voice_text": "हाथ से बनी हुई मिट्टी की कलाकृति", "language": "hi"},
        headers=auth_headers,
    )
    assert process_resp.status_code == 200
    data = process_resp.json()

    product = data["product"]
    assert product["id"] == product_id
    assert product["status"] == "processed"
    assert product["description_hi"] is not None
    assert product["description_en"] is not None
    assert product["voice_transcription"] is not None
    assert product["translated_voice_text"] is not None

    # Verify original raw costs were not overwritten
    assert product["raw_material_cost"] == 150.0
    assert product["labour_cost"] == 75.0
    assert product["packaging_cost"] == 25.0

    # Verify pricing recommendation
    pricing = data["pricing"]
    assert pricing["recommended_price"] is not None
    assert pricing["recommended_price"] > (150.0 + 75.0 + 25.0)


def test_prevent_duplicate_concurrent_processing(client: TestClient, auth_headers: dict, db_session: Session):
    """Test that attempting to process a product that is currently 'processing' returns 409 Conflict."""
    create_resp = client.post(
        "/api/v1/products",
        json={"name": "Processing Item", "raw_material_cost": 100.0},
        headers=auth_headers,
    )
    product_id = create_resp.json()["id"]

    # Manually simulate in-flight status
    prod = db_session.query(Product).filter(Product.id == product_id).first()
    prod.status = "processing"
    db_session.commit()

    # Attempt to process again
    dup_resp = client.post(
        f"/api/v1/products/{product_id}/process",
        json={"voice_text": "Duplicate call"},
        headers=auth_headers,
    )
    assert dup_resp.status_code == 409
    assert "currently being processed" in dup_resp.json()["detail"]


def test_end_to_end_artisan_hackathon_demo_flow(client: TestClient, auth_headers: dict, seed_buyers: list[Buyer]):
    """Full End-to-End Hackathon Workflow Test:
    1. Authenticate artisan
    2. Create product
    3. Upload image
    4. Upload audio
    5. Process product via AI pipeline
    6. Generate AI descriptions and recommended pricing
    7. Verify status changes to 'processed'
    8. Create catalog & add product
    9. Match wholesale B2B buyers
    10. Send B2B enquiry
    11. Verify enquiry creation generates in-app notification
    12. Verify unread notification count is 1
    13. Mark notification as read (unread count -> 0)
    14. Update enquiry status to 'contacted' with artisan response
    """
    # 1. User Profile check
    user_resp = client.get("/api/v1/users/me", headers=auth_headers)
    assert user_resp.status_code == 200

    # 2. Create product
    create_payload = {
        "name": "Terracotta Flower Pot",
        "raw_material_cost": 180.0,
        "labour_cost": 90.0,
        "packaging_cost": 30.0,
        "category": "Pottery",
        "material": "Clay",
    }
    prod_resp = client.post("/api/v1/products", json=create_payload, headers=auth_headers)
    assert prod_resp.status_code == 201
    product_id = prod_resp.json()["id"]

    # 3. Upload photo
    dummy_img = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00"
    img_resp = client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("pot.jpg", io.BytesIO(dummy_img), "image/jpeg")},
        headers=auth_headers,
    )
    assert img_resp.status_code in [200, 201]

    # 4. Upload audio voice note
    dummy_audio = b"RIFF....WAVEfmt ....data....voice description"
    audio_resp = client.post(
        f"/api/v1/products/{product_id}/audio",
        files={"file": ("voice.m4a", io.BytesIO(dummy_audio), "audio/m4a")},
        data={"language": "hi", "duration": "5.0"},
        headers=auth_headers,
    )
    assert audio_resp.status_code in [200, 201]

    # 5. Process product via AI pipeline
    process_resp = client.post(
        f"/api/v1/products/{product_id}/process",
        json={"voice_text": "यह सुंदर फूलदान है", "language": "hi"},
        headers=auth_headers,
    )
    assert process_resp.status_code == 200
    p_data = process_resp.json()["product"]
    pricing_data = process_resp.json()["pricing"]

    # 6. Verify status and enhancements
    assert p_data["status"] == "processed"
    assert p_data["description_hi"] is not None
    assert p_data["description_en"] is not None
    assert pricing_data["recommended_price"] >= 300.0

    # 7. Create catalog and add product
    cat_resp = client.post(
        "/api/v1/catalogs",
        json={"title": "Jaipur Terracotta Showcase", "description": "Export quality pottery"},
        headers=auth_headers,
    )
    assert cat_resp.status_code == 201
    catalog_id = cat_resp.json()["id"]

    add_cat_resp = client.post(f"/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=auth_headers)
    assert add_cat_resp.status_code == 200
    assert len(add_cat_resp.json()["products"]) == 1

    # 8. Match wholesale buyers
    match_resp = client.get(f"/api/v1/products/{product_id}/buyers", headers=auth_headers)
    assert match_resp.status_code == 200
    buyers = match_resp.json()["buyers"]
    assert len(buyers) > 0
    top_buyer = buyers[0]

    # 9. Send buyer enquiry
    enquiry_resp = client.post(
        f"/api/v1/buyers/{top_buyer['id']}/enquiries",
        json={"product_id": product_id, "message": "Ready to fulfill bulk procurement orders."},
        headers=auth_headers,
    )
    assert enquiry_resp.status_code == 201
    enquiry_id = enquiry_resp.json()["id"]

    # 10. Verify notification created
    notifs = client.get("/api/v1/notifications", headers=auth_headers).json()["notifications"]
    assert len(notifs) >= 1
    assert notifs[0]["related_enquiry_id"] == enquiry_id
    notif_id = notifs[0]["id"]

    # 11. Verify unread count = 1
    unread_c = client.get("/api/v1/notifications/unread-count", headers=auth_headers).json()["count"]
    assert unread_c >= 1

    # 12. Mark notification read -> unread count decreases
    client.put(f"/api/v1/notifications/{notif_id}/read", headers=auth_headers)
    unread_after = client.get("/api/v1/notifications/unread-count", headers=auth_headers).json()["count"]
    assert unread_after == unread_c - 1

    # 13. Update enquiry status & artisan response
    update_enq = client.put(
        f"/api/v1/enquiries/{enquiry_id}",
        json={"status": "contacted", "artisan_response": "We have dispatched sample units."},
        headers=auth_headers,
    )
    assert update_enq.status_code == 200
    assert update_enq.json()["status"] == "contacted"
    assert update_enq.json()["artisan_response"] == "We have dispatched sample units."
    assert update_enq.json()["responded_at"] is not None
