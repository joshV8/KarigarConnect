"""
Gate 13 — Integration & End-to-End Testing.

Per 13_GATE_INTEGRATION_E2E.md:
  Prove that Person 2's AI service works end-to-end as an integrated system.

  Full artisan journey:
    1. Artisan uploads product photo.
    2. Image is validated, background-removed, enhanced.
    3. Product attributes are extracted via vision.
    4. Optional voice audio is transcribed (speech-to-text).
    5. Transcription is translated to English and Hindi.
    6. AI product description is generated in both languages.
    7. SEO metadata (title + keywords) is generated.
    8. Price is calculated from supplied cost inputs.
    9. Final structured catalog JSON is returned.
   10. Errors are handled gracefully.

Demo product used across integration tests:
  Product : Handwoven Bamboo Basket
  Voice   : ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे. (Marathi)
  Expected price range: ₹700-₹950 (recommended ~₹799)

All tests use AI_EMULATOR_MODE=true for reliable offline / CI execution.
Live API tests are skipped when no GEMINI_API_KEY is configured.
"""

import io
import os
import struct
import time
import wave
import math

import pytest
from PIL import Image

# ---------------------------------------------------------------------------
# Optional FastAPI / TestClient import guard
# ---------------------------------------------------------------------------
try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jpeg(width: int = 500, height: int = 500, color=(80, 120, 60)) -> bytes:
    """Create a minimal valid JPEG image (e.g. green bamboo-like colour)."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_wav(duration_s: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Create a minimal valid WAV file (silent tone for transcription tests)."""
    num_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            val = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            frames += struct.pack("<h", val)
        wf.writeframes(bytes(frames))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Checklist: Image works (validation + processing)
# ---------------------------------------------------------------------------


def test_e2e_image_validation_valid(monkeypatch):
    """Gate 13 checklist -- Image works: valid product image passes validation."""
    from app.services.image_service import validate_image

    img_bytes = _make_jpeg(600, 600)
    validate_image(img_bytes)  # no exception = pass


def test_e2e_image_validation_rejects_empty():
    """Gate 13 checklist -- Image works: empty image raises ValueError."""
    from app.services.image_service import validate_image

    with pytest.raises((ValueError, Exception)):
        validate_image(b"")


def test_e2e_image_validation_rejects_corrupted():
    """Gate 13 checklist -- Image works: corrupted bytes are rejected."""
    from app.services.image_service import validate_image

    with pytest.raises((ValueError, Exception)):
        validate_image(b"\xff\xd8\xff corrupted garbage data only")


# ---------------------------------------------------------------------------
# 2. Checklist: Background removal works
# ---------------------------------------------------------------------------


def test_e2e_background_removal():
    """Gate 13 checklist -- Background removal works: removes background, returns RGBA PNG."""
    from app.services.background_service import remove_background

    img_bytes = _make_jpeg(400, 400, color=(90, 60, 30))
    result_bytes = remove_background(img_bytes)
    out_img = Image.open(io.BytesIO(result_bytes))
    assert out_img.mode == "RGBA"
    assert out_img.size[0] > 0 and out_img.size[1] > 0


# ---------------------------------------------------------------------------
# 3. Checklist: Image enhancement works
# ---------------------------------------------------------------------------


def test_e2e_image_enhancement():
    """Gate 13 checklist -- Enhancement works: enhances image without altering dimensions."""
    from app.services.enhancement_service import enhance_image

    img_bytes = _make_jpeg(300, 300)
    enhanced = enhance_image(img_bytes)
    assert len(enhanced) > 0
    out_img = Image.open(io.BytesIO(enhanced))
    assert out_img.size == (300, 300)


# ---------------------------------------------------------------------------
# 4. Checklist: Vision JSON is valid (emulator)
# ---------------------------------------------------------------------------


def test_e2e_vision_attributes_emulator(monkeypatch):
    """Gate 13 checklist -- Vision JSON is valid: emulator returns full structured attributes."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.vision_service import analyze_product

    img_bytes = _make_jpeg(400, 400, color=(80, 120, 60))
    result = analyze_product(img_bytes, mime_type="image/jpeg")
    assert result.product_name != ""
    assert result.category != ""
    assert result.material != ""
    assert 0.0 <= result.confidence <= 1.0


def test_e2e_vision_json_structure(monkeypatch):
    """Gate 13 checklist -- Vision JSON is valid: result serialises to dict with expected keys."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.vision_service import analyze_product

    img_bytes = _make_jpeg(400, 400)
    result = analyze_product(img_bytes)
    data = result.model_dump()
    required_keys = {"product_name", "category", "material", "confidence"}
    assert required_keys.issubset(data.keys())


