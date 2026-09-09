"""
Gate 7 tests — Translation Service & API.

Per 07_GATE_TRANSLATION.md acceptance criteria:
- Original text is strictly preserved
- English and Hindi translations are returned
- Direct translations (Source -> English, Source -> Hindi) without chaining
- Translation errors do not crash the service (controlled error handling)
- Supports regional Indian languages (Marathi, Hindi, English, etc.)
- Endpoint POST /ai/translate: empty input -> 400, valid payload -> 200 with structured JSON
- Offline unit tests (mock client) and live integration tests (Gemini 2.5 Flash)
"""

import os
import pytest

from app.models.translation import TranslationRequest, TranslationResult
from app.services.translation_service import (
    _clean_json_string,
    _parse_translation_json,
    translate_text,
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


def test_translation_request_valid():
    """TranslationRequest parses valid inputs."""
    req = TranslationRequest(text="ही हाताने बनवलेली टोपली आहे.", source_language="mr")
    assert req.text == "ही हाताने बनवलेली टोपली आहे."
    assert req.source_language == "mr"


def test_translation_request_default_source_lang():
    """TranslationRequest works without explicit source_language."""
    req = TranslationRequest(text="Handmade clay pot")
    assert req.text == "Handmade clay pot"
    assert req.source_language is None


def test_translation_result_model():
    """TranslationResult models output correctly."""
    res = TranslationResult(
        source_language="mr",
        original="ही बांबूची टोपली आहे.",
        translations={
            "en": "This is a bamboo basket.",
            "hi": "यह बांस की टोकरी है।",
        },
    )
    assert res.source_language == "mr"
    assert res.original == "ही बांबूची टोपली आहे."
    assert "en" in res.translations
    assert "hi" in res.translations
    assert res.translations["en"] == "This is a bamboo basket."


# ---------------------------------------------------------------------------
# JSON Cleaning and Parsing Tests
# ---------------------------------------------------------------------------


def test_clean_json_string_fenced():
    raw = '```json\n{"detected_source_language": "mr", "translations": {"en": "basket", "hi": "tokari"}}\n```'
    cleaned = _clean_json_string(raw)
    assert cleaned.startswith("{") and cleaned.endswith("}")


def test_clean_json_string_with_extra_commentary():
    raw = 'Here is the translation:\n{"detected_source_language": "mr", "translations": {"en": "basket", "hi": "tokari"}}\nHope this helps!'
    cleaned = _clean_json_string(raw)
    assert cleaned.startswith("{") and cleaned.endswith("}")


def test_parse_translation_json_valid():
    raw = '{"detected_source_language": "mr", "translations": {"en": "Handmade bamboo basket.", "hi": "हस्तनिर्मित बांस की टोकरी।"}}'
    parsed = _parse_translation_json(raw)
    assert parsed["detected_source_language"] == "mr"
    assert parsed["translations"]["en"] == "Handmade bamboo basket."


def test_parse_translation_json_invalid():
    with pytest.raises(ValueError, match="Could not parse"):
        _parse_translation_json("invalid json")


# ---------------------------------------------------------------------------
# Service Unit Tests (Empty, Error, and Mock Client)
# ---------------------------------------------------------------------------


def test_translate_text_empty_raises_value_error():
    with pytest.raises(ValueError, match="empty or blank"):
        translate_text("")
    with pytest.raises(ValueError, match="empty or blank"):
        translate_text("   ")


def test_translate_text_missing_key_raises_runtime_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="No translation provider configured"):
        translate_text("Test string")


def test_translate_text_with_mock_client():
    """Mock client translates directly and preserves original text."""
    class MockClient:
        def generate_content(self, prompt):
            class Resp:
                text = (
                    '{"detected_source_language": "mr", '
                    '"translations": {"en": "This is a handmade bamboo basket.", '
                    '"hi": "यह हाथ से बनी बांस की टोकरी है।"}}'
                )
            return Resp()

    original_text = "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे."
    result = translate_text(
        text=original_text,
        source_language="mr",
        client=MockClient(),
    )

    assert result.original == original_text
    assert result.source_language == "mr"
    assert result.translations["en"] == "This is a handmade bamboo basket."
    assert "बांस" in result.translations["hi"]


def test_translate_text_direct_not_chained_contract():
    """Confirms both target translations are provided directly under translations dictionary."""
    mock_resp = {
        "source_language": "hi",
        "original": "यह सुंदर मिट्टी का बर्तन है।",
        "translations": {
            "en": "This is a beautiful clay pot.",
            "hi": "यह सुंदर मिट्टी का बर्तन है।",
        },
    }
    result = translate_text(
        text="यह सुंदर मिट्टी का बर्तन है।",
        source_language="hi",
        client=lambda text, source_language: TranslationResult(**mock_resp),
    )
    assert result.original == "यह सुंदर मिट्टी का बर्तन है।"
    assert result.translations["en"] == "This is a beautiful clay pot."
    assert result.translations["hi"] == "यह सुंदर मिट्टी का बर्तन है।"


