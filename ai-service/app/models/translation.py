"""
Translation models — Gate 7: Translation.

Defines Pydantic schemas for the translation service and endpoint
per 07_GATE_TRANSLATION.md.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """
    Input schema for POST /ai/translate.
    """
    text: str = Field(..., min_length=1, description="Source text to translate")
    source_language: Optional[str] = Field(
        default=None,
        description="Optional ISO 639-1 language code (e.g., 'mr', 'hi', 'en'). Auto-detected if omitted.",
    )


class TranslationResult(BaseModel):
    """
    Output schema for POST /ai/translate.
    """
    source_language: str = Field(..., description="Detected or specified source ISO 639-1 language code")
    original: str = Field(..., description="Original untranslated source text")
    translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping target language codes (e.g., 'en', 'hi') to translated text",
    )