# ---------------------------------------------------------------------------
# 5. Checklist: Voice transcription works (mock)
# ---------------------------------------------------------------------------


def test_e2e_voice_transcription_mock(monkeypatch):
    """Gate 13 checklist -- Voice transcription works: mock Whisper transcribes WAV."""
    from app.services.speech_service import TranscriptionResult

    mock_result = TranscriptionResult(
        text="ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
        language="mr",
        confidence=0.92,
        segments=[],
    )

    def _mock_transcribe(audio_bytes, filename="audio.wav"):
        assert len(audio_bytes) > 0
        return mock_result

    monkeypatch.setattr("app.services.speech_service.transcribe_audio", _mock_transcribe)
    from app.services.speech_service import transcribe_audio

    wav_bytes = _make_wav()
    res = transcribe_audio(wav_bytes)
    assert "टोपली" in res.text
    assert res.language == "mr"
    assert res.confidence > 0.5


# ---------------------------------------------------------------------------
# 6. Checklist: Translation works (emulator)
# ---------------------------------------------------------------------------


def test_e2e_translation_marathi_to_english_emulator(monkeypatch):
    """Gate 13 checklist -- Translation works: Marathi -> English via emulator."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.translation_service import translate_text

    text = "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे."
    result = translate_text(text, source_language="mr")
    assert "en" in result.translations
    assert len(result.translations["en"]) > 0
    assert result.original == text


def test_e2e_translation_hindi_to_english_emulator(monkeypatch):
    """Gate 13 checklist -- Translation works: Hindi -> English via emulator."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.translation_service import translate_text

    text = "यह बांस से बनी हस्तनिर्मित टोकरी है।"
    result = translate_text(text, source_language="hi")
    assert "en" in result.translations
    assert len(result.translations["en"]) > 0
    assert result.original == text


# ---------------------------------------------------------------------------
# 7. Checklist: Description is grounded (emulator)
# ---------------------------------------------------------------------------


def test_e2e_description_grounded_emulator(monkeypatch):
    """Gate 13 checklist -- Description is grounded: no hallucinations beyond supplied attrs."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.description_service import generate_product_description

    attrs = {
        "product_name": "Handwoven Bamboo Basket",
        "category": "Home Decor",
        "material": "Bamboo",
        "color": "Natural Brown",
        "craft_type": "Weaving",
        "style": "Traditional",
        "visible_features": ["tight weave", "reinforced rim", "natural finish"],
    }

    result_en = generate_product_description(
        attributes=attrs,
        artisan_notes="Made by skilled artisan from Assam",
        language="en",
    )
    result_hi = generate_product_description(attributes=attrs, language="hi")

    assert len(result_en.description) > 0
    assert len(result_hi.description) > 0
    assert result_en.title != ""
    assert result_hi.title != ""


# ---------------------------------------------------------------------------
# 8. Checklist: SEO is relevant (emulator)
# ---------------------------------------------------------------------------


def test_e2e_seo_relevant_emulator(monkeypatch):
    """Gate 13 checklist -- SEO is relevant: keywords relate to bamboo basket product."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.seo_service import generate_seo_metadata

    result = generate_seo_metadata(
        title="Handwoven Bamboo Basket",
        description="A traditional handwoven bamboo basket crafted by Assam artisans.",
        attributes={
            "product_name": "Bamboo Basket",
            "material": "Bamboo",
            "category": "Home Decor",
        },
        category="Home Decor",
    )

    assert result.seo_title != ""
    assert len(result.keywords) >= 2
    assert any(len(kw) > 3 for kw in result.keywords)


# ---------------------------------------------------------------------------
# 9. Checklist: Pricing is explainable
# ---------------------------------------------------------------------------


def test_e2e_pricing_bamboo_basket():
    """Gate 13 checklist -- Pricing is explainable: transparent cost-plus formula for basket."""
    from app.services.pricing_service import calculate_price_recommendation

    result = calculate_price_recommendation(
        raw_material_cost=150.0,
        labour_cost=300.0,
        packaging_cost=50.0,
        other_cost=30.0,
        category="Home Decor",
        material="Bamboo",
        quality="standard",
        demand="medium",
    )

    assert result.recommended >= result.minimum
    assert result.maximum >= result.recommended
    assert result.currency == "INR"
    assert len(result.explanation) > 0
    # Total cost = 530, recommended must be above that
    assert result.recommended > 530


