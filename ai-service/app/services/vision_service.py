"""
Product vision service — Gate 5: Product Vision / Attribute Extraction.

Uses a multimodal vision LLM (Gemini or OpenAI API) to identify artisan products
and extract structured attributes without fabricating unsupported claims,
per 05_GATE_PRODUCT_VISION.md.
"""

import json
import os
import re
from typing import Optional

from app.models.product import ProductVisionResult

VISION_PROMPT = """Analyze this artisan product image.

Return JSON with:
product_name
category
material
color
craft_type
style
visible_features
confidence

Only report attributes supported by the image.
If an attribute cannot be determined, use null.
Do not invent dimensions, certifications, origin, material, or features.
"""


def _clean_json_string(text: str) -> str:
    """Extract raw JSON from possible markdown code fences or conversational text."""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        return fence_match.group(1).strip()
    # Otherwise find the outermost { ... }
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        return brace_match.group(0).strip()
    return text


def analyze_product(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    client: Optional[object] = None,
) -> ProductVisionResult:
    """
    Analyze an artisan product image using a multimodal LLM to extract attributes.

    Args:
        image_bytes: raw bytes of the product image.
        mime_type: MIME type of the image (e.g. image/jpeg, image/png).
        client: optional injected client (for testing/mocking).

    Returns:
        Validated ProductVisionResult containing structured product attributes.

    Raises:
        RuntimeError: if no LLM API key is configured and no client is provided.
        ValueError: if the image cannot be processed or the model output cannot be parsed.
    """
    if not image_bytes:
        raise ValueError("Image data is empty")

    # If emulator mode is enabled via environment variable
    if os.getenv("AI_EMULATOR_MODE", "").lower() in ("1", "true", "yes") or os.getenv("VISION_EMULATOR_MODE", "").lower() in ("1", "true", "yes"):
        return _emulate_vision(image_bytes, mime_type)

    # If a mock or pre-configured client was injected, use it directly
    if client is not None:
        return _call_client(client, image_bytes, mime_type)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        return _call_gemini(gemini_key, image_bytes, mime_type)
    elif openai_key:
        return _call_openai(openai_key, image_bytes, mime_type)
    else:
        raise RuntimeError(
            "No LLM API key configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env "
            "before calling analyze_product()."
        )


def _emulate_vision(image_bytes: bytes, mime_type: str) -> ProductVisionResult:
    """Deterministic emulator for product vision attribute extraction."""
    return ProductVisionResult(
        product_name="Handcrafted Terracotta Clay Pottery",
        category="Pottery & Ceramics",
        material="Terracotta Clay",
        color="Earthy Terracotta Brown",
        craft_type="Wheel Thrown",
        style="Traditional Indian Folk",
        visible_features=["smooth finish", "wheel ridges", "traditional artisan shape"],
        confidence=0.95,
    )



def _call_gemini(api_key: str, image_bytes: bytes, mime_type: str) -> ProductVisionResult:
    """Execute product attribute extraction via Google Gemini API."""
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed. Run `pip install google-genai`.") from exc

    client = genai.Client(api_key=api_key)

    # Normalize mime_type if needed
    if "png" in mime_type.lower():
        effective_mime = "image/png"
    elif "webp" in mime_type.lower():
        effective_mime = "image/webp"
    else:
        effective_mime = "image/jpeg"

    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
        "gemini-flash-lite-latest",
        "gemini-2.5-flash",
    ]
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_exc = None
    response = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    genai.types.Part.from_bytes(data=image_bytes, mime_type=effective_mime),
                    VISION_PROMPT,
                ],
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            break
        except Exception as exc:
            last_exc = exc
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "404" in err_str:
                continue
            raise RuntimeError(f"Gemini vision call failed: {exc}") from exc

    if response is None:
        raise RuntimeError(f"Gemini vision call failed: {last_exc}") from last_exc

    raw_text = getattr(response, "text", "") or ""
    return _parse_llm_json(raw_text)



def _call_openai(api_key: str, image_bytes: bytes, mime_type: str) -> ProductVisionResult:
    """Execute product attribute extraction via OpenAI API."""
    import base64
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai is not installed. Run `pip install openai`.") from exc

    client = OpenAI(api_key=api_key)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                        },
                    ],
                }
            ],
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI vision call failed: {exc}") from exc

    raw_text = response.choices[0].message.content or ""
    return _parse_llm_json(raw_text)


def _call_client(client: object, image_bytes: bytes, mime_type: str) -> ProductVisionResult:
    """Execute with an injected mock or custom client for testing."""
    if hasattr(client, "analyze"):
        res = client.analyze(image_bytes=image_bytes, mime_type=mime_type)
        if isinstance(res, ProductVisionResult):
            return res
        if isinstance(res, dict):
            return ProductVisionResult.model_validate(res)
        if isinstance(res, str):
            return _parse_llm_json(res)
    raise ValueError("Injected client must implement analyze()")


def _parse_llm_json(raw_text: str) -> ProductVisionResult:
    """Clean, parse, and validate JSON response into a ProductVisionResult."""
    clean_text = _clean_json_string(raw_text)
    try:
        data = json.loads(clean_text)
    except Exception as exc:
        raise ValueError(f"LLM returned invalid JSON: {clean_text[:200]}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"LLM returned non-object JSON: {data}")

    return ProductVisionResult.model_validate(data)