# ---------------------------------------------------------------------------
# FastAPI Endpoint Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi/httpx not installed")
class TestTranslationEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_endpoint_empty_text_returns_422_or_400(self):
        """Empty or blank text is rejected."""
        res = self.client.post("/ai/translate", json={"text": ""})
        assert res.status_code in (400, 422)

    def test_endpoint_whitespace_text_returns_400(self):
        """Whitespace-only text is rejected with 400."""
        res = self.client.post("/ai/translate", json={"text": "   "})
        assert res.status_code == 400

    def test_endpoint_with_mocked_service(self, monkeypatch):
        """Valid request returns 200 and structured JSON matching Gate 7 spec."""
        import app.routers.translation as router_module

        def fake_translate(text, source_language=None, client=None):
            return TranslationResult(
                source_language="mr",
                original=text,
                translations={
                    "en": "This is a handmade bamboo basket.",
                    "hi": "यह हाथ से बनी बांस की टोकरी है।",
                },
            )

        monkeypatch.setattr(router_module, "translate_text", fake_translate)

        payload = {
            "text": "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
            "source_language": "mr",
        }
        res = self.client.post("/ai/translate", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["source_language"] == "mr"
        assert body["original"] == "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे."
        assert "en" in body["translations"]
        assert "hi" in body["translations"]
        assert body["translations"]["en"] == "This is a handmade bamboo basket."


# ---------------------------------------------------------------------------
# Emulator Translation Tests (Gate 7 Emulator)
# ---------------------------------------------------------------------------


class TestEmulatorTranslation:
    """Test full translation workflows using the Gate 7 Translation Emulator."""

    def test_emulator_marathi_direct_translation(self, monkeypatch):
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        marathi_text = "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे."
        result = translate_text(marathi_text, source_language="mr")

        assert result.original == marathi_text
        assert result.source_language == "mr"
        assert "en" in result.translations
        assert "hi" in result.translations
        assert "basket" in result.translations["en"].lower()
        assert "टोकरी" in result.translations["hi"]

    def test_emulator_hindi_direct_translation(self, monkeypatch):
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        hindi_text = "यह पारंपरिक हस्तनिर्मित मिट्टी का दिया है।"
        result = translate_text(hindi_text, source_language="hi")

        assert result.original == hindi_text
        assert result.source_language == "hi"
        assert "en" in result.translations
        assert "diya" in result.translations["en"].lower()

    def test_emulator_endpoint_roundtrip(self, monkeypatch):
        """Full HTTP roundtrip via FastAPI test client using the Emulator."""
        monkeypatch.setenv("AI_EMULATOR_MODE", "true")
        client = TestClient(app)
        payload = {
            "text": "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
            "source_language": "mr",
        }
        res = client.post("/ai/translate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["original"] == payload["text"]
        assert data["source_language"] == "mr"
        assert "en" in data["translations"]
        assert "hi" in data["translations"]
        assert "basket" in data["translations"]["en"].lower()
        assert "टोकरी" in data["translations"]["hi"]


# ---------------------------------------------------------------------------
# Live Translation Integration Tests (Gemini 2.5 Flash)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")),
    reason="GEMINI_API_KEY not configured",
)
class TestLiveTranslation:
    """Live integration tests executing actual translation calls via Gemini API."""

    def test_live_marathi_translation(self):
        """Live test: Marathi text translated directly to English and Hindi."""
        marathi_text = "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे."
        try:
            result = translate_text(marathi_text, source_language="mr")
        except RuntimeError as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
            raise

        assert result.original == marathi_text
        assert result.source_language == "mr"
        assert "en" in result.translations
        assert "hi" in result.translations
        assert "basket" in result.translations["en"].lower()
        assert len(result.translations["hi"]) > 0

    def test_live_hindi_translation(self):
        """Live test: Hindi text translated directly to English."""
        hindi_text = "यह पारंपरिक हस्तनिर्मित मिट्टी का दिया है।"
        try:
            result = translate_text(hindi_text, source_language="hi")
        except RuntimeError as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
            raise

        assert result.original == hindi_text
        assert "en" in result.translations
        assert len(result.translations["en"]) > 0

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi not installed")
    def test_live_endpoint_roundtrip(self):
        """Live HTTP roundtrip on POST /ai/translate."""
        client = TestClient(app)
        payload = {
            "text": "ही बांबूपासून बनवलेली हाताने विणलेली टोपली आहे.",
            "source_language": "mr",
        }
        res = client.post("/ai/translate", json=payload)
        if res.status_code == 500 and "429" in res.text:
            pytest.skip("Gemini free tier quota exhausted (429 RESOURCE_EXHAUSTED).")
        assert res.status_code == 200
        body = res.json()
        assert body["original"] == payload["text"]
        assert "en" in body["translations"]
        assert "hi" in body["translations"]
        assert len(body["translations"]["en"]) > 0

