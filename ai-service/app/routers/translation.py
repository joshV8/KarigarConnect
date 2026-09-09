"""
Translation router — Gate 7.

Exposes POST /ai/translate.
Accepts a JSON payload with source text and optional source_language,
and returns structured translations for English and Hindi along with
the preserved original text.
"""

from fastapi import APIRouter, HTTPException

from app.models.translation import TranslationRequest, TranslationResult
from app.services.translation_service import translate_text

router = APIRouter(prefix="/ai", tags=["translation"])


@router.post("/translate", response_model=TranslationResult)
def translate(payload: TranslationRequest) -> TranslationResult:
    """
    Translate artisan's regional-language text directly into English and Hindi.

    Accepts:
        - text: non-empty string to translate
        - source_language: optional ISO 639-1 code (e.g. "mr", "hi", "en", "ta", "te")

    Returns:
        - source_language: detected or specified source language
        - original: original input text (strictly preserved)
        - translations: dict with "en" and "hi" translations
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty or blank.")

    try:
        result = translate_text(
            text=payload.text,
            source_language=payload.source_language,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Translation service encountered an unexpected error: {exc}",
        )
