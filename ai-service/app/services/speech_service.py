"""
Speech-to-Text service — Gate 6.

Uses OpenAI Whisper (open-source, runs locally, no API key required) to
transcribe regional-language artisan voice recordings into text.

Per 06_GATE_SPEECH_TO_TEXT.md:
- Accepts audio in any format Whisper supports (WAV, MP3, M4A, WEBM, OGG, …)
- Detects and returns the ISO 639-1 language code
- Returns a confidence score derived from segment-level log-probabilities
- Raises a controlled error instead of returning fake/empty text on failure
"""

import inspect
import io
import math
import os
import re
import shutil
import tempfile
import threading
from typing import Optional

from app.models.speech import TranscriptionResult

# Whisper model size to load.  "base" is fast (~74 MB) and handles
# Marathi / Hindi / English well enough for an MVP.  Override via env.
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
_model = None
_model_lock = threading.Lock()


def _ensure_ffmpeg_path():
    """Ensure ffmpeg is discoverable on PATH and available as ffmpeg/ffmpeg.exe."""
    if shutil.which("ffmpeg"):
        return
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        target_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        alias = os.path.join(ffmpeg_dir, target_name)

        # Try to create alias in imageio_ffmpeg directory
        if not os.path.exists(alias) and os.path.exists(ffmpeg_exe):
            try:
                shutil.copyfile(ffmpeg_exe, alias)
            except Exception:
                pass

        # If alias could not be created in package dir (e.g. permissions), use tempdir
        if not os.path.exists(alias):
            user_tools_dir = os.path.join(tempfile.gettempdir(), "whisper_ffmpeg")
            os.makedirs(user_tools_dir, exist_ok=True)
            temp_alias = os.path.join(user_tools_dir, target_name)
            if not os.path.exists(temp_alias) and os.path.exists(ffmpeg_exe):
                try:
                    shutil.copyfile(ffmpeg_exe, temp_alias)
                except Exception:
                    pass
            if user_tools_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = user_tools_dir + os.pathsep + os.environ.get("PATH", "")

        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


# Run at module load time so ffmpeg is available immediately
_ensure_ffmpeg_path()


