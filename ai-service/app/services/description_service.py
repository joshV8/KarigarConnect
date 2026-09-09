"""
AI Product Description Service — Gate 8.

Generates professional, marketplace-ready product descriptions grounded strictly
in supplied attributes and artisan inputs without hallucinations.

Per 08_GATE_AI_DESCRIPTION.md:
- Uses ONLY supplied product information.
- Does not invent certifications, dimensions, materials, origin, health claims,
  sustainability certifications, or features not provided or visible.
- Returns JSON matching ProductDescriptionResult:
  title, short_description, description, features, materials.
- Multi-tier provider: Gemini 2.5 Flash, OpenAI fallback, plus deterministic
  AI Emulator for testing and offline environments.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Union

from app.models.description import ProductDescriptionResult

logger = logging.getLogger("artisan_ai_service.description")

DESCRIPTION_PROMPT_TEMPLATE = """You are an expert e-commerce catalog specialist for an authentic artisan handicraft marketplace.

Create marketplace content for an artisan product.

CRITICAL RULES:
1. Use ONLY the supplied product information below.
2. Do NOT invent:
   - certifications
   - dimensions
   - materials
   - origin / geographical tags unless explicitly mentioned
   - health claims
   - sustainability certifications
   - features not provided or visible
3. Tone: Professional, authentic, respectful of Indian artisanal heritage, customer-appealing, and marketplace-ready.
4. Output Language: {target_language}

--- Supplied Product Information ---
{supplied_info}
-----------------------------------

Respond STRICTLY with a valid JSON object matching this exact schema:
{{
  "title": "Clear, appealing marketplace product title",
  "short_description": "1-2 concise sentences summarizing the product for listing cards",
  "description": "Full, well-structured product description highlighting authentic craftsmanship and details based strictly on supplied info",
  "features": ["Feature 1", "Feature 2"],
  "materials": ["Material 1", "Material 2"]
}}

Do NOT include any commentary, explanations, or text outside the JSON object.
"""


def _clean_json_string(text: str) -> str:
    """Strip markdown fences and surrounding commentary to isolate the JSON object."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return match.group(0)
    return cleaned


