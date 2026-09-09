"""
Gate 9 tests — SEO Catalog Content Service & API.

Per 09_GATE_SEO_CATALOG.md acceptance criteria:
- SEO output is relevant and contains no fabricated claims.
- Keywords must be directly relevant to the product.
- Do not add unrelated trending keywords.
- Returns structured JSON matching SEOResult (seo_title, meta_description, keywords).
- Endpoint POST /ai/generate-seo: empty payload -> 400, valid payload -> 200 with structured JSON.
- Deterministic AI Emulator verified for zero-cloud testing.
- Live LLM calls safely guard against external 429 quota exhaustion.
"""

import os
import pytest

from app.models.seo import SEORequest, SEOResult
from app.services.seo_service import (
    _clean_json_string,
    _format_supplied_info,
    _parse_seo_json,
    generate_seo_metadata,
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


def test_seo_request_model():
    """SEORequest parses valid inputs."""
    req = SEORequest(
        title="Handwoven Bamboo Storage Basket",
        description="Crafted with natural bamboo by tribal artisans.",
        attributes={"material": "Bamboo", "category": "Handicrafts"},
        category="Handicrafts",
    )
    assert req.title == "Handwoven Bamboo Storage Basket"
    assert req.attributes["material"] == "Bamboo"
    assert req.category == "Handicrafts"


def test_seo_result_model():
    """SEOResult validates required fields."""
    res = SEOResult(
        seo_title="Handwoven Bamboo Basket | Handmade Indian Handicraft",
        meta_description="Sturdy handwoven bamboo basket crafted by rural artisans.",
        keywords=["bamboo basket", "handmade basket", "Indian handicraft"],
    )
    assert "Handwoven Bamboo Basket" in res.seo_title
    assert len(res.keywords) == 3


def test_seo_result_keyword_coercion():
    """Coerces comma-separated strings to clean lists."""
    res = SEOResult(
        seo_title="Clay Pot",
        meta_description="Handmade clay pot.",
        keywords="pottery, clay pot, terracotta, Indian craft",
    )
    assert isinstance(res.keywords, list)
    assert len(res.keywords) == 4
    assert "terracotta" in res.keywords


# ---------------------------------------------------------------------------
# JSON Cleaning and Formatting Tests
# ---------------------------------------------------------------------------


def test_clean_json_string_fenced():
    raw = '```json\n{"seo_title": "Bamboo Basket", "meta_description": "Eco basket", "keywords": ["bamboo", "basket"]}\n```'
    cleaned = _clean_json_string(raw)
    assert cleaned.startswith("{") and cleaned.endswith("}")


def test_parse_seo_json_valid():
    raw = '{"seo_title": "Bamboo Basket", "meta_description": "Eco basket", "keywords": ["bamboo", "basket"]}'
    data = _parse_seo_json(raw)
    assert data["seo_title"] == "Bamboo Basket"
    assert data["keywords"] == ["bamboo", "basket"]


def test_parse_seo_json_invalid():
    with pytest.raises(ValueError, match="Could not parse"):
        _parse_seo_json("not valid json")


def test_format_supplied_info():
    info = _format_supplied_info(
        title="Terracotta Diya",
        description="Festive clay diya",
        attributes={"material": "Clay"},
        category="Pottery",
    )
    assert "Terracotta Diya" in info
    assert "Category: Pottery" in info
    assert "material: Clay" in info


# ---------------------------------------------------------------------------
# Unit and Mock Tests
# ---------------------------------------------------------------------------


def test_generate_seo_metadata_empty_raises_value_error():
    """Fails with ValueError if all inputs are empty or blank."""
    with pytest.raises(ValueError, match="no product information provided"):
        generate_seo_metadata()
    with pytest.raises(ValueError, match="no product information provided"):
        generate_seo_metadata(title="  ", description="", attributes={})


def test_generate_seo_metadata_with_mock_client():
    """Generates metadata with an injected mock LLM."""
    class MockLLM:
        def generate_content(self, prompt):
            class Resp:
                text = (
                    '{"seo_title": "Handcrafted Clay Diya | Festive Decor", '
                    '"meta_description": "Authentic terracotta diya made on a potter\'s wheel.", '
                    '"keywords": ["clay diya", "handmade lamp", "terracotta"]}'
                )
            return Resp()

    res = generate_seo_metadata(
        title="Clay Diya",
        attributes={"material": "Clay"},
        client=MockLLM(),
    )
    assert res.seo_title == "Handcrafted Clay Diya | Festive Decor"
    assert "clay diya" in res.keywords


# ---------------------------------------------------------------------------
# Emulator Tests (Gate 9 Deterministic AI Emulator)
# ---------------------------------------------------------------------------


class TestEmulatorSEO:
    """Tests SEO metadata generation using the Gate 9 AI Emulator."""

    def test_emulator_bamboo_basket_seo(self, monkeypatch):
        """Emulator produces relevant, un-spammed keywords for bamboo basket."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        res = generate_seo_metadata(
            title="Handwoven Bamboo Basket",
            description="Handmade basket made from natural bamboo canes.",
            attributes={"material": "Bamboo", "category": "Handicrafts"},
        )
        assert isinstance(res, SEOResult)
        assert "Bamboo" in res.seo_title
        assert "bamboo basket" in [k.lower() for k in res.keywords]
        assert "handmade basket" in [k.lower() for k in res.keywords]
        assert "indian handicraft" in [k.lower() for k in res.keywords]
        # Verify no random viral keywords
        assert "iphone" not in [k.lower() for k in res.keywords]

    def test_emulator_terracotta_diya_seo(self, monkeypatch):
        """Emulator produces accurate pottery SEO metadata."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        res = generate_seo_metadata(
            title="Handmade Terracotta Clay Diya",
            description="Traditional festive clay lamp for pooja.",
            category="Festive Pottery",
        )
        assert isinstance(res, SEOResult)
        assert "Diya" in res.seo_title or "Terracotta" in res.seo_title
        assert any("diya" in k.lower() for k in res.keywords)
        assert len(res.meta_description) > 30

    def test_emulator_endpoint_roundtrip(self, monkeypatch):
        """HTTP POST /ai/generate-seo roundtrip via FastAPI test client using emulator."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        client = TestClient(app)
        payload = {
            "title": "Handwoven Bamboo Basket",
            "attributes": {"material": "Bamboo", "category": "Handicrafts"},
            "category": "Handicrafts",
        }
        res = client.post("/ai/generate-seo", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "seo_title" in data
        assert "meta_description" in data
        assert "keywords" in data
        assert "bamboo basket" in [k.lower() for k in data["keywords"]]


# ---------------------------------------------------------------------------
# FastAPI Endpoint Validation Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestSEOEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_rejects_empty_payload(self):
        """Rejects request with empty payload."""
        res = self.client.post("/ai/generate-seo", json={})
        assert res.status_code == 400
        assert "At least one source of product information" in res.json()["detail"]

    def test_endpoint_rejects_whitespace_payload(self):
        """Rejects request with only whitespace strings."""
        res = self.client.post(
            "/ai/generate-seo",
            json={"title": "   ", "description": "  "},
        )
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# Live Integration Tests (Gemini 2.5 Flash)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")),
    reason="GEMINI_API_KEY not configured",
)
class TestLiveSEOGeneration:
    """Live LLM generation tests against Gemini API."""

    def test_live_gemini_seo(self):
        """Live test: generates grounded SEO metadata via Gemini 2.5 Flash."""
        try:
            res = generate_seo_metadata(
                title="Handwoven Bamboo Storage Basket",
                attributes={"material": "Bamboo", "category": "Handicrafts"},
                category="Handicrafts",
            )
        except RuntimeError as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
            raise

        assert isinstance(res, SEOResult)
        assert len(res.seo_title) > 0
        assert len(res.meta_description) > 0
        assert len(res.keywords) >= 2

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
    def test_live_endpoint_roundtrip(self):
        """Live HTTP roundtrip on POST /ai/generate-seo."""
        client = TestClient(app)
        payload = {
            "title": "Terracotta Flower Pot",
            "attributes": {"material": "Clay", "category": "Pottery"},
        }
        res = client.post("/ai/generate-seo", json=payload)
        if res.status_code == 500 and ("429" in res.text or "RESOURCE_EXHAUSTED" in res.text):
            pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
        assert res.status_code == 200
        body = res.json()
        assert "seo_title" in body
        assert "meta_description" in body
        assert "keywords" in body
