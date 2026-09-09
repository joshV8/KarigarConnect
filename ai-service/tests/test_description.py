"""
Gate 8 tests — AI Product Description Service & Endpoint.

Per 08_GATE_AI_DESCRIPTION.md acceptance criteria:
- Generated content is readable, marketplace-ready, and grounded ONLY in supplied information.
- Does not invent certifications, dimensions, materials, origin, health claims,
  sustainability certifications, or features not provided or visible.
- Schema validates: title, short_description, description, features (List[str]), materials (List[str]).
- POST /ai/generate-description: empty payload -> 400, valid payload -> 200 with structured JSON.
- Fully supports deterministic AI Emulator for testing and offline environments.
- Live LLM calls safely guard against external 429 quota exhaustion.
"""

import os
import pytest

from app.models.description import DescriptionRequest, ProductDescriptionResult
from app.services.description_service import (
    _clean_json_string,
    _format_supplied_info,
    _parse_description_json,
    generate_product_description,
)

try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Schema and Model Validation Tests
# ---------------------------------------------------------------------------


def test_description_request_models():
    """DescriptionRequest accepts valid structured inputs."""
    req = DescriptionRequest(
        attributes={"material": "Bamboo", "category": "Basket"},
        transcription="This is a handmade basket woven from bamboo.",
        artisan_notes="Made by tribal artisans in rural Maharashtra.",
        language="en",
    )
    assert req.attributes["material"] == "Bamboo"
    assert req.transcription == "This is a handmade basket woven from bamboo."
    assert req.artisan_notes == "Made by tribal artisans in rural Maharashtra."
    assert req.language == "en"


def test_product_description_result_model():
    """ProductDescriptionResult validates required fields."""
    res = ProductDescriptionResult(
        title="Handwoven Bamboo Storage Basket",
        short_description="A sturdy, natural handwoven basket made from bamboo.",
        description="Handcrafted by traditional artisans using sustainable natural bamboo.",
        features=["Handwoven lattice design", "Sturdy base"],
        materials=["Bamboo"],
    )
    assert res.title == "Handwoven Bamboo Storage Basket"
    assert len(res.features) == 2
    assert res.materials == ["Bamboo"]


def test_product_description_result_list_coercion():
    """Coerces string-separated features or materials into lists cleanly."""
    res = ProductDescriptionResult(
        title="Terracotta Diya",
        short_description="Traditional clay lamp.",
        description="Crafted on a potter's wheel.",
        features="Handmade, Kiln-fired, Festive decor",
        materials="Clay, Terracotta",
    )
    assert isinstance(res.features, list)
    assert len(res.features) == 3
    assert "Handmade" in res.features
    assert "Clay" in res.materials


# ---------------------------------------------------------------------------
# JSON Utilities and Prompt Formatting Tests
# ---------------------------------------------------------------------------


def test_clean_json_string_fenced():
    raw = '```json\n{"title": "Clay Pot", "short_description": "A pot", "description": "Handmade pot", "features": ["Durable"], "materials": ["Clay"]}\n```'
    cleaned = _clean_json_string(raw)
    assert cleaned.startswith("{") and cleaned.endswith("}")


def test_parse_description_json_valid():
    raw = '{"title": "Clay Pot", "short_description": "A pot", "description": "Handmade pot", "features": ["Durable"], "materials": ["Clay"]}'
    data = _parse_description_json(raw)
    assert data["title"] == "Clay Pot"
    assert data["materials"] == ["Clay"]


def test_parse_description_json_invalid():
    with pytest.raises(ValueError, match="Could not parse"):
        _parse_description_json("not a valid json")


def test_format_supplied_info():
    info = _format_supplied_info(
        attributes={"material": "Clay", "color": "Terracotta"},
        transcription="Traditional diya made on a wheel",
        artisan_notes="Festive collection",
    )
    assert "material: Clay" in info
    assert "color: Terracotta" in info
    assert "Traditional diya made on a wheel" in info
    assert "Festive collection" in info


# ---------------------------------------------------------------------------
# Unit and Mock Tests
# ---------------------------------------------------------------------------


def test_generate_product_description_empty_raises_value_error():
    """Fails with ValueError if all inputs are empty or blank."""
    with pytest.raises(ValueError, match="no attributes, transcription, or notes"):
        generate_product_description()
    with pytest.raises(ValueError, match="no attributes, transcription, or notes"):
        generate_product_description(attributes={}, transcription="", artisan_notes="  ")


def test_generate_product_description_with_mock_client():
    """Generates description with injected mock client."""
    class MockLLM:
        def generate_content(self, prompt):
            class Resp:
                text = (
                    '{"title": "Handwoven Bamboo Basket", '
                    '"short_description": "Eco-friendly bamboo basket.", '
                    '"description": "Carefully woven with natural bamboo canes.", '
                    '"features": ["Lightweight", "Sturdy"], '
                    '"materials": ["Bamboo"]}'
                )
            return Resp()

    res = generate_product_description(
        attributes={"material": "Bamboo"},
        client=MockLLM(),
    )
    assert res.title == "Handwoven Bamboo Basket"
    assert "Bamboo" in res.materials
    assert "Lightweight" in res.features


