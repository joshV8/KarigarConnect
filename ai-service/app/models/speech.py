"""
Speech models - Gate 6: Speech-to-Text.

Defines the Pydantic schema for transcription output from the
regional-language speech-to-text service, per 06_GATE_SPEECH_TO_TEXT.md.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TranscriptionResult(BaseModel):
    """
    Structured output from the speech-to-text transcription service.

    Per 06_GATE_SPEECH_TO_TEXT.md:
    - text: the transcribed text (required)
    - language: ISO 639-1 language code detected by the model
    - confidence: average segment-level log-probability mapped to 0.0-1.0
    """

    model_config = ConfigDict(extra="ignore")

    text: str = Field(description="Transcribed text from the audio recording.")
    language: Optional[str] = Field(
        default=None,
        description="Detected ISO 639-1 language code, e.g. 'mr', 'hi', 'en'.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Average transcription confidence between 0.0 and 1.0.",
    )
