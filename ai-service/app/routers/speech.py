"""
Speech-to-Text router — Gate 6.

Exposes POST /ai/transcribe.
Accepts a multipart audio file and returns a JSON transcription result.
"""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.models.speech import TranscriptionResult
from app.services.speech_service import transcribe_audio

router = APIRouter(tags=["speech"])


@router.post("/ai/transcribe", response_model=TranscriptionResult)
@router.post("/speech/transcribe", response_model=TranscriptionResult)
async def transcribe(
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    voice: Optional[UploadFile] = File(None),
    language: Optional[str] = Form(None),
) -> TranscriptionResult:
    """
    Transcribe an artisan's regional-language voice recording.

    Accepts: WAV, MP3, M4A, WEBM, OGG, FLAC, or any format ffmpeg can decode.
    Can be uploaded as multipart form parameter 'audio', 'file', or 'voice'.

    Returns:
        - text: transcribed text
        - language: detected ISO 639-1 language code (e.g. "mr", "hi", "en")
        - confidence: average 0–1 confidence derived from Whisper log-probs
    """
    upload = None
    data = b""

    # Check all candidate fields in case client or Swagger UI uses audio, file, or voice
    for candidate in (audio, file, voice):
        if candidate is not None:
            cand_data = await candidate.read()
            if cand_data:
                upload = candidate
                data = cand_data
                break

    if not data or upload is None:
        if file is None and audio is None and voice is None:
            raise HTTPException(status_code=400, detail="Uploaded audio file is missing.")
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    try:
        # Offload heavy CPU Whisper transcription to worker thread so ASGI loop is not blocked
        result = await run_in_threadpool(
            transcribe_audio,
            audio_bytes=data,
            filename=upload.filename or "audio.wav",
            language=language if (language and language.strip() and language.strip().lower() != "auto") else None,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed unexpectedly: {exc}",
        )
