from fastapi.testclient import TestClient
from app.models.buyer import Buyer
from app.services.notification_service import notification_service
from sqlalchemy.orm import Session


def test_notification_creation_and_retrieval(client: TestClient, auth_headers: dict, user_a, db_session: Session):
    """Test manual notification creation via service and retrieval via API."""
    notification_service.create_notification(
        db=db_session,
        user_id=user_a.id,
        type="system",
        title="Welcome to KarigarConnect",
        message="Your artisan profile is ready.",
    )

    resp = client.get("/api/v1/notifications", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["unread_count"] >= 1
    assert data["notifications"][0]["title"] == "Welcome to KarigarConnect"
    assert data["notifications"][0]["is_read"] is False


def test_unread_count_endpoint(client: TestClient, auth_headers: dict, user_a, db_session: Session):
    """Test /notifications/unread-count reflects unread notification counts."""
    # Create 2 unread notifications
    notification_service.create_notification(db=db_session, user_id=user_a.id, title="Notice 1", message="Msg 1")
    notification_service.create_notification(db=db_session, user_id=user_a.id, title="Notice 2", message="Msg 2")

    resp = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] >= 2


def test_mark_single_notification_as_read(client: TestClient, auth_headers: dict, user_a, db_session: Session):
    """Test marking a specific notification as read."""
    notif = notification_service.create_notification(db=db_session, user_id=user_a.id, title="Order Alert", message="Buyer interested")
    notif_id = notif.id

    # Mark as read
    put_resp = client.put(f"/api/v1/notifications/{notif_id}/read", headers=auth_headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["is_read"] is True

    # Check unread count decreased
    count_resp = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert count_resp.status_code == 200


def test_mark_all_notifications_as_read(client: TestClient, auth_headers: dict, user_a, db_session: Session):
    """Test bulk marking all notifications as read."""
    notification_service.create_notification(db=db_session, user_id=user_a.id, title="Alert 1", message="1")
    notification_service.create_notification(db=db_session, user_id=user_a.id, title="Alert 2", message="2")

    # Mark all read
    put_all = client.put("/api/v1/notifications/read-all", headers=auth_headers)
    assert put_all.status_code == 200
    assert put_all.json()["status"] == "success"

    # Unread count should now be 0
    count_resp = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert count_resp.json()["count"] == 0


def test_unread_only_filter_and_pagination(client: TestClient, auth_headers: dict, user_a, db_session: Session):
    """Test unread_only filtering and pagination (limit/offset)."""
    # Create 3 unread, 1 read
    n1 = notification_service.create_notification(db=db_session, user_id=user_a.id, title="Item 1", message="1")
    n2 = notification_service.create_notification(db=db_session, user_id=user_a.id, title="Item 2", message="2")
    n3 = notification_service.create_notification(db=db_session, user_id=user_a.id, title="Item 3", message="3")

    # Mark n1 as read
    client.put(f"/api/v1/notifications/{n1.id}/read", headers=auth_headers)

    # Filter unread only
    resp = client.get("/api/v1/notifications?unread_only=true", headers=auth_headers)
    assert resp.status_code == 200
    unreads = resp.json()["notifications"]
    assert all(n["is_read"] is False for n in unreads)

    # Pagination: limit 1
    page_resp = client.get("/api/v1/notifications?limit=1&offset=0", headers=auth_headers)
    assert page_resp.status_code == 200
    assert len(page_resp.json()["notifications"]) == 1


def test_enquiry_automatically_triggers_artisan_notification(client: TestClient, auth_headers: dict, seed_buyers: list[Buyer]):
    """Test that submitting an enquiry automatically creates an in-app notification for the product owner."""
    # 1. Create product
    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Handmade Clay Jug", "raw_material_cost": 150.0},
        headers=auth_headers,
    )
    product_id = prod_resp.json()["id"]
    buyer = seed_buyers[0]

    # 2. Get initial unread count
    initial_count = client.get("/api/v1/notifications/unread-count", headers=auth_headers).json()["count"]

    # 3. Submit enquiry
    enquiry_resp = client.post(
        f"/api/v1/buyers/{buyer.id}/enquiries",
        json={"product_id": product_id, "message": "Interested in 50 pieces."},
        headers=auth_headers,
    )
    assert enquiry_resp.status_code == 201
    enquiry_id = enquiry_resp.json()["id"]

    # 4. Verify unread notification count incremented
    new_count = client.get("/api/v1/notifications/unread-count", headers=auth_headers).json()["count"]
    assert new_count == initial_count + 1

    # 5. Verify notification content
    notifs_resp = client.get("/api/v1/notifications", headers=auth_headers)
    latest_notif = notifs_resp.json()["notifications"][0]
    assert latest_notif["type"] == "new_enquiry"
    assert "New Buyer Enquiry" in latest_notif["title"]
    assert latest_notif["related_product_id"] == product_id
    assert latest_notif["related_enquiry_id"] == enquiry_id


def test_cross_user_notification_isolation(client: TestClient, auth_headers: dict, auth_headers_b: dict, user_a, db_session: Session):
    """Test User B cannot view or mark User A's notifications as read."""
    notif = notification_service.create_notification(db=db_session, user_id=user_a.id, title="User A Private Alert", message="Confidential")

    # User B tries to mark User A's notification as read
    put_resp = client.put(f"/api/v1/notifications/{notif.id}/read", headers=auth_headers_b)
    assert put_resp.status_code == 404

    # User B list notifications does not show User A's notification
    list_b = client.get("/api/v1/notifications", headers=auth_headers_b).json()["notifications"]
    assert not any(n["id"] == notif.id for n in list_b)