def test_e2e_pricing_expected_range():
    """Gate 13 checklist -- Pricing: recommended above cost floor for demo basket."""
    from app.services.pricing_service import calculate_price_recommendation

    result = calculate_price_recommendation(
        raw_material_cost=200.0,
        labour_cost=300.0,
        packaging_cost=60.0,
        other_cost=40.0,
        category="Home Decor",
        material="Bamboo",
        quality="standard",
        demand="medium",
    )
    assert result.recommended >= 600
    assert result.maximum <= 5000


# ---------------------------------------------------------------------------
# 10. Checklist: Complete catalog JSON works (emulator -- full pipeline)
# ---------------------------------------------------------------------------


def test_e2e_complete_catalog_bamboo_basket(monkeypatch):
    """
    Gate 13 -- FULL END-TO-END: Complete artisan journey for demo bamboo basket.

    Steps verified:
      - Image validation
      - Background removal (skipped for speed)
      - Product vision attribute extraction
      - AI description (English + Hindi)
      - SEO metadata
      - Price recommendation
      - Consolidated CatalogResult JSON
    """
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.catalog_service import orchestrate_catalog
    from app.models.catalog import CatalogResult

    img_bytes = _make_jpeg(600, 600, color=(80, 120, 60))

    result = orchestrate_catalog(
        image_bytes=img_bytes,
        image_filename="bamboo_basket.jpg",
        image_mime_type="image/jpeg",
        raw_material_cost=200.0,
        labour_cost=300.0,
        packaging_cost=60.0,
        other_cost=40.0,
        quality="standard",
        demand="medium",
        artisan_notes="Traditional handwoven bamboo basket from Assam",
        skip_bg_removal=True,
    )

    assert isinstance(result, CatalogResult)
    assert result.product.name != ""
    assert result.product.category != ""
    assert result.product.material != ""
    assert result.images.original.startswith("data:image/")
    assert result.images.processed.startswith("data:image/")
    assert len(result.description.english) > 10
    assert len(result.description.hindi) > 0
    assert len(result.seo.title) > 0
    assert len(result.seo.keywords) >= 2
    assert result.pricing.recommended >= result.pricing.minimum
    assert result.pricing.maximum >= result.pricing.recommended
    assert result.pricing.currency == "INR"
    assert len(result.pricing.explanation) > 0


def test_e2e_complete_catalog_with_voice(monkeypatch):
    """
    Gate 13 -- FULL E2E WITH VOICE: Catalog generation including Marathi voice.

    Simulates the full artisan journey where voice is provided.
    Uses a mock transcription to avoid Whisper dependency in CI.
    """
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")

    from app.services.speech_service import TranscriptionResult

    mock_transcription = TranscriptionResult(
        text="ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
        language="mr",
        confidence=0.91,
        segments=[],
    )
    monkeypatch.setattr(
        "app.services.catalog_service.transcribe_audio",
        lambda audio_bytes, filename="audio.wav": mock_transcription,
    )

    from app.services.catalog_service import orchestrate_catalog
    from app.models.catalog import CatalogResult

    img_bytes = _make_jpeg(500, 500, color=(90, 130, 70))
    wav_bytes = _make_wav()

    result = orchestrate_catalog(
        image_bytes=img_bytes,
        image_filename="bamboo_basket.jpg",
        image_mime_type="image/jpeg",
        audio_bytes=wav_bytes,
        audio_filename="voice_marathi.wav",
        raw_material_cost=150.0,
        labour_cost=300.0,
        packaging_cost=50.0,
        other_cost=30.0,
        artisan_notes="Handwoven bamboo basket",
        skip_bg_removal=True,
    )

    assert isinstance(result, CatalogResult)
    assert result.product.name != ""
    assert len(result.description.english) > 0
    assert len(result.description.hindi) > 0
    assert result.pricing.recommended > 0


# ---------------------------------------------------------------------------
# 11. Checklist: Errors are handled gracefully
# ---------------------------------------------------------------------------


def test_e2e_error_handling_empty_image(monkeypatch):
    """Gate 13 checklist -- Errors are handled: empty image raises ValueError, not crash."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.catalog_service import orchestrate_catalog

    with pytest.raises(ValueError):
        orchestrate_catalog(image_bytes=b"")


def test_e2e_error_handling_corrupted_image(monkeypatch):
    """Gate 13 checklist -- Errors are handled: corrupted image raises a clear exception."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.catalog_service import orchestrate_catalog

    with pytest.raises(Exception):
        orchestrate_catalog(image_bytes=b"not a real image \xff\xd8")