def _infer_audio_extension(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Infer the correct audio file extension from container magic bytes,
    falling back to filename extension when magic bytes are inconclusive.
    """
    if not audio_bytes:
        return ".wav"

    # Container magic bytes are definitive
    if audio_bytes.startswith(b"RIFF") and len(audio_bytes) > 12 and audio_bytes[8:12] == b"WAVE":
        return ".wav"
    if audio_bytes.startswith(b"ID3") or (
        len(audio_bytes) > 2 and audio_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")
    ):
        return ".mp3"
    if len(audio_bytes) > 12 and b"ftyp" in audio_bytes[4:12]:
        return ".m4a"
    if audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        return ".webm"
    if audio_bytes.startswith(b"OggS"):
        return ".ogg"
    if audio_bytes.startswith(b"fLaC"):
        return ".flac"
    # ADTS AAC syncword (0xFFF...)
    if len(audio_bytes) > 2 and audio_bytes[0] == 0xFF and (audio_bytes[1] & 0xF0) == 0xF0:
        return ".aac"

    # Fallback to filename extension
    ext = os.path.splitext(filename or "")[-1].lower()
    known_exts = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".aac", ".wma", ".mp4"}
    if ext in known_exts:
        return ext

    return ".wav"


def _normalize_language(lang: Optional[str]) -> Optional[str]:
    """
    Normalize language hint to a valid Whisper ISO 639-1 code.
    Handles BCP-47 tags (e.g. 'mr-IN' -> 'mr', 'hi-IN' -> 'hi', 'en-US' -> 'en')
    and common language names (e.g. 'marathi' -> 'mr', 'hindi' -> 'hi').
    """
    if not lang:
        return None
    cleaned = lang.strip().lower()
    if cleaned in ("", "auto", "none", "null", "undefined"):
        return None

    # Handle regional subtag like 'mr-IN' or 'hi_IN'
    primary = re.split(r"[-_]", cleaned)[0]

    try:
        import whisper.tokenizer
        if primary in whisper.tokenizer.LANGUAGES:
            return primary
        if cleaned in whisper.tokenizer.TO_LANGUAGE_CODE:
            return whisper.tokenizer.TO_LANGUAGE_CODE[cleaned]
        if primary in whisper.tokenizer.TO_LANGUAGE_CODE:
            return whisper.tokenizer.TO_LANGUAGE_CODE[primary]
    except Exception:
        pass

    return primary if len(primary) == 2 else None


def _load_model(whisper_module):
    """Load Whisper once, on demand, instead of per transcription request."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = whisper_module.load_model(WHISPER_MODEL_SIZE)
    return _model


def preload_whisper_model():
    """Optional warmup helper to load Whisper model ahead of time."""
    try:
        import whisper
        return _load_model(whisper)
    except Exception:
        return None


def _avg_confidence(segments: list) -> Optional[float]:
    """
    Convert Whisper's per-segment avg_logprob values to a 0–1 confidence score.

    Whisper reports avg_logprob per segment, typically in the range [-1.5, 0].
    We clamp and linearly scale that range to [0, 1].
    """
    if not segments:
        return None
    log_probs = [s.get("avg_logprob", -1.0) for s in segments]
    mean_lp = sum(log_probs) / len(log_probs)
    # Clamp to [-1.5, 0] then scale to [0, 1]
    clamped = max(-1.5, min(0.0, mean_lp))
    confidence = 1.0 + (clamped / 1.5)   # maps -1.5→0.0, 0→1.0
    return round(confidence, 4)


def _is_silence_hallucination(text: str, segments: list) -> bool:
    """Detect common Whisper hallucinations produced on silence or low noise."""
    normalized = text.strip().lower().strip(" .!?,[]()")
    hallucination_phrases = {
        "",
        "blank_audio",
        "music",
        "applause",
        "silence",
        "whispering",
        "thank you",
        "thank you.",
        "thanks for watching",
        "thanks for watching!",
        "subtitles by",
        "you",
    }
    if normalized in hallucination_phrases:
        return True

    # High no_speech_prob on all segments for very short text
    if segments and len(text) < 15:
        if all(s.get("no_speech_prob", 0.0) > 0.8 for s in segments):
            return True

    return False


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language: Optional[str] = None,
    model=None,
) -> TranscriptionResult:
    """
    Transcribe an audio recording to text using Whisper.

    Args:
        audio_bytes: Raw bytes of the audio file.
        filename:    Original filename — used to infer extension for the
                     temporary file so Whisper can select the right decoder.
        language:    Optional ISO language code hint (e.g. 'mr', 'hi', 'en').
        model:       Optional pre-loaded Whisper model (used in tests to
                     avoid re-loading the model on every call).

    Returns:
        TranscriptionResult with text, language, and confidence.

    Raises:
        ValueError: If audio_bytes is empty, corrupt, or the audio is silent /
                    too short to produce usable transcription.
        RuntimeError: If Whisper is not installed or internal system failure occurs.
    """
    if not audio_bytes:
        raise ValueError("Audio data is empty — no bytes received.")

    # Re-verify ffmpeg is available on PATH
    _ensure_ffmpeg_path()

    # Lazy-import so the service fails clearly when whisper is missing
    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "openai-whisper is not installed. "
            "Run `pip install openai-whisper` (also needs ffmpeg on PATH)."
        ) from exc

    # Determine the audio format extension
    ext = _infer_audio_extension(audio_bytes, filename)

    # Write audio bytes to a temporary file so Whisper can decode it
    tmp_path = None
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Lazily load and reuse the model across requests.
        if model is None:
            model = _load_model(whisper)

        transcribe_kwargs = {"verbose": None}
        norm_lang = _normalize_language(language)
        if norm_lang:
            transcribe_kwargs["language"] = norm_lang

        # Disable FP16 on CPU to prevent warning & fallback overhead
        try:
            import torch
            transcribe_kwargs["fp16"] = torch.cuda.is_available()
        except Exception:
            transcribe_kwargs["fp16"] = False

        # Safely filter kwargs based on model.transcribe signature
        # (supports real Whisper model as well as custom/mock model objects)
        call_kwargs = dict(transcribe_kwargs)
        try:
            sig = inspect.signature(model.transcribe)
            params = sig.parameters
            has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
            if not has_var_kw:
                call_kwargs = {k: v for k, v in transcribe_kwargs.items() if k in params}
        except Exception:
            pass

        try:
            result = model.transcribe(tmp_path, **call_kwargs)
        except TypeError:
            # Fallback if mock or wrapper rejects all extra kwargs
            result = model.transcribe(tmp_path)

    except Exception as exc:
        err_msg = str(exc).lower()
        # Classify bad/corrupt audio as ValueError (400 Bad Request) rather than server crash (500)
        if any(marker in err_msg for marker in ("failed to load audio", "invalid data found", "could not find codec", "error opening input")):
            raise ValueError(f"Invalid or unsupported audio file: {exc}") from exc
        raise RuntimeError(f"Whisper transcription failed: {exc}") from exc
    finally:
        # Always clean up the temp file
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    text: str = (result.get("text") or "").strip()
    detected_language: Optional[str] = result.get("language") or norm_lang
    segments: list = result.get("segments") or []

    # Reject empty transcription or silence hallucinations
    if not text or _is_silence_hallucination(text, segments):
        raise ValueError(
            "Whisper returned empty transcription. "
            "The audio may be silent, too short, or too noisy."
        )

    confidence = _avg_confidence(segments)

    return TranscriptionResult(text=text, language=detected_language, confidence=confidence)
