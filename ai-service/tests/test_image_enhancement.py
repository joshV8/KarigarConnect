"""
Gate 4 tests — Image Enhancement.

Per 04_GATE_IMAGE_ENHANCEMENT.md:
- Brightness (+5%), Contrast (+10%), Sharpness (+15%)
- Preserves product geometry and appearance
- Reuses Gate 2 image validation
- Supports both standard RGB photos and transparent RGBA photos (from Gate 3)
"""

import io
import pytest
from PIL import Image, ImageDraw

from app.services.enhancement_service import enhance_image

try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def make_test_photo(w=400, h=400, mode="RGB"):
    """Create a sample product image for testing."""
    if mode == "RGBA":
        img = Image.new("RGBA", (w, h), color=(220, 220, 220, 255))
        draw = ImageDraw.Draw(img)
        # Transparent corner
        draw.rectangle([0, 0, 100, 100], fill=(0, 0, 0, 0))
        # Product body
        draw.ellipse([100, 100, 300, 300], fill=(160, 82, 45, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    else:
        img = Image.new("RGB", (w, h), color=(220, 220, 220))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 300], fill=(160, 82, 45))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()


# --- Service-level tests -----------------------------------------------------


def test_enhance_image_valid_jpeg():
    """Enhancing a valid JPEG product image returns a valid RGBA PNG."""
    raw = make_test_photo(400, 400, mode="RGB")
    enhanced_bytes = enhance_image(raw)

    assert isinstance(enhanced_bytes, bytes)
    assert len(enhanced_bytes) > 0

    out = Image.open(io.BytesIO(enhanced_bytes))
    assert out.format == "PNG"
    assert out.mode == "RGBA"
    assert out.size == (400, 400)


def test_enhance_image_preserves_dimensions():
    """Enhancement must never distort dimensions or aspect ratio."""
    raw = make_test_photo(480, 360, mode="RGB")
    out = Image.open(io.BytesIO(enhance_image(raw)))
    assert out.size == (480, 360)


def test_enhance_image_preserves_transparency():
    """Gate 4 must preserve alpha channel transparency from Gate 3."""
    raw_rgba = make_test_photo(400, 400, mode="RGBA")
    out = Image.open(io.BytesIO(enhance_image(raw_rgba)))

    assert out.format == "PNG"
    assert out.mode == "RGBA"
    alpha = out.getchannel("A")
    alpha_vals = list(alpha.tobytes())
    # Should have both transparent pixels and opaque product pixels
    assert min(alpha_vals) == 0
    assert max(alpha_vals) == 255


def test_enhance_image_actually_modifies_pixels():
    """Verify that brightness/contrast enhancement changes pixel values as expected."""
    # Create image with known mid-tone grey
    img = Image.new("RGB", (320, 320), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    enhanced = Image.open(io.BytesIO(enhance_image(buf.getvalue())))
    # Pixel brightness should have increased (+5% brightness, plus contrast)
    orig_pixel = img.getpixel((160, 160))
    enh_pixel = enhanced.getpixel((160, 160))[:3]

    assert enh_pixel != orig_pixel, "Enhancement should visibly alter pixel values"
    # Midtones should be brighter
    assert sum(enh_pixel) > sum(orig_pixel)


def test_enhance_image_empty_data_raises():
    """Empty image bytes must raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        enhance_image(b"")


def test_enhance_image_corrupted_data_raises():
    """Corrupted / unreadable data must raise ValueError."""
    with pytest.raises(ValueError, match="Cannot decode"):
        enhance_image(b"not an image at all")


# --- API-level tests ---------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi/httpx not installed")
class TestEnhanceImageEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_accepts_valid_image(self):
        """POST /ai/enhance-image returns HTTP 200 and image/png."""
        data = make_test_photo(400, 400, mode="RGB")
        res = self.client.post(
            "/ai/enhance-image",
            files={"file": ("photo.jpg", data, "image/jpeg")},
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        out = Image.open(io.BytesIO(res.content))
        assert out.format == "PNG"
        assert out.size == (400, 400)

    def test_endpoint_rejects_tiny_image(self):
        """Rejects images smaller than 300x300 with HTTP 400 (per Gate 2 rules)."""
        tiny = Image.new("RGB", (100, 100), color=(100, 100, 100))
        buf = io.BytesIO()
        tiny.save(buf, format="JPEG")
        res = self.client.post(
            "/ai/enhance-image",
            files={"file": ("tiny.jpg", buf.getvalue(), "image/jpeg")},
        )
        assert res.status_code == 400
        assert "resolution too low" in res.json()["detail"]

    def test_endpoint_rejects_corrupted_file(self):
        """Rejects corrupted files with HTTP 400."""
        res = self.client.post(
            "/ai/enhance-image",
            files={"file": ("corrupt.jpg", b"corrupted garbage bytes", "image/jpeg")},
        )
        assert res.status_code == 400
        assert "Invalid image" in res.json()["detail"]

    def test_endpoint_rejects_unsupported_format(self):
        """Rejects unsupported format (e.g. BMP) with HTTP 400."""
        img = Image.new("RGB", (350, 350), color=(100, 100, 100))
        buf = io.BytesIO()
        img.save(buf, format="BMP")
        res = self.client.post(
            "/ai/enhance-image",
            files={"file": ("test.bmp", buf.getvalue(), "image/bmp")},
        )
        assert res.status_code == 400
        assert "Unsupported image format" in res.json()["detail"]