# ---------------------------------------------------------------------------
# Emulator Tests (Gate 8 Deterministic AI Emulator)
# ---------------------------------------------------------------------------


class TestEmulatorDescription:
    """Tests product description generation using the Gate 8 AI Emulator."""

    def test_emulator_bamboo_basket_grounding(self, monkeypatch):
        """Emulator grounds description in supplied bamboo attributes without hallucination."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        res = generate_product_description(
            attributes={
                "product_name": "Handwoven Bamboo Storage Basket",
                "material": "Bamboo",
                "craft_type": "Handwoven",
                "category": "Handicrafts",
                "color": "Natural Beige",
                "visible_features": ["lattice weave", "sturdy rim"],
            },
            transcription="ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
            language="en",
        )
        assert isinstance(res, ProductDescriptionResult)
        assert "Bamboo" in res.title
        assert "Bamboo" in res.materials
        assert any("lattice" in f.lower() or "handwoven" in f.lower() for f in res.features)
        assert res.short_description != ""
        assert res.description != ""

    def test_emulator_terracotta_diya_hindi_output(self, monkeypatch):
        """Emulator supports Hindi target language output."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        res = generate_product_description(
            attributes={
                "product_name": "मिट्टी का दिया",
                "material": "Clay",
                "category": "Festive Pottery",
            },
            transcription="यह पारंपरिक हस्तनिर्मित मिट्टी का दिया है।",
            language="hi",
        )
        assert isinstance(res, ProductDescriptionResult)
        assert "हस्तनिर्मित" in res.title
        assert len(res.features) > 0
        assert len(res.materials) > 0

    def test_emulator_endpoint_roundtrip(self, monkeypatch):
        """HTTP POST /ai/generate-description roundtrip via FastAPI test client using emulator."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        client = TestClient(app)
        payload = {
            "attributes": {
                "product_name": "Handmade Clay Jug",
                "material": "Terracotta",
                "category": "Pottery",
                "visible_features": ["spout", "handle"],
            },
            "transcription": "Handcrafted clay pot for water storage",
            "language": "en",
        }
        res = client.post("/ai/generate-description", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "title" in data
        assert "short_description" in data
        assert "description" in data
        assert "features" in data
        assert "materials" in data
        assert "Clay" in data["title"] or "Terracotta" in data["title"] or "Jug" in data["title"]


# ---------------------------------------------------------------------------
# FastAPI Endpoint Validation Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestDescriptionEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_rejects_empty_payload(self):
        """Rejects request when no information is supplied."""
        res = self.client.post("/ai/generate-description", json={})
        assert res.status_code == 400
        assert "At least one source of information" in res.json()["detail"]

    def test_endpoint_rejects_whitespace_payload(self):
        """Rejects request with only blank whitespace notes."""
        res = self.client.post(
            "/ai/generate-description",
            json={"transcription": "   ", "artisan_notes": "   "},
        )
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# Live Integration Tests (Gemini 2.5 Flash)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")),
    reason="GEMINI_API_KEY not configured",
)
class TestLiveDescriptionGeneration:
    """Live LLM generation tests against Gemini API."""

    def test_live_gemini_description(self):
        """Live test: generates grounded product description via Gemini 2.5 Flash."""
        try:
            res = generate_product_description(
                attributes={
                    "product_name": "Handcrafted Bamboo Basket",
                    "material": "Bamboo",
                    "craft_type": "Weaving",
                    "color": "Natural Beige",
                },
                transcription="Handmade basket woven from natural raw bamboo.",
            )
        except RuntimeError as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
            raise

        assert isinstance(res, ProductDescriptionResult)
        assert "Bamboo" in res.title
        assert len(res.short_description) > 0
        assert len(res.description) > 0
        assert len(res.features) > 0
        assert len(res.materials) > 0

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
    def test_live_endpoint_roundtrip(self):
        """Live HTTP roundtrip on POST /ai/generate-description."""
        client = TestClient(app)
        payload = {
            "attributes": {
                "product_name": "Terracotta Flower Pot",
                "material": "Clay",
            },
            "transcription": "Handmade clay flower pot crafted on traditional wheel.",
        }
        res = client.post("/ai/generate-description", json=payload)
        if res.status_code == 500 and ("429" in res.text or "RESOURCE_EXHAUSTED" in res.text):
            pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
        assert res.status_code == 200
        body = res.json()
        assert "title" in body
        assert "short_description" in body
        assert "features" in body
        assert "materials" in body