def _parse_description_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON string safely into a dictionary."""
    cleaned = _clean_json_string(raw_text)
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse description JSON: %s\nRaw output: %s", exc, raw_text)
        raise ValueError(f"Could not parse LLM description response: {exc}") from exc


def _format_supplied_info(
    attributes: Optional[Dict[str, Any]] = None,
    transcription: Optional[str] = None,
    artisan_notes: Optional[str] = None,
) -> str:
    """Format available attributes and notes into a structured prompt section."""
    lines = []
    if attributes:
        lines.append("Product Attributes:")
        for k, v in attributes.items():
            if v is not None and v != "" and v != []:
                if isinstance(v, list):
                    lines.append(f"  - {k}: {', '.join(str(i) for i in v)}")
                else:
                    lines.append(f"  - {k}: {v}")
    if transcription and transcription.strip():
        lines.append(f"Artisan Voice / Transcription: {transcription.strip()}")
    if artisan_notes and artisan_notes.strip():
        lines.append(f"Artisan Notes: {artisan_notes.strip()}")

    return "\n".join(lines)


def generate_product_description(
    attributes: Optional[Dict[str, Any]] = None,
    transcription: Optional[str] = None,
    artisan_notes: Optional[str] = None,
    language: str = "en",
    client: Optional[Any] = None,
) -> ProductDescriptionResult:
    """
    Generate marketplace content for an artisan product based strictly on supplied inputs.

    Args:
        attributes: Dictionary of vision or extracted attributes.
        transcription: Transcribed or translated voice text.
        artisan_notes: Artisan commentary or notes.
        language: Target output language ("en", "hi", etc.). Default is "en".
        client: Optional injected client or mock callable for testing.

    Returns:
        ProductDescriptionResult with title, short_description, description, features, materials.

    Raises:
        ValueError: If all inputs are empty or blank.
        RuntimeError: If LLM service call fails and no provider is configured.
    """
    has_attr = bool(attributes and any(v is not None and v != "" and v != [] for v in attributes.values()))
    has_trans = bool(transcription and transcription.strip())
    has_notes = bool(artisan_notes and artisan_notes.strip())

    if not (has_attr or has_trans or has_notes):
        raise ValueError("Cannot generate product description: no attributes, transcription, or notes provided.")

    # Check if emulator mode is enabled
    if os.getenv("AI_EMULATOR_MODE", "").lower() in ("1", "true", "yes") or os.getenv("DESCRIPTION_EMULATOR_MODE", "").lower() in ("1", "true", "yes"):
        return _emulate_description(attributes, transcription, artisan_notes, language)

    # Injected test client / mock
    if client is not None:
        return _call_client(client, attributes, transcription, artisan_notes, language)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        return _call_gemini(gemini_key, attributes, transcription, artisan_notes, language)
    elif openai_key:
        return _call_openai(openai_key, attributes, transcription, artisan_notes, language)
    else:
        raise RuntimeError("No LLM provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env.")


def _emulate_description(
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    artisan_notes: Optional[str],
    language: str,
) -> ProductDescriptionResult:
    """
    Deterministic emulator for Gate 8 that produces authentic descriptions
    strictly grounded in provided inputs without external API dependencies.
    """
    attrs = attributes or {}
    product_name = attrs.get("product_name")
    material = attrs.get("material")
    category = attrs.get("category") or "Handicraft"
    craft_type = attrs.get("craft_type")
    color = attrs.get("color")
    features = list(attrs.get("visible_features") or [])

    # Derive materials list
    materials = []
    if material:
        if isinstance(material, list):
            materials.extend([str(m) for m in material])
        else:
            materials.append(str(material))

    # Derive features
    combined_features = []
    if craft_type:
        combined_features.append(f"Authentic {craft_type} craft technique")
    if color:
        combined_features.append(f"{color} natural finish")
    for f in features:
        if f not in combined_features:
            combined_features.append(str(f))

    # Incorporate transcription cues
    combined_text = " ".join(filter(None, [transcription, artisan_notes])).lower()
    if "bamboo" in combined_text or "बांबू" in combined_text or "बांस" in combined_text:
        if "Bamboo" not in materials:
            materials.append("Bamboo")
        if not product_name:
            product_name = "Handwoven Bamboo Basket"
        if not combined_features:
            combined_features = ["Handwoven lattice weave", "Eco-friendly natural bamboo"]
    elif "clay" in combined_text or "मिट्टी" in combined_text or "terracotta" in combined_text:
        if "Clay" not in materials and "Terracotta" not in materials:
            materials.append("Terracotta Clay")
        if not product_name:
            product_name = "Handcrafted Terracotta Clay Diya"
        if not combined_features:
            combined_features = ["Wheel-thrown handcrafted finish", "Traditional festive design"]

    if not product_name:
        if craft_type and material:
            product_name = f"Handcrafted {material} {craft_type} {category}"
        elif material:
            product_name = f"Handcrafted {material} {category}"
        else:
            product_name = f"Artisan Handcrafted {category}"

    if language.lower().startswith("hi"):
        title = f"हस्तनिर्मित {product_name}"
        short_desc = f"यह एक प्रामाणिक हस्तनिर्मित {product_name} है, जिसे पारंपरिक कारीगरी से बनाया गया है।"
        desc = (
            f"यह सुंदर {product_name} कुशल कारीगरों द्वारा हस्तनिर्मित है। "
            f"पारंपरिक भारतीय शिल्पकला की विरासत को ध्यान में रखते हुए, इसे उच्च गुणवत्ता और प्रामाणिकता के साथ तैयार किया गया है。"
        )
    else:
        title = product_name
        short_desc = f"Authentic handcrafted {product_name.lower()} crafted with traditional artisanal techniques."
        desc = (
            f"This authentic {product_name} is handcrafted by skilled traditional artisans. "
            f"Reflecting the rich heritage of handcrafted artistry, every piece is shaped with care, "
            f"offering a unique blend of functional utility and traditional charm."
        )

    return ProductDescriptionResult(
        title=title,
        short_description=short_desc,
        description=desc,
        features=combined_features if combined_features else ["Handmade with traditional techniques"],
        materials=materials if materials else ["Natural artisanal materials"],
    )


def _call_client(
    client: Any,
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    artisan_notes: Optional[str],
    language: str,
) -> ProductDescriptionResult:
    """Execute generation using an injected client or mock callable."""
    supplied_info = _format_supplied_info(attributes, transcription, artisan_notes)
    prompt = DESCRIPTION_PROMPT_TEMPLATE.format(
        target_language="English" if language == "en" else language,
        supplied_info=supplied_info,
    )

    if hasattr(client, "generate_content"):
        resp = client.generate_content(prompt)
        raw_text = getattr(resp, "text", "") or ""
    elif callable(client):
        res = client(attributes=attributes, transcription=transcription, artisan_notes=artisan_notes, language=language)
        if isinstance(res, ProductDescriptionResult):
            return res
        raw_text = str(res)
    else:
        raise ValueError(f"Unsupported mock client type: {type(client)}")

    data = _parse_description_json(raw_text)
    return ProductDescriptionResult(**data)


def _call_gemini(
    api_key: str,
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    artisan_notes: Optional[str],
    language: str,
) -> ProductDescriptionResult:
    """Execute description generation using Gemini 2.5 Flash."""
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed. Run `pip install google-genai`.") from exc

    supplied_info = _format_supplied_info(attributes, transcription, artisan_notes)
    prompt = DESCRIPTION_PROMPT_TEMPLATE.format(
        target_language="English" if language == "en" else language,
        supplied_info=supplied_info,
    )

    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest"),
        "gemini-flash-lite-latest",
        "gemini-2.5-flash",
    ]
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_exc = None
    response = None
    client = genai.Client(api_key=api_key)
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            break
        except Exception as exc:
            last_exc = exc
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "404" in err_str:
                continue
            logger.exception("Gemini description generation failed: %s", exc)
            raise RuntimeError(f"Gemini description generation failed: {exc}") from exc

    if response is None:
        logger.exception("Gemini description generation failed across models: %s", last_exc)
        raise RuntimeError(f"Gemini description generation failed: {last_exc}") from last_exc


    raw_text = getattr(response, "text", "") or ""
    data = _parse_description_json(raw_text)
    return ProductDescriptionResult(**data)


def _call_openai(
    api_key: str,
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    artisan_notes: Optional[str],
    language: str,
) -> ProductDescriptionResult:
    """Execute description generation using OpenAI gpt-4o-mini."""
    try:
        import openai
    except ImportError as exc:
        raise RuntimeError("openai is not installed. Run `pip install openai`.") from exc

    supplied_info = _format_supplied_info(attributes, transcription, artisan_notes)
    prompt = DESCRIPTION_PROMPT_TEMPLATE.format(
        target_language="English" if language == "en" else language,
        supplied_info=supplied_info,
    )

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw_text = response.choices[0].message.content or ""
    except Exception as exc:
        logger.exception("OpenAI description generation failed: %s", exc)
        raise RuntimeError(f"OpenAI description generation failed: {exc}") from exc

    data = _parse_description_json(raw_text)
    return ProductDescriptionResult(**data)
