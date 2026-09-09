"""
Gate 2 tests — Image Upload & Validation.

Covers every case called out in the gate spec:
- valid JPEG/PNG
- tiny image (below minimum resolution)
- >10 MB file
- corrupted file
- unsupported file format
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.image_service import MAX_SIZE, validate_image

client = TestClient(app)


def make_image_bytes(width=400, height=400, fmt="JPEG"):
    """Build an in-memory image of the given size/format for test fixtures."""
    img = Image.new("RGB", (width, height), color=(120, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# --- service-level tests -----------------------------------------------


def test_valid_jpeg_passes():
    data = make_image_bytes(400, 400, "JPEG")
    image = validate_image(data)
    assert image.format == "JPEG"
    assert image.width == 400 and image.height == 400


def test_valid_png_passes():
    data = make_image_bytes(400, 400, "PNG")
    image = validate_image(data)
    assert image.format == "PNG"


def test_tiny_image_rejected():
    data = make_image_bytes(50, 50, "JPEG")
    with pytest.raises(ValueError, match="resolution too low"):
        validate_image(data)


def test_oversized_file_rejected():
    # Doesn't need to be a real image — size check happens before decoding.
    data = b"0" * (MAX_SIZE + 1)
    with pytest.raises(ValueError, match="exceeds 10 MB"):
        validate_image(data)


def test_corrupted_file_rejected():
    data = b"this is not a real image file, just garbage bytes"
    with pytest.raises(ValueError, match="Invalid image"):
        validate_image(data)


def test_unsupported_format_rejected():
    img = Image.new("RGB", (400, 400), color=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    with pytest.raises(ValueError, match="Unsupported image format"):
        validate_image(buf.getvalue())


def test_empty_file_rejected():
    with pytest.raises(ValueError, match="Empty file"):
        validate_image(b"")


# --- API-level tests -----------------------------------------------------


def test_endpoint_accepts_valid_jpeg():
    data = make_image_bytes(400, 400, "JPEG")
    response = client.post(
        "/ai/validate-image",
        files={"file": ("product.jpg", data, "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["format"] == "JPEG"
    assert body["width"] == 400
    assert body["height"] == 400


def test_endpoint_rejects_tiny_image():
    data = make_image_bytes(50, 50, "JPEG")
    response = client.post(
        "/ai/validate-image",
        files={"file": ("tiny.jpg", data, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "resolution too low" in response.json()["detail"]


def test_endpoint_rejects_corrupted_file():
    data = b"garbage not an image"
    response = client.post(
        "/ai/validate-image",
        files={"file": ("broken.jpg", data, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "Invalid image" in response.json()["detail"]


def test_endpoint_rejects_oversized_file():
    data = b"0" * (MAX_SIZE + 1)
    response = client.post(
        "/ai/validate-image",
        files={"file": ("huge.jpg", data, "image/jpeg")},
    )
    assert response.status_code == 400
    assert "exceeds 10 MB" in response.json()["detail"]
