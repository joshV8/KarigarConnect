"""
Gate 6 tests -- Speech-to-Text.

Per 06_GATE_SPEECH_TO_TEXT.md acceptance criteria:
- Marathi audio -> correct transcription
- Hindi audio -> correct transcription
- English audio -> correct transcription
- Noisy audio -> still produces output (or controlled error)
- Empty audio -> controlled ValueError
- Missing whisper -> controlled RuntimeError
- POST /ai/transcribe endpoint: empty upload -> 400, valid WAV -> 200
- Live Whisper tests (skipped when ffmpeg is not on PATH)
"""

import importlib
import io
import os
import struct
import sys
import wave
import pytest

# ---------------------------------------------------------------------------
# Helpers -- synthetic audio builders (no external TTS needed)
# ---------------------------------------------------------------------------

def _make_wav_bytes(num_frames=16000, sample_rate=16000, amplitude=0):
    """
    Build a minimal valid WAV file in memory.

    amplitude=0 -> silence.
    amplitude>0 -> square wave (useful for testing the audio pipeline).
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit PCM
        wf.setframerate(sample_rate)
        samples = []
        for i in range(num_frames):
            if amplitude == 0:
                samples.append(0)
            else:
                samples.append(amplitude if (i // (sample_rate // 440)) % 2 == 0 else -amplitude)
        data = struct.pack(f"<{num_frames}h", *samples)
        wf.writeframes(data)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

WHISPER_AVAILABLE = importlib.util.find_spec("whisper") is not None

try:
    from fastapi.testclient import TestClient
    from app.main import app
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Model tests (no network/model needed)
# ---------------------------------------------------------------------------


def test_transcription_result_model_full():
    """TranscriptionResult accepts all fields."""
    from app.models.speech import TranscriptionResult
    m = TranscriptionResult(
        text="hi bambupasun banavaleli hatane vinaleli topali ahe.",
        language="mr",
        confidence=0.87,
    )
    assert m.text == "hi bambupasun banavaleli hatane vinaleli topali ahe."
    assert m.language == "mr"
    assert m.confidence == 0.87


def test_transcription_result_model_optional_fields():
    """TranscriptionResult works with only text."""
    from app.models.speech import TranscriptionResult
    m = TranscriptionResult(text="test")
    assert m.text == "test"
    assert m.language is None
    assert m.confidence is None


def test_transcription_result_model_confidence_bounds():
    """Pydantic enforces 0.0 <= confidence <= 1.0."""
    from app.models.speech import TranscriptionResult
    import pydantic
    with pytest.raises((pydantic.ValidationError, ValueError)):
        TranscriptionResult(text="x", confidence=1.5)
    with pytest.raises((pydantic.ValidationError, ValueError)):
        TranscriptionResult(text="x", confidence=-0.1)


# ---------------------------------------------------------------------------
# Service unit tests -- empty audio / missing-whisper paths
# ---------------------------------------------------------------------------


def test_transcribe_empty_bytes_raises_value_error():
    """Empty bytes raise ValueError before touching Whisper."""
    from app.services.speech_service import transcribe_audio
    with pytest.raises(ValueError, match="empty"):
        transcribe_audio(b"")


def test_transcribe_missing_whisper_raises_runtime_error(monkeypatch):
    """If whisper is not importable, RuntimeError is raised (not ImportError)."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "whisper":
            raise ImportError("No module named 'whisper'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    sys.modules.pop("whisper", None)

    from app.services import speech_service
    importlib.reload(speech_service)

    with pytest.raises(RuntimeError, match="openai-whisper"):
        speech_service.transcribe_audio(_make_wav_bytes(1000))


# ---------------------------------------------------------------------------
# Confidence helper tests (pure Python, no model needed)
# ---------------------------------------------------------------------------


def test_avg_confidence_no_segments():
    from app.services.speech_service import _avg_confidence
    assert _avg_confidence([]) is None


def test_avg_confidence_zero_logprob():
    """avg_logprob=0 should map to confidence 1.0."""
    from app.services.speech_service import _avg_confidence
    result = _avg_confidence([{"avg_logprob": 0.0}])
    assert result == 1.0


def test_avg_confidence_worst_logprob():
    """avg_logprob=-1.5 (worst) should map to confidence 0.0."""
    from app.services.speech_service import _avg_confidence
    result = _avg_confidence([{"avg_logprob": -1.5}])
    assert result == 0.0


def test_avg_confidence_typical_logprob():
    """avg_logprob=-0.3 (typical good result) maps to ~0.8."""
    from app.services.speech_service import _avg_confidence
    result = _avg_confidence([{"avg_logprob": -0.3}])
    assert 0.75 <= result <= 0.85


def test_avg_confidence_clamped():
    """Values outside [-1.5, 0] are clamped before scaling."""
    from app.services.speech_service import _avg_confidence
    r_low = _avg_confidence([{"avg_logprob": -5.0}])
    assert r_low == 0.0
    r_high = _avg_confidence([{"avg_logprob": 0.5}])
    assert r_high == 1.0


# ---------------------------------------------------------------------------
# Mock-model service tests (offline -- injects fake Whisper model)
# ---------------------------------------------------------------------------


class _MockWhisperModel:
    """Fake Whisper model that returns canned output without touching ffmpeg."""

    def __init__(self, text, language, avg_logprob=-0.2):
        self._text = text
        self._language = language
        self._avg_logprob = avg_logprob

    def transcribe(self, audio_path, *args, **kwargs):
        return {
            "text": self._text,
            "language": self._language,
            "segments": [{"avg_logprob": self._avg_logprob}],
        }


def test_transcribe_marathi_mock():
    """Marathi transcription mock returns correct text and language."""
    from app.services.speech_service import transcribe_audio
    mock = _MockWhisperModel(
        text="hi bambupasun banavaleli hatane vinaleli topali ahe.",
        language="mr",
    )
    wav = _make_wav_bytes(16000)
    result = transcribe_audio(wav, model=mock)
    assert result.text == "hi bambupasun banavaleli hatane vinaleli topali ahe."
    assert result.language == "mr"
    assert result.confidence is not None and 0.0 <= result.confidence <= 1.0


def test_transcribe_hindi_mock():
    """Hindi transcription mock."""
    from app.services.speech_service import transcribe_audio
    mock = _MockWhisperModel(
        text="yah hastanirmit bans ki tokari hai.",
        language="hi",
    )
    wav = _make_wav_bytes(16000)
    result = transcribe_audio(wav, model=mock)
    assert result.text == "yah hastanirmit bans ki tokari hai."
    assert result.language == "hi"


def test_transcribe_english_mock():
    """English transcription mock."""
    from app.services.speech_service import transcribe_audio
    mock = _MockWhisperModel(text="This is a handmade bamboo basket.", language="en")
    wav = _make_wav_bytes(16000)
    result = transcribe_audio(wav, model=mock)
    assert result.text == "This is a handmade bamboo basket."
    assert result.language == "en"


def test_transcribe_noisy_audio_mock():
    """Noisy audio: Whisper still returns a result (low confidence but non-empty)."""
    from app.services.speech_service import transcribe_audio
    mock = _MockWhisperModel(
        text="hastanirmit topali",
        language="mr",
        avg_logprob=-0.9,   # lower confidence for noisy audio
    )
    noisy_wav = _make_wav_bytes(num_frames=16000, amplitude=20000)
    result = transcribe_audio(noisy_wav, model=mock)
    assert result.text != ""
    assert result.confidence is not None
    assert result.confidence < 0.5   # noisy -> low confidence


def test_transcribe_empty_result_raises_value_error():
    """If model returns empty text, service raises ValueError (not silent failure)."""
    from app.services.speech_service import transcribe_audio

    class _EmptyModel:
        def transcribe(self, path, *args, **kwargs):
            return {"text": "", "language": "mr", "segments": []}

    wav = _make_wav_bytes(16000)
    with pytest.raises(ValueError, match="empty transcription"):
        transcribe_audio(wav, model=_EmptyModel())


def test_transcribe_silence_hallucination_raises_value_error():
    """Whisper hallucination tokens on silent audio are rejected as empty/silent."""
    from app.services.speech_service import transcribe_audio

    class _HallucinatingModel:
        def transcribe(self, path, *args, **kwargs):
            return {"text": "[BLANK_AUDIO]", "language": "en", "segments": []}

    wav = _make_wav_bytes(16000)
    with pytest.raises(ValueError, match="empty transcription"):
        transcribe_audio(wav, model=_HallucinatingModel())


def test_infer_audio_extension_magic_bytes():
    """Magic bytes take precedence over misleading filenames."""
    from app.services.speech_service import _infer_audio_extension

    # M4A bytes with a default .wav filename -> correctly detects .m4a
    m4a_dummy = b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00" + b"\x00" * 30
    assert _infer_audio_extension(m4a_dummy, "audio.wav") == ".m4a"

    # WebM bytes with .wav filename -> correctly detects .webm
    webm_dummy = b"\x1a\x45\xdf\xa3" + b"\x00" * 30
    assert _infer_audio_extension(webm_dummy, "recording.wav") == ".webm"

    # MP3 ID3 header
    mp3_dummy = b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 30
    assert _infer_audio_extension(mp3_dummy, "voice.wav") == ".mp3"

    # Fallback to filename extension when magic bytes are unknown
    assert _infer_audio_extension(b"unknown_header_bytes", "sample.mp3") == ".mp3"
    assert _infer_audio_extension(b"unknown_header_bytes", "sample.unknown") == ".wav"


def test_normalize_language():
    """Language tags and names normalize to ISO 639-1 code."""
    from app.services.speech_service import _normalize_language

    assert _normalize_language("mr-IN") == "mr"
    assert _normalize_language("hi-IN") == "hi"
    assert _normalize_language("en-US") == "en"
    assert _normalize_language("Marathi") == "mr"
    assert _normalize_language("Hindi") == "hi"
    assert _normalize_language("auto") is None
    assert _normalize_language("") is None
    assert _normalize_language(None) is None


# ---------------------------------------------------------------------------
# FastAPI endpoint tests (offline -- patches at router level)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi/httpx not installed")
class TestTranscribeEndpoint:
    def setup_method(self):
        self.client = TestClient(app)

    def test_empty_upload_returns_400(self):
        """Zero-byte audio upload -> 400."""
        res = self.client.post(
            "/ai/transcribe",
            files={"file": ("empty.wav", b"", "audio/wav")},
        )
        assert res.status_code == 400

    def test_valid_wav_with_mock(self, monkeypatch):
        """Valid WAV with mocked transcribe_audio returns 200 with correct JSON."""
        from app.models.speech import TranscriptionResult
        import app.routers.speech as speech_router_module

        def _fake_transcribe(audio_bytes, filename="audio.wav", language=None, model=None):
            return TranscriptionResult(
                text="hi bambupasun banavaleli hatane vinaleli topali ahe.",
                language=language or "mr",
                confidence=0.87,
            )

        monkeypatch.setattr(speech_router_module, "transcribe_audio", _fake_transcribe)

        wav = _make_wav_bytes(16000)
        res = self.client.post(
            "/ai/transcribe",
            files={"file": ("speech.wav", wav, "audio/wav")},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["text"] == "hi bambupasun banavaleli hatane vinaleli topali ahe."
        assert body["language"] == "mr"
        assert body["confidence"] == 0.87

    def test_audio_param_fallback_when_file_is_empty(self, monkeypatch):
        """Swagger UI scenario: file parameter is empty string/0 bytes, audio parameter has WAV."""
        from app.models.speech import TranscriptionResult
        import app.routers.speech as speech_router_module

        def _fake_transcribe(audio_bytes, filename="audio.wav", language=None, model=None):
            return TranscriptionResult(text="audio uploaded via audio param", language="en", confidence=0.9)

        monkeypatch.setattr(speech_router_module, "transcribe_audio", _fake_transcribe)

        wav = _make_wav_bytes(16000)
        res = self.client.post(
            "/speech/transcribe",
            files={"file": ("empty.wav", b"", "audio/wav"), "audio": ("real.wav", wav, "audio/wav")},
            data={"language": "en"},
        )
        assert res.status_code == 200
        assert res.json()["text"] == "audio uploaded via audio param"
        assert res.json()["language"] == "en"

    def test_invalid_short_audio_returns_400(self):
        """Invalid/corrupt audio bytes raise ValueError -> 400 Bad Request."""
        res = self.client.post(
            "/ai/transcribe",
            files={"audio": ("corrupt.wav", b"not_a_valid_wav_file_at_all", "audio/wav")},
        )
        assert res.status_code == 400
        assert "invalid" in res.json()["detail"].lower() or "too small" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Live Whisper tests (skipped unless whisper installed AND ffmpeg on PATH)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not WHISPER_AVAILABLE, reason="openai-whisper not installed")
class TestLiveWhisper:
    """
    Live tests that actually load the Whisper 'base' model and run inference.
    These are integration tests (~5-20s first run due to torch startup).
    Synthetic WAV audio is used so no TTS dependency is needed.

    NOTE: Whisper uses ffmpeg to decode audio files. On Windows, ffmpeg must
    be on PATH. If it is not, the tests are skipped (not failed) with a clear
    message.
    """

    @pytest.fixture(scope="class")
    def whisper_model(self):
        import whisper
        return whisper.load_model("base")

    @staticmethod
    def _is_ffmpeg_error(exc):
        """Return True if exc is a WinError 2 (ffmpeg not found on PATH)."""
        return "WinError 2" in str(exc) or "cannot find the file" in str(exc).lower()

    def test_live_english_wav(self, whisper_model):
        """
        Pass a synthetic WAV through the real Whisper model.
        Verifies the pipeline contract: text (str), language (str), confidence (float).
        Skipped if ffmpeg is not available on PATH.
        """
        from app.services.speech_service import transcribe_audio
        wav = _make_wav_bytes(num_frames=32000, amplitude=8000)  # 2s square wave
        try:
            result = transcribe_audio(wav, filename="test.wav", model=whisper_model)
            assert isinstance(result.text, str)
            assert result.language is not None
            assert result.confidence is None or 0.0 <= result.confidence <= 1.0
        except ValueError as exc:
            # Whisper may legitimately return empty text for a pure square wave
            assert "empty transcription" in str(exc).lower()
        except RuntimeError as exc:
            if self._is_ffmpeg_error(exc):
                pytest.skip("ffmpeg not found on PATH -- install ffmpeg to run live audio tests")
            raise

    def test_live_pipeline_structure(self, whisper_model):
        """TranscriptionResult returned by live model is a valid Pydantic object."""
        from app.services.speech_service import transcribe_audio
        from app.models.speech import TranscriptionResult
        wav = _make_wav_bytes(num_frames=32000, amplitude=8000)
        try:
            result = transcribe_audio(wav, filename="test.wav", model=whisper_model)
            assert isinstance(result, TranscriptionResult)
        except ValueError:
            pass  # empty transcription for a pure tone is acceptable
        except RuntimeError as exc:
            if self._is_ffmpeg_error(exc):
                pytest.skip("ffmpeg not found on PATH -- install ffmpeg to run live audio tests")
            raise
