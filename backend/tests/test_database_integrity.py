import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command

from app.models import (
    User,
    Product,
    ProductImage,
    ProductAudio,
    Price,
    Catalog,
    Buyer,
    Enquiry,
    Notification,
)


def test_user_firebase_uid_uniqueness(client: TestClient, db_session):
    """Test database rejects duplicate firebase_uid insertion."""
    user1 = User(firebase_uid="unique_fb_uid_1", name="Artisan One")
    db_session.add(user1)
    db_session.commit()

    user2 = User(firebase_uid="unique_fb_uid_1", name="Artisan Duplicate")
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_catalog_product_unique_constraint(client: TestClient, auth_headers: dict):
    """Test duplicate association of a product to the same catalog is rejected with 409 Conflict."""
    # 1. Create product
    prod_resp = client.post("/api/v1/products", json={"name": "Silk Scarf", "raw_material_cost": 200.0}, headers=auth_headers)
    assert prod_resp.status_code == 201
    product_id = prod_resp.json()["id"]

    # 2. Create catalog
    cat_resp = client.post("/api/v1/catalogs", json={"title": "Silk Collection"}, headers=auth_headers)
    assert cat_resp.status_code == 201
    catalog_id = cat_resp.json()["id"]

    # 3. Add product to catalog (1st time -> 200 OK)
    add_resp = client.post(f"/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=auth_headers)
    assert add_resp.status_code == 200

    # 4. Add product again (2nd time -> 409 Conflict)
    dup_resp = client.post(f"/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=auth_headers)
    assert dup_resp.status_code == 409
    assert "already in this catalog" in dup_resp.json()["detail"].lower()


def test_product_cascade_deletion(client: TestClient, auth_headers: dict, db_session):
    """Test deleting a product cleanly cascades to dependent images, audio, prices, and enquiries."""
    # 1. Create product
    prod_resp = client.post("/api/v1/products", json={"name": "Terracotta Pot", "raw_material_cost": 150.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    # 2. Add price record directly to DB
    price = Price(
        product_id=product_id,
        recommended_price=300.0,
        minimum_price=250.0,
        maximum_price=400.0,
        reason="Test cascade pricing",
    )
    db_session.add(price)

    # 3. Add image and audio directly to DB
    img = ProductImage(product_id=product_id, original_url="https://example.com/pot.jpg")
    audio = ProductAudio(product_id=product_id, audio_url="https://example.com/pot.m4a")
    db_session.add(img)
    db_session.add(audio)

    # 4. Create buyer & enquiry
    buyer = Buyer(company="Cascade Buyer Ltd", name="Rohan", location="Delhi", category="Pottery & Terracotta")
    db_session.add(buyer)
    db_session.commit()

    enquiry = Enquiry(buyer_id=buyer.id, product_id=product_id, message="Interested in 50 pots")
    db_session.add(enquiry)
    db_session.commit()

    # Verify dependencies exist
    assert db_session.query(Price).filter(Price.product_id == product_id).count() == 1
    assert db_session.query(ProductImage).filter(ProductImage.product_id == product_id).count() == 1
    assert db_session.query(ProductAudio).filter(ProductAudio.product_id == product_id).count() == 1
    assert db_session.query(Enquiry).filter(Enquiry.product_id == product_id).count() == 1

    # 5. Delete product via API
    del_resp = client.delete(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # 6. Verify dependent records are cascade-deleted
    assert db_session.query(Price).filter(Price.product_id == product_id).count() == 0
    assert db_session.query(ProductImage).filter(ProductImage.product_id == product_id).count() == 0
    assert db_session.query(ProductAudio).filter(ProductAudio.product_id == product_id).count() == 0
    assert db_session.query(Enquiry).filter(Enquiry.product_id == product_id).count() == 0


def test_notification_set_null_on_product_deletion(client: TestClient, auth_headers: dict, db_session):
    """Test deleting a product sets notification related_product_id to NULL without deleting the notification."""
    # 1. Create product
    prod_resp = client.post("/api/v1/products", json={"name": "Brass Lamp"}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    # 2. Get user id
    me_resp = client.get("/api/v1/users/me", headers=auth_headers)
    user_id = me_resp.json()["id"]

    # 3. Create notification linked to product
    notif = Notification(
        user_id=user_id,
        type="system",
        title="Product Approved",
        message="Your brass lamp is approved",
        related_product_id=product_id,
    )
    db_session.add(notif)
    db_session.commit()
    notif_id = notif.id

    # 4. Delete product
    del_resp = client.delete(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert del_resp.status_code == 200

    # 5. Verify notification still exists with related_product_id = None
    db_session.expire_all()
    refreshed_notif = db_session.query(Notification).filter(Notification.id == notif_id).first()
    assert refreshed_notif is not None
    assert refreshed_notif.related_product_id is None


def test_catalog_publishing_rules(client: TestClient, auth_headers: dict):
    """Test that empty or draft-only catalogs cannot be published."""
    # 1. Create empty catalog
    cat_resp = client.post("/api/v1/catalogs", json={"title": "Empty Collection"}, headers=auth_headers)
    catalog_id = cat_resp.json()["id"]

    # 2. Try to publish empty catalog -> 400 Bad Request
    pub_resp = client.post(f"/api/v1/catalogs/{catalog_id}/publish", headers=auth_headers)
    assert pub_resp.status_code == 400
    assert "empty catalog" in pub_resp.json()["detail"].lower()

    # 3. Add a draft product to catalog
    prod_resp = client.post("/api/v1/products", json={"name": "Draft Bowl"}, headers=auth_headers)
    prod_id = prod_resp.json()["id"]
    client.post(f"/api/v1/catalogs/{catalog_id}/products/{prod_id}", headers=auth_headers)

    # 4. Try to publish catalog with only draft products -> 400 Bad Request
    pub_resp_draft = client.post(f"/api/v1/catalogs/{catalog_id}/publish", headers=auth_headers)
    assert pub_resp_draft.status_code == 400

    # 5. Process the product
    proc_resp = client.post(f"/api/v1/products/{prod_id}/process", headers=auth_headers)
    assert proc_resp.status_code == 200

    # 6. Now publish catalog -> 200 OK
    pub_success = client.post(f"/api/v1/catalogs/{catalog_id}/publish", headers=auth_headers)
    assert pub_success.status_code == 200
    assert pub_success.json()["status"] == "published"


def test_marketplace_visibility_rules(client: TestClient, auth_headers: dict):
    """Test marketplace query visibility based on product and catalog status."""
    # 1. Create draft product (should be HIDDEN from marketplace)
    draft_p = client.post("/api/v1/products", json={"name": "Hidden Draft Product"}, headers=auth_headers).json()

    # 2. Create processed product (not yet in published catalog -> HIDDEN)
    proc_p = client.post("/api/v1/products", json={"name": "Processed Product"}, headers=auth_headers).json()
    client.post(f"/api/v1/products/{proc_p['id']}/process", headers=auth_headers)

    # 3. Create published product directly -> VISIBLE
    pub_p = client.post("/api/v1/products", json={"name": "Published Product"}, headers=auth_headers).json()
    client.post(f"/api/v1/products/{pub_p['id']}/process", headers=auth_headers)
    client.post(f"/api/v1/products/{pub_p['id']}/publish", headers=auth_headers)

    # Query marketplace products
    market_resp = client.get("/api/v1/marketplace/products")
    assert market_resp.status_code == 200
    market_items = market_resp.json()
    market_ids = [item["id"] for item in market_items]

    assert pub_p["id"] in market_ids
    assert draft_p["id"] not in market_ids
    assert proc_p["id"] not in market_ids

    # 4. Now create a catalog, add proc_p to it, and publish the catalog
    cat = client.post("/api/v1/catalogs", json={"title": "Marketplace Catalog"}, headers=auth_headers).json()
    client.post(f"/api/v1/catalogs/{cat['id']}/products/{proc_p['id']}", headers=auth_headers)
    client.post(f"/api/v1/catalogs/{cat['id']}/publish", headers=auth_headers)

    # Query marketplace again -> proc_p is now visible because its catalog is published
    market_resp_after = client.get("/api/v1/marketplace/products")
    market_ids_after = [item["id"] for item in market_resp_after.json()]
    assert proc_p["id"] in market_ids_after
    assert draft_p["id"] not in market_ids_after


def test_invalid_enquiry_status_update(client: TestClient, auth_headers: dict, db_session):
    """Test updating an enquiry with an invalid status is rejected."""
    # Create buyer and product
    buyer = Buyer(company="Status Test Buyer", name="Ajay", location="Pune", category="Handicrafts")
    db_session.add(buyer)
    db_session.commit()

    prod = client.post("/api/v1/products", json={"name": "Clay Pot"}, headers=auth_headers).json()
    enq_resp = client.post(f"/api/v1/buyers/{buyer.id}/enquiries", json={"product_id": prod["id"], "message": "Inquiry test"}, headers=auth_headers)
    enquiry_id = enq_resp.json()["id"]

    # Try invalid status
    invalid_resp = client.put(f"/api/v1/enquiries/{enquiry_id}", json={"status": "invalid_status_xyz"}, headers=auth_headers)
    assert invalid_resp.status_code == 422


def test_fresh_database_initialization_from_alembic(tmp_path, monkeypatch):
    """Test that a completely fresh database can be initialized from scratch via Alembic migrations."""
    fresh_db_path = str(tmp_path / "fresh_test.db")
    fresh_db_url = f"sqlite:///{fresh_db_path}"

    monkeypatch.setenv("DATABASE_URL", fresh_db_url)

    # Configure Alembic with fresh database URL
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", fresh_db_url)

    # Run upgrade head
    command.upgrade(alembic_cfg, "head")

    # Connect to fresh DB and verify all 10 required tables exist
    test_engine = create_engine(fresh_db_url)
    with test_engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = {row[0] for row in result.fetchall()}

    expected_tables = {
        "users",
        "products",
        "product_images",
        "product_audio",
        "prices",
        "catalogs",
        "catalog_products",
        "buyers",
        "enquiries",
        "notifications",
    }
    assert expected_tables.issubset(tables), f"Missing tables in fresh DB: {expected_tables - tables}"
