import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer mock_artisan_test"}


def test_full_phase9_voice_ai_pipeline():
    # 1. Create a draft product
    create_payload = {
        "name": "Handmade Clay Lamp",
        "raw_material_cost": 80.0,
        "labour_cost": 40.0,
        "packaging_cost": 15.0,
        "category": "Pottery",
        "material": "Terracotta",
    }
    create_resp = client.post("/products", json=create_payload, headers=AUTH_HEADERS)
    assert create_resp.status_code == 201
    product = create_resp.json()
    product_id = product["id"]
    assert product["status"] == "draft"

    # 2. Check initial status
    status_resp = client.get(f"/products/{product_id}/status", headers=AUTH_HEADERS)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "draft"

    # 3. Upload voice recording
    dummy_audio = b"RIFF....WAVEfmt ....data....artisan voice audio"
    files = {"file": ("recording.m4a", io.BytesIO(dummy_audio), "audio/m4a")}
    data = {"language": "hi", "duration": "6.5"}
    audio_resp = client.post(f"/products/{product_id}/audio", files=files, data=data, headers=AUTH_HEADERS)
    assert audio_resp.status_code == 201
    audio_data = audio_resp.json()
    assert audio_data["product_id"] == product_id
    assert "audio_url" in audio_data
    assert audio_data["language"] == "hi"

    # 4. List audio records for product
    list_audio = client.get(f"/products/{product_id}/audio", headers=AUTH_HEADERS)
    assert list_audio.status_code == 200
    assert len(list_audio.json()) == 1

    # 5. Process AI pipeline
    process_payload = {
        "voice_text": "यह हस्तनिर्मित दीपक है।",
        "language": "hi",
    }
    process_resp = client.post(f"/products/{product_id}/process", json=process_payload, headers=AUTH_HEADERS)
    assert process_resp.status_code == 200
    proc_json = process_resp.json()
    assert "product" in proc_json
    assert "pricing" in proc_json

    p = proc_json["product"]
    assert p["status"] == "processed"
    assert p["voice_transcription"] is not None
    assert p["translated_voice_text"] is not None
    assert p["description_hi"] is not None
    assert p["description_en"] is not None

    # 6. Status check post-processing
    status_post = client.get(f"/products/{product_id}/status", headers=AUTH_HEADERS)
    assert status_post.status_code == 200
    assert status_post.json()["status"] == "processed"

    # 7. Verify product details retrieval includes audio recordings and voice transcription
    get_resp = client.get(f"/products/{product_id}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    p_full = get_resp.json()
    assert p_full["voice_transcription"] == p["voice_transcription"]
    assert len(p_full["audio_recordings"]) >= 1
