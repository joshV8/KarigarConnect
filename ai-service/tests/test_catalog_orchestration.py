"""
Gate 11 tests — Catalog Orchestration Service & Endpoint.

Per 11_GATE_CATALOG_ORCHESTRATION.md acceptance criteria:
- Connects all AI modules into one unified pipeline.
- POST /ai/generate-catalog returns full catalog: product, images, description, seo, pricing.
- Reuses existing modular service functions without duplicating logic.
- Acceptance: One photo + optional voice + pricing inputs must produce a complete catalog response.
"""

import io
import pytest
from PIL import Image

from app.models.catalog import (
    CatalogDescriptions,
    CatalogImages,
    CatalogPricing,
    CatalogProductInfo,
    CatalogResult,
    CatalogSEO,
)
from app.services.catalog_service import _bytes_to_data_uri, orchestrate_catalog

try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def _make_test_image(width: int = 400, height: int = 400, color=(160, 82, 45)) -> bytes:
    """Helper to generate a valid test JPEG image (e.g. terracotta pottery)."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Schema and Model Validation Tests
# ---------------------------------------------------------------------------


def test_catalog_result_model():
    """CatalogResult validates all composite sub-models."""
    res = CatalogResult(
        product=CatalogProductInfo(name="Clay Diya", category="Pottery", material="Clay"),
        images=CatalogImages(original="data:image/jpeg;base64,...", processed="data:image/png;base64,..."),
        description=CatalogDescriptions(english="Handcrafted clay diya.", hindi="हस्तनिर्मित दिया।", original="दिया"),
        seo=CatalogSEO(title="Clay Diya | Pottery", keywords=["clay diya", "handmade"]),
        pricing=CatalogPricing(recommended=450.0, minimum=350.0, maximum=600.0, currency="INR", explanation="Good price"),
    )
    assert res.product.name == "Clay Diya"
    assert res.images.original.startswith("data:")
    assert res.description.english == "Handcrafted clay diya."
    assert res.seo.title == "Clay Diya | Pottery"
    assert res.pricing.recommended == 450.0


def test_bytes_to_data_uri():
    """Data URI generation formats correctly."""
    raw = b"testbytes"
    uri = _bytes_to_data_uri(raw, "image/jpeg")
    assert uri.startswith("data:image/jpeg;base64,")


# ---------------------------------------------------------------------------
# Orchestration Pipeline Unit Tests
# ---------------------------------------------------------------------------


def test_orchestrate_catalog_with_emulator(monkeypatch):
    """End-to-end orchestration pipeline runs and produces full catalog with emulator."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    img_bytes = _make_test_image()

    res = orchestrate_catalog(
        image_bytes=img_bytes,
        raw_material_cost=300.0,
        labour_cost=250.0,
        packaging_cost=50.0,
        artisan_notes="Traditional terracotta pottery item",
        skip_bg_removal=True,  # test fast flow
    )

    assert isinstance(res, CatalogResult)
    assert res.product.name != ""
    assert res.product.category != ""
    assert res.product.material != ""
    assert res.images.original.startswith("data:image/")
    assert res.images.processed.startswith("data:image/")
    assert len(res.description.english) > 0
    assert len(res.description.hindi) > 0
    assert len(res.seo.title) > 0
    assert len(res.seo.keywords) >= 2
    assert res.pricing.recommended >= res.pricing.minimum


def test_orchestrate_catalog_rejects_empty_image():
    """Empty image raises ValueError during validation."""
    with pytest.raises(ValueError):
        orchestrate_catalog(image_bytes=b"")


# ---------------------------------------------------------------------------
# FastAPI Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestCatalogEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_generate_catalog_success(self, monkeypatch):
        """POST /ai/generate-catalog multipart form produces complete JSON."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        img_bytes = _make_test_image()

        files = {
            "image": ("pottery.jpg", img_bytes, "image/jpeg"),
        }
        data = {
            "raw_material_cost": "250.0",
            "labour_cost": "200.0",
            "packaging_cost": "30.0",
            "artisan_notes": "Wheel-thrown traditional diya",
            "skip_bg_removal": "true",
        }

        res = self.client.post("/ai/generate-catalog", files=files, data=data)
        assert res.status_code == 200
        body = res.json()
        assert "product" in body
        assert "images" in body
        assert "description" in body
        assert "seo" in body
        assert "pricing" in body
        assert body["pricing"]["recommended"] > 0

    def test_endpoint_generate_catalog_rejects_empty_image(self):
        """POST /ai/generate-catalog rejects zero-byte image upload."""
        files = {
            "image": ("empty.jpg", b"", "image/jpeg"),
        }
        res = self.client.post("/ai/generate-catalog", files=files)
        assert res.status_code in (400, 422)

    def test_products_contract_flow(self, monkeypatch):
        """Test API contract: process product, publish product, fetch catalog."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        img_bytes = _make_test_image()

        # 1. /products/process
        res = self.client.post(
            "/products/process",
            files={"photo": ("test.jpg", img_bytes, "image/jpeg")},
            data={"raw_material_cost": "300.0"},
        )
        assert res.status_code == 200
        proc_data = res.json()
        assert "image_url" in proc_data
        assert "description_hi" in proc_data
        assert "description_en" in proc_data
        assert "price" in proc_data
        assert "price_reason" in proc_data
        assert proc_data["price"] > 0

        # 2. /products (publish)
        pub_res = self.client.post(
            "/products",
            json={
                "image_url": proc_data["image_url"],
                "description_hi": proc_data["description_hi"],
                "description_en": proc_data["description_en"],
                "price": proc_data["price"],
                "price_reason": proc_data["price_reason"],
                "artisan_id": "artisan_test_42",
            },
        )
        assert pub_res.status_code == 200
        pub_data = pub_res.json()
        assert "id" in pub_data

        # 3. /products (get catalog)
        cat_res = self.client.get("/products?artisan_id=artisan_test_42")
        assert cat_res.status_code == 200
        cat_data = cat_res.json()
        assert isinstance(cat_data, list)
        assert any(item["id"] == pub_data["id"] for item in cat_data)

