"""
Gate 3 tests — Background Removal.

Per the gate spec, exercised against at least:
- plain background
- cluttered background
- dark product
- light product

Also covers: the endpoint rejects invalid input the same way Gate 2
already does (no duplicated/loosened validation logic), and the
service layer raises clearly if rembg is unavailable.

NOTE: rembg loads a real segmentation model on first use, which
requires network access to download model weights. These tests are
written to run wherever rembg + model weights are available (e.g. in
Antigravity or CI with network access). Where rembg is not
installed, the service-layer "not installed" behavior is still
verified directly, and the rest are skipped rather than failed, since
that reflects an environment limitation rather than a code defect.
"""

import io

import pytest
from PIL import Image, ImageDraw

from app.services.image_service import validate_image

try:
    import rembg  # noqa: F401

    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

try:
    from fastapi.testclient import TestClient

    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def make_plain_background(w=400, h=400):
    """Solid-color background with a solid-color 'product' square in the middle."""
    img = Image.new("RGB", (w, h), color=(230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(180, 90, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_cluttered_background(w=400, h=400):
    """Noisy multi-shape background with a central 'product' circle."""
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for i in range(0, w, 20):
        draw.line([(i, 0), (0, i)], fill=(i % 255, (i * 2) % 255, (i * 3) % 255), width=3)
    draw.ellipse([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(40, 90, 180))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_dark_product(w=400, h=400):
    img = Image.new("RGB", (w, h), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(10, 10, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_light_product(w=400, h=400):
    img = Image.new("RGB", (w, h), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)
    draw.rectangle([w // 4, h // 4, 3 * w // 4, 3 * h // 4], fill=(245, 245, 245))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# --- service-level tests -----------------------------------------------


def test_remove_background_raises_clearly_when_rembg_missing():
    """
    If rembg isn't installed, the service must fail with a clear,
    actionable RuntimeError rather than an unhandled ImportError deep
    inside the call stack.
    """
    if REMBG_AVAILABLE:
        pytest.skip("rembg is installed in this environment; not exercising the missing-dependency path")

    from app.services.background_service import remove_background

    with pytest.raises(RuntimeError, match="rembg is not installed"):
        remove_background(make_plain_background())


@pytest.mark.skipif(not REMBG_AVAILABLE, reason="rembg not installed in this environment (no network to fetch it/model weights)")
@pytest.mark.parametrize(
    "make_fixture",
    [make_plain_background, make_cluttered_background, make_dark_product, make_light_product],
)
def test_remove_background_returns_transparent_png(make_fixture):
    from app.services.background_service import remove_background

    data = make_fixture()
    result = remove_background(data)

    out_img = Image.open(io.BytesIO(result))
    assert out_img.format == "PNG"
    assert out_img.mode == "RGBA"

    # Product geometry should be preserved: output dimensions match input.
    in_img = Image.open(io.BytesIO(data))
    assert out_img.size == in_img.size

    # At least some pixels should be transparent (background removed)
    # and at least some should be opaque (product preserved).
    alpha = out_img.split()[-1]
    alpha_values = list(alpha.tobytes())
    assert min(alpha_values) < 255, "expected at least some transparent background pixels"
    assert max(alpha_values) > 0, "expected the product itself to remain visible"


# --- API-level tests -----------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi/httpx not installed in this environment")
class TestRemoveBackgroundEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_rejects_invalid_image_same_as_gate2(self):
        response = self.client.post(
            "/ai/remove-background",
            files={"file": ("broken.jpg", b"garbage not an image", "image/jpeg")},
        )
        assert response.status_code == 400
        assert "Invalid image" in response.json()["detail"]

    def test_endpoint_rejects_tiny_image(self):
        data = io.BytesIO()
        Image.new("RGB", (50, 50), color=(1, 2, 3)).save(data, format="JPEG")
        response = self.client.post(
            "/ai/remove-background",
            files={"file": ("tiny.jpg", data.getvalue(), "image/jpeg")},
        )
        assert response.status_code == 400
        assert "resolution too low" in response.json()["detail"]

    @pytest.mark.skipif(not REMBG_AVAILABLE, reason="rembg not installed in this environment")
    def test_endpoint_accepts_valid_image_and_returns_png(self):
        response = self.client.post(
            "/ai/remove-background",
            files={"file": ("product.jpg", make_plain_background(), "image/jpeg")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        out_img = Image.open(io.BytesIO(response.content))
        assert out_img.format == "PNG"