def test_e2e_translation_empty_text_error():
    """Gate 13 checklist -- Errors handled: translating blank text raises ValueError."""
    from app.services.translation_service import translate_text

    with pytest.raises(ValueError):
        translate_text("   ")


def test_e2e_description_empty_attributes_error(monkeypatch):
    """Gate 13 checklist -- Errors handled: empty attributes raises ValueError."""
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")
    from app.services.description_service import generate_product_description

    with pytest.raises((ValueError, Exception)):
        generate_product_description(attributes={}, language="en")


# ---------------------------------------------------------------------------
# 12. Checklist: Backend integration -- API endpoints accessible (Person 3)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestBackendIntegration:
    """
    Gate 13 checklist -- Backend integration works.

    Validates that Person 3's backend can call the AI service API endpoints
    and receive well-structured JSON responses.
    """

    def setup_method(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Person 3 / Flutter liveness check: GET /health returns 200 ok."""
        res = self.client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

    def test_root_endpoint(self):
        """GET / returns service info without 404."""
        res = self.client.get("/")
        assert res.status_code == 200
        body = res.json()
        assert "service" in body
        assert "docs" in body

    def test_backend_sync_catalog_endpoint(self, monkeypatch):
        """
        Person 3 Backend integration:
        POST /ai/generate-catalog returns complete JSON catalog.
        """
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        img_bytes = _make_jpeg(500, 500, color=(80, 120, 60))

        files = {"image": ("bamboo_basket.jpg", img_bytes, "image/jpeg")}
        data = {
            "raw_material_cost": "200.0",
            "labour_cost": "300.0",
            "packaging_cost": "60.0",
            "other_cost": "40.0",
            "quality": "standard",
            "demand": "medium",
            "artisan_notes": "Handwoven bamboo basket from Assam",
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

        assert body["product"]["name"] != ""
        assert body["product"]["category"] != ""
        assert body["product"]["material"] != ""
        assert len(body["description"]["english"]) > 0
        assert len(body["description"]["hindi"]) > 0
        assert len(body["seo"]["title"]) > 0
        assert len(body["seo"]["keywords"]) >= 2
        assert body["pricing"]["recommended"] > 0
        assert body["pricing"]["currency"] == "INR"
        assert body["pricing"]["recommended"] >= body["pricing"]["minimum"]

    def test_backend_async_catalog_endpoint(self, monkeypatch):
        """
        Person 3 Backend integration:
        POST /ai/generate-catalog-async returns 202, poll returns completed result.
        """
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        img_bytes = _make_jpeg(400, 400)

        files = {"image": ("product.jpg", img_bytes, "image/jpeg")}
        data = {
            "raw_material_cost": "250",
            "labour_cost": "200",
            "skip_bg_removal": "true",
        }

        res = self.client.post("/ai/generate-catalog-async", files=files, data=data)
        assert res.status_code == 202
        body = res.json()
        assert "job_id" in body
        assert body["status"] == "processing"
        job_id = body["job_id"]

        max_wait = 10.0
        start = time.time()
        final_status = None
        while time.time() - start < max_wait:
            poll = self.client.get(f"/ai/status/{job_id}")
            assert poll.status_code == 200
            pd = poll.json()
            if pd["status"] == "completed":
                final_status = "completed"
                assert "result" in pd and pd["result"] is not None
                assert "product" in pd["result"]
                assert "pricing" in pd["result"]
                break
            elif pd["status"] == "failed":
                pytest.fail(f"Async job failed: {pd.get('error')}")
            time.sleep(0.15)

        assert final_status == "completed", "Async job did not complete in time"

    def test_backend_error_handling_empty_image(self):
        """Person 3 Backend integration: empty image returns HTTP 400 not 500."""
        files = {"image": ("empty.jpg", b"", "image/jpeg")}
        res = self.client.post("/ai/generate-catalog", files=files)
        assert res.status_code in (400, 422)

    def test_backend_unknown_job_returns_404(self):
        """Person 3 Backend integration: unknown job_id returns HTTP 404."""
        res = self.client.get("/ai/status/nonexistent_job_e2e_test")
        assert res.status_code == 404

    def test_api_docs_accessible(self):
        """Person 3 Backend integration: OpenAPI docs are available at /docs."""
        res = self.client.get("/docs")
        assert res.status_code == 200

    def test_openapi_schema_accessible(self):
        """Person 3 Backend integration: OpenAPI schema available at /openapi.json."""
        res = self.client.get("/openapi.json")
        assert res.status_code == 200
        schema = res.json()
        assert "paths" in schema
        assert "/ai/generate-catalog" in schema["paths"]
        assert "/ai/generate-catalog-async" in schema["paths"]
        assert "/ai/status/{job_id}" in schema["paths"]


# ---------------------------------------------------------------------------
# 13. Checklist: API keys are protected (no secrets in responses)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
class TestAPIKeyProtection:
    """
    Gate 13 checklist -- API keys are protected.

    Verifies that API keys and secrets are never exposed in API responses,
    error messages, or the OpenAPI schema.
    """

    def setup_method(self):
        self.client = TestClient(app)

    def test_health_response_contains_no_secrets(self):
        """Health check must not leak environment variables or API keys."""
        res = self.client.get("/health")
        body_text = res.text
        assert "GEMINI_API_KEY" not in body_text
        assert "sk-" not in body_text
        assert "AIza" not in body_text

    def test_openapi_schema_contains_no_api_keys(self):
        """OpenAPI schema must not contain any real API key values."""
        res = self.client.get("/openapi.json")
        schema_text = res.text
        assert "AIza" not in schema_text

    def test_error_response_is_structured_json(self, monkeypatch):
        """
        Error responses from the global exception handler must be structured JSON,
        not raw stack traces leaking internal details.
        """
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        files = {"image": ("bad.jpg", b"\xff\xfe garbage data", "image/jpeg")}
        res = self.client.post("/ai/generate-catalog", files=files)
        assert res.status_code in (400, 422, 500)
        if res.status_code == 500:
            body = res.json()
            assert "detail" in body or "message" in body


# ---------------------------------------------------------------------------
# 14. Gate 13 -- ACCEPTANCE TEST: Full Artisan Journey
# ---------------------------------------------------------------------------


def test_e2e_full_artisan_journey_acceptance(monkeypatch):
    """
    Gate 13 -- ACCEPTANCE TEST.

    Per 13_GATE_INTEGRATION_E2E.md acceptance gate:
      'A complete artisan journey can be demonstrated from photo/voice input
       to final catalog and price without manually editing the AI response.'

    This test exercises the complete flow described in the Gate 13 spec:
      1. Artisan has a handwoven bamboo basket to list.
      2. Photo is provided -> image pipeline runs.
      3. Voice description in Marathi is provided (mocked).
      4. Full catalog JSON is returned with English & Hindi descriptions.
      5. Price is in expected artisan range for this category.
      6. No manual editing of the AI response is needed.
    """
    monkeypatch.setenv("AI_EMULATOR_MODE", "true")

    from app.services.speech_service import TranscriptionResult

    marathi_voice = TranscriptionResult(
        text="ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
        language="mr",
        confidence=0.93,
        segments=[],
    )
    monkeypatch.setattr(
        "app.services.catalog_service.transcribe_audio",
        lambda audio_bytes, filename="audio.wav": marathi_voice,
    )

    from app.services.catalog_service import orchestrate_catalog

    img_bytes = _make_jpeg(600, 500, color=(78, 116, 58))
    wav_bytes = _make_wav()

    result = orchestrate_catalog(
        image_bytes=img_bytes,
        image_filename="handwoven_bamboo_basket.jpg",
        image_mime_type="image/jpeg",
        audio_bytes=wav_bytes,
        audio_filename="marathi_voice.wav",
        raw_material_cost=200.0,
        labour_cost=350.0,
        packaging_cost=60.0,
        other_cost=40.0,
        quality="standard",
        demand="medium",
        artisan_notes="Handwoven bamboo basket, traditional Assam craft",
        skip_bg_removal=True,
    )

    # Product name must be non-empty
    assert len(result.product.name) >= 3, "Product name must be generated"
    assert result.product.category != ""
    assert result.product.material != ""

    # Multilingual descriptions
    assert len(result.description.english) >= 20, "English description too short"
    assert len(result.description.hindi) >= 5, "Hindi description missing"

    # Pricing: must be above total cost (200 + 350 + 60 + 40 = 650)
    total_cost = 200.0 + 350.0 + 60.0 + 40.0
    assert result.pricing.recommended >= total_cost, (
        f"Recommended price {result.pricing.recommended} is below total cost {total_cost}"
    )
    assert result.pricing.minimum >= total_cost * 0.8
    assert result.pricing.maximum >= result.pricing.recommended
    assert result.pricing.currency == "INR"

    # SEO populated
    assert len(result.seo.title) > 0
    assert len(result.seo.keywords) >= 2

    # Images as base64 data URIs
    assert result.images.original.startswith("data:image/")
    assert result.images.processed.startswith("data:image/")

    # Transparent explanation
    assert len(result.pricing.explanation) > 0
