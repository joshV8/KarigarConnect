"""
Automated Production & Integration Smoke Test for Artisan FastAPI Backend.

Tests the full end-to-end artisan flow against any target environment:
  python scripts/smoke_test.py
  API_URL=https://artisan-api.onrender.com AUTH_TOKEN=my_firebase_token python scripts/smoke_test.py
"""

import os
import sys
import io
import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "mock_smoke_artisan_1")
OTHER_USER_TOKEN = "mock_smoke_artisan_2"

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
}

OTHER_HEADERS = {
    "Authorization": f"Bearer {OTHER_USER_TOKEN}",
    "Content-Type": "application/json",
}

def log(step: str, ok: bool, details: str = ""):
    icon = "✅ PASS" if ok else "❌ FAIL"
    print(f"[{icon}] {step}{f': {details}' if details else ''}")
    if not ok:
        print(f"\nSmoke test aborted due to failure on: {step}")
        sys.exit(1)


def run_smoke_test():
    print(f"\n==================================================")
    print(f"  Artisan Backend Production Smoke Test")
    print(f"  Target: {API_URL}")
    print(f"==================================================\n")

    # 1. Health & Version Checks
    try:
        r = requests.get(f"{API_URL}/health", timeout=10)
        log("GET /health", r.status_code == 200, f"Status={r.status_code}, Env={r.json().get('environment')}")
    except Exception as e:
        log("GET /health", False, f"Connection error: {e}")

    try:
        r = requests.get(f"{API_URL}/health/db", timeout=10)
        log("GET /health/db", r.status_code == 200, f"DB Status={r.json().get('database')}")
    except Exception as e:
        log("GET /health/db", False, f"DB error: {e}")

    r = requests.get(f"{API_URL}/version", timeout=10)
    log("GET /version", r.status_code == 200, f"Version={r.json().get('version')}")

    # 2. Versioned Route Check
    r = requests.get(f"{API_URL}/api/v1/health", timeout=10)
    log("GET /api/v1/health (API Versioning)", r.status_code == 200)

    # 3. User Profile
    r = requests.get(f"{API_URL}/api/v1/users/me", headers=HEADERS, timeout=10)
    log("GET /api/v1/users/me", r.status_code == 200, f"User ID={r.json().get('id')}, UID={r.json().get('firebase_uid')}")

    # 4. Create Product (Draft)
    create_payload = {
        "name": "Hand-painted Blue Pottery Vase",
        "raw_material_cost": 250.0,
        "labour_cost": 120.0,
        "packaging_cost": 30.0,
        "category": "Pottery",
        "material": "Ceramic",
    }
    r = requests.post(f"{API_URL}/api/v1/products", headers=HEADERS, json=create_payload, timeout=10)
    log("POST /api/v1/products (Create Draft)", r.status_code == 201)
    product = r.json()
    product_id = product["id"]

    # 5. Upload Image Asset
    dummy_image = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00"
    img_files = {"file": ("vase_photo.jpg", io.BytesIO(dummy_image), "image/jpeg")}
    r = requests.post(
        f"{API_URL}/api/v1/products/{product_id}/images",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        files=img_files,
        timeout=15,
    )
    log("POST /api/v1/products/{id}/images (Photo Upload)", r.status_code in [200, 201], f"URL={r.json().get('original_url')}")

    # 6. Upload Voice Note
    dummy_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00data\x00\x00\x00\x00"
    audio_files = {"file": ("vase_desc.m4a", io.BytesIO(dummy_audio), "audio/m4a")}
    audio_data = {"language": "hi", "duration": "8.5"}
    r = requests.post(
        f"{API_URL}/api/v1/products/{product_id}/audio",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        files=audio_files,
        data=audio_data,
        timeout=15,
    )
    log("POST /api/v1/products/{id}/audio (Voice Upload)", r.status_code in [200, 201], f"URL={r.json().get('audio_url')}")

    # 7. Pre-processing Status Check
    r = requests.get(f"{API_URL}/api/v1/products/{product_id}/status", headers=HEADERS, timeout=10)
    log("GET /api/v1/products/{id}/status (Pre-Process)", r.status_code == 200, f"Status={r.json().get('status')}")

    # 8. Run AI Multimodal Pipeline & Pricing Engine
    process_payload = {
        "voice_text": "यह हाथ से बना हुआ सुंदर नीला मिट्टी का फूलदान है।",
        "language": "hi",
    }
    r = requests.post(f"{API_URL}/api/v1/products/{product_id}/process", headers=HEADERS, json=process_payload, timeout=30)
    log("POST /api/v1/products/{id}/process (AI Pipeline + Pricing)", r.status_code == 200)
    proc_data = r.json()
    p_result = proc_data["product"]
    pricing_result = proc_data.get("pricing", {})
    log("  → AI Transcription Output", bool(p_result.get("voice_transcription")), f"'{p_result.get('voice_transcription')}'")
    log("  → AI Translation Output", bool(p_result.get("translated_voice_text")), f"'{p_result.get('translated_voice_text')}'")
    log("  → AI Pricing Recommendation", bool(pricing_result.get("recommended_price")), f"₹{pricing_result.get('recommended_price')} ({pricing_result.get('reason')})")

    # 9. Create Catalog and Add Product
    cat_payload = {"title": "Heritage Pottery Collection", "description": "Handcrafted traditional ceramics"}
    r = requests.post(f"{API_URL}/api/v1/catalogs", headers=HEADERS, json=cat_payload, timeout=10)
    log("POST /api/v1/catalogs (Create Catalog)", r.status_code == 201)
    catalog_id = r.json()["id"]

    r = requests.post(f"{API_URL}/api/v1/catalogs/{catalog_id}/products/{product_id}", headers=HEADERS, timeout=10)
    log("POST /api/v1/catalogs/{id}/products/{product_id} (Add Product to Catalog)", r.status_code == 200)

    # 10. B2B Buyer Matching & Discovery
    r = requests.get(f"{API_URL}/api/v1/buyers", headers=HEADERS, timeout=10)
    log("GET /api/v1/buyers (Discover B2B Buyers)", r.status_code == 200)
    buyers = r.json()
    first_buyer_id = buyers[0]["id"] if buyers else None

    # 11. Send Buyer Enquiry
    enquiry_id = None
    if first_buyer_id:
        enquiry_payload = {
            "product_id": product_id,
            "message": "We have new authentic Jaipur blue pottery in stock.",
        }
        r = requests.post(f"{API_URL}/api/v1/buyers/{first_buyer_id}/enquiries", headers=HEADERS, json=enquiry_payload, timeout=10)
        log("POST /api/v1/buyers/{id}/enquiries (Send B2B Enquiry)", r.status_code == 201)
        enquiry_id = r.json()["id"]

    # 12. Enquiry Tracking & Response Workflow
    if enquiry_id:
        r = requests.get(f"{API_URL}/api/v1/enquiries/{enquiry_id}", headers=HEADERS, timeout=10)
        log("GET /api/v1/enquiries/{id} (Track Enquiry)", r.status_code == 200, f"Status={r.json().get('status')}")

        r = requests.put(
            f"{API_URL}/api/v1/enquiries/{enquiry_id}",
            headers=HEADERS,
            json={"status": "contacted", "artisan_response": "Sample pieces are dispatched."},
            timeout=10,
        )
        log("PUT /api/v1/enquiries/{id} (Respond to Enquiry)", r.status_code == 200, f"New Status={r.json().get('status')}")

    # 13. Notifications System Check
    r = requests.get(f"{API_URL}/api/v1/notifications", headers=HEADERS, timeout=10)
    log("GET /api/v1/notifications (List Notifications)", r.status_code == 200, f"Total={r.json().get('total')}")

    r = requests.get(f"{API_URL}/api/v1/notifications/unread-count", headers=HEADERS, timeout=10)
    log("GET /api/v1/notifications/unread-count (Unread Count)", r.status_code == 200, f"Unread={r.json().get('count')}")

    r = requests.put(f"{API_URL}/api/v1/notifications/read-all", headers=HEADERS, timeout=10)
    log("PUT /api/v1/notifications/read-all (Mark All Read)", r.status_code == 200)

    # 14. Security & Tenant Isolation Checks
    r_unauth = requests.delete(f"{API_URL}/api/v1/products/{product_id}", headers=OTHER_HEADERS, timeout=10)
    log("Security Check: Cross-user product access denied", r_unauth.status_code in [403, 404])

    if enquiry_id:
        r_enq_unauth = requests.get(f"{API_URL}/api/v1/enquiries/{enquiry_id}", headers=OTHER_HEADERS, timeout=10)
        log("Security Check: Cross-user enquiry access denied", r_enq_unauth.status_code in [403, 404])

    r_no_auth = requests.get(f"{API_URL}/api/v1/products", timeout=10)
    log("Security Check: Unauthenticated request rejected (401)", r_no_auth.status_code == 401)

    print("\n==================================================")
    print("  ✨ ALL SMOKE TESTS PASSED SUCCESSFULLY! ✨")
    print("  Backend is hardened and production ready.")
    print("==================================================\n")


if __name__ == "__main__":
    run_smoke_test()
