"""
Gate 5 tests — Product Vision / Attribute Extraction.

Per 05_GATE_PRODUCT_VISION.md:
- Multimodal LLM identification of artisan products
- Structured attribute extraction (product_name, category, material, color,
  craft_type, style, visible_features, confidence)
- Reuses Gate 2 image validation (rejection of corrupted, tiny, oversized, unsupported files)
- Pydantic response validation
- Offline mock tests and live multimodal verification using GEMINI_API_KEY
"""

import io
import os
import pytest
from PIL import Image, ImageDraw

from app.models.product import ProductVisionResult
from app.services.vision_service import (
    _clean_json_string,
    _parse_llm_json,
    analyze_product,
)

try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def make_artisan_test_photo(w=400, h=400):
    """Create a sample artisan clay pot test image."""
    img = Image.new("RGB", (w, h), color=(240, 235, 230))
    draw = ImageDraw.Draw(img)
    # Clay pot body
    draw.ellipse([100, 100, 300, 320], fill=(180, 80, 40))
    # Pot neck
    draw.rectangle([160, 60, 240, 110], fill=(150, 65, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# --- Model Validation Tests --------------------------------------------------


def test_product_vision_model_full():
    """Verify complete product vision result parses correctly."""
    data = {
        "product_name": "Handwoven Bamboo Basket",
        "category": "Handicrafts",
        "material": "Bamboo",
        "color": "Natural",
        "craft_type": "Handwoven",
        "style": "Traditional",
        "visible_features": ["woven structure", "handle"],
        "confidence": 0.91,
    }
    model = ProductVisionResult.model_validate(data)
    assert model.product_name == "Handwoven Bamboo Basket"
    assert model.category == "Handicrafts"
    assert model.material == "Bamboo"
    assert model.craft_type == "Handwoven"
    assert model.confidence == 0.91
    assert "woven structure" in model.visible_features


def test_product_vision_model_partial_and_nulls():
    """Per spec, attributes that cannot be determined must support null."""
    data = {
        "product_name": "Earthen Vase",
        "category": "Pottery",
        "material": None,
        "color": "Terracotta",
        "craft_type": None,
        "style": None,
        "visible_features": ["curved base"],
        "confidence": None,
    }
    model = ProductVisionResult.model_validate(data)
    assert model.product_name == "Earthen Vase"
    assert model.material is None
    assert model.craft_type is None
    assert model.confidence is None


def test_product_vision_model_confidence_string_coercion():
    """Verify string confidence like 'High' or '0.85' safely coerces to float."""
    m_high = ProductVisionResult.model_validate({"confidence": "High"})
    assert m_high.confidence == 0.9

    m_med = ProductVisionResult.model_validate({"confidence": "Medium"})
    assert m_med.confidence == 0.7

    m_str_num = ProductVisionResult.model_validate({"confidence": "0.85"})
    assert m_str_num.confidence == 0.85


# --- JSON Parsing Tests ------------------------------------------------------


def test_clean_json_string_fenced():
    """Verify extraction of JSON inside markdown fences."""
    raw = '```json\n{"product_name": "Silk Saree", "category": "Textiles"}\n```'
    cleaned = _clean_json_string(raw)
    assert '{"product_name": "Silk Saree", "category": "Textiles"}' in cleaned


def test_clean_json_string_with_commentary():
    """Verify extraction of JSON surrounded by conversational text."""
    raw = 'Here is the analyzed product in JSON:\n{"product_name": "Clay Lamp"}\nHope this helps!'
    cleaned = _clean_json_string(raw)
    assert cleaned == '{"product_name": "Clay Lamp"}'


def test_parse_llm_json_valid():
    """Verify _parse_llm_json returns a valid model."""
    raw = '```json\n{"product_name": "Brass Bell", "category": "Metalcraft", "confidence": 0.88}\n```'
    model = _parse_llm_json(raw)
    assert model.product_name == "Brass Bell"
    assert model.category == "Metalcraft"
    assert model.confidence == 0.88


def test_parse_llm_json_invalid():
    """Verify invalid JSON raises ValueError."""
    with pytest.raises(ValueError, match="invalid JSON"):
        _parse_llm_json("not valid json at all")


# --- Service Layer Tests -----------------------------------------------------


def test_analyze_product_empty_data_raises():
    """Empty image bytes raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        analyze_product(b"")


def test_analyze_product_with_mock_client():
    """Verify analyze_product works with an injected mock client."""
    class MockVisionClient:
        def analyze(self, image_bytes, mime_type):
            return {
                "product_name": "Handmade Clay Jug",
                "category": "Pottery",
                "material": "Terracotta",
                "color": "Earthy Brown",
                "craft_type": "Wheel Thrown",
                "style": "Rustic",
                "visible_features": ["spout", "handle"],
                "confidence": 0.95,
            }

    raw = make_artisan_test_photo()
    res = analyze_product(raw, client=MockVisionClient())
    assert isinstance(res, ProductVisionResult)
    assert res.product_name == "Handmade Clay Jug"
    assert res.material == "Terracotta"
    assert res.confidence == 0.95


# --- Live API Integration Test -----------------------------------------------


@pytest.mark.skipif(
    not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")),
    reason="GEMINI_API_KEY not configured",
)
def test_live_gemini_vision_analysis():
    """Execute live product vision analysis with Gemini API against a sample image."""
    raw = make_artisan_test_photo()
    try:
        result = analyze_product(raw, mime_type="image/jpeg")
    except RuntimeError as exc:
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
        raise

    assert isinstance(result, ProductVisionResult)
    assert result.product_name is not None
    assert len(result.product_name) > 0
    assert result.color is not None
    assert result.confidence is not None
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.visible_features, list)


# --- API Endpoint Tests ------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi/httpx not installed")
class TestVisionEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_rejects_tiny_image(self):
        """Rejects images smaller than 300x300 (reusing Gate 2 rules)."""
        tiny = Image.new("RGB", (150, 150), color=(100, 100, 100))
        buf = io.BytesIO()
        tiny.save(buf, format="JPEG")
        res = self.client.post(
            "/ai/analyze-product",
            files={"file": ("tiny.jpg", buf.getvalue(), "image/jpeg")},
        )
        assert res.status_code == 400
        assert "resolution too low" in res.json()["detail"]

    def test_endpoint_rejects_corrupted_image(self):
        """Rejects corrupt image bytes."""
        res = self.client.post(
            "/ai/analyze-product",
            files={"file": ("corrupt.jpg", b"corrupted bytes", "image/jpeg")},
        )
        assert res.status_code == 400
        assert "Invalid image" in res.json()["detail"]

    def test_endpoint_rejects_unsupported_format(self):
        """Rejects unsupported format (e.g. BMP)."""
        img = Image.new("RGB", (350, 350), color=(100, 100, 100))
        buf = io.BytesIO()
        img.save(buf, format="BMP")
        res = self.client.post(
            "/ai/analyze-product",
            files={"file": ("test.bmp", buf.getvalue(), "image/bmp")},
        )
        assert res.status_code == 400
        assert "Unsupported image format" in res.json()["detail"]

    @pytest.mark.skipif(
        not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")),
        reason="GEMINI_API_KEY not configured",
    )
    def test_endpoint_live_analyze_product(self):
        """Live POST /ai/analyze-product returns 200 with structured JSON."""
        raw = make_artisan_test_photo()
        res = self.client.post(
            "/ai/analyze-product",
            files={"file": ("pottery.jpg", raw, "image/jpeg")},
        )
        if res.status_code == 500 and ("429" in res.text or "RESOURCE_EXHAUSTED" in res.text):
            pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
        assert res.status_code == 200
        body = res.json()
        assert "product_name" in body
        assert "category" in body
        assert "confidence" in body
        assert isinstance(body["visible_features"], list)


