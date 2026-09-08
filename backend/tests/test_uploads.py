import io
from fastapi.testclient import TestClient


def test_upload_valid_jpeg_and_png_image(client: TestClient, auth_headers: dict):
    """Test uploading valid JPEG and PNG product images."""
    prod_resp = client.post("/api/v1/products", json={"name": "Vase", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    # Upload JPEG
    jpeg_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00"
    jpeg_resp = client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("photo.jpg", io.BytesIO(jpeg_data), "image/jpeg")},
        headers=auth_headers,
    )
    assert jpeg_resp.status_code in [200, 201]
    assert jpeg_resp.json()["original_url"] is not None

    # Upload PNG
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    png_resp = client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("photo.png", io.BytesIO(png_data), "image/png")},
        headers=auth_headers,
    )
    assert png_resp.status_code in [200, 201]


def test_upload_invalid_image_type_rejected(client: TestClient, auth_headers: dict):
    """Test uploading non-image file (.txt / .pdf) is rejected with 400 Bad Request."""
    prod_resp = client.post("/api/v1/products", json={"name": "Lamp", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    txt_data = b"Some plain text document"
    txt_resp = client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("notes.txt", io.BytesIO(txt_data), "text/plain")},
        headers=auth_headers,
    )
    assert txt_resp.status_code == 400


def test_list_and_delete_product_images(client: TestClient, auth_headers: dict):
    """Test listing images and deleting an image."""
    prod_resp = client.post("/api/v1/products", json={"name": "Sculpture", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    jpeg_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00"
    upload_resp = client.post(
        f"/api/v1/products/{product_id}/images",
        files={"file": ("img1.jpg", io.BytesIO(jpeg_data), "image/jpeg")},
        headers=auth_headers,
    )
    img_id = upload_resp.json()["id"]

    # List images
    list_resp = client.get(f"/api/v1/products/{product_id}/images", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Delete image
    del_resp = client.delete(f"/api/v1/products/{product_id}/images/{img_id}", headers=auth_headers)
    assert del_resp.status_code == 200


def test_upload_valid_audio_recording(client: TestClient, auth_headers: dict):
    """Test uploading supported audio formats (.m4a, .wav)."""
    prod_resp = client.post("/api/v1/products", json={"name": "Bamboo Bag", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    dummy_audio = b"RIFF....WAVEfmt ....data....artisan voice audio"
    audio_resp = client.post(
        f"/api/v1/products/{product_id}/audio",
        files={"file": ("voice.m4a", io.BytesIO(dummy_audio), "audio/m4a")},
        data={"language": "hi", "duration": "6.2"},
        headers=auth_headers,
    )
    assert audio_resp.status_code == 201
    audio_data = audio_resp.json()
    assert audio_data["product_id"] == product_id
    assert audio_data["language"] == "hi"
    assert audio_data["duration"] == 6.2
    assert "audio_url" in audio_data


def test_upload_invalid_audio_type_rejected(client: TestClient, auth_headers: dict):
    """Test uploading unsupported file to audio endpoint is rejected with 400 Bad Request."""
    prod_resp = client.post("/api/v1/products", json={"name": "Carpet", "raw_material_cost": 100.0}, headers=auth_headers)
    product_id = prod_resp.json()["id"]

    pdf_data = b"%PDF-1.4 file contents"
    pdf_resp = client.post(
        f"/api/v1/products/{product_id}/audio",
        files={"file": ("document.pdf", io.BytesIO(pdf_data), "application/pdf")},
        data={"language": "hi"},
        headers=auth_headers,
    )
    assert pdf_resp.status_code == 400
