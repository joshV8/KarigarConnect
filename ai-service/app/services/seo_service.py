"""
SEO Catalog Service — Gate 9.

Generates searchable, market-ready marketplace SEO metadata (seo_title, meta_description, keywords)
grounded strictly in verified product information without fabricated claims or unrelated trending keywords.

Per 09_GATE_SEO_CATALOG.md:
- Uses ONLY supplied product information.
- Keywords must be directly relevant to the product.
- Do not add unrelated trending keywords.
- Returns JSON matching SEOResult:
  seo_title, meta_description, keywords.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from app.models.seo import SEOResult

logger = logging.getLogger("artisan_ai_service.seo")

SEO_PROMPT_TEMPLATE = """You are an e-commerce SEO specialist for an authentic Indian artisan marketplace.

Generate marketplace SEO metadata using ONLY the supplied product information below.

CRITICAL RULES:
1. Keywords must be directly relevant to the product.
2. Do NOT add unrelated trending keywords (e.g. no unrelated celebrities, unverified brands, or random viral tags).
3. Do NOT make fabricated claims (e.g. certifications, health claims, non-existent features).
4. seo_title should be concise, professional, and optimized for search (e.g. "[Product Name] | Handmade Indian Handicraft").
5. meta_description should be an engaging, keyword-rich summary (150-160 characters).

--- Supplied Product Information ---
{supplied_info}
-----------------------------------

Respond STRICTLY with a valid JSON object matching this exact schema:
{{
  "seo_title": "Product Title | Category/Craft Handicraft",
  "meta_description": "Search-optimized 150-160 character description summarizing the authentic artisan item.",
  "keywords": ["keyword 1", "keyword 2", "keyword 3", "keyword 4"]
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


def _parse_seo_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON string safely into a dictionary."""
    cleaned = _clean_json_string(raw_text)
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        return data
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse SEO JSON: %s\nRaw output: %s", exc, raw_text)
        raise ValueError(f"Could not parse LLM SEO response: {exc}") from exc


def _format_supplied_info(
    title: Optional[str] = None,
    description: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    transcription: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """Format available product information for the prompt."""
    lines = []
    if title and title.strip():
        lines.append(f"Product Title: {title.strip()}")
    if category and category.strip():
        lines.append(f"Category: {category.strip()}")
    if description and description.strip():
        lines.append(f"Description: {description.strip()}")
    if attributes:
        lines.append("Attributes:")
        for k, v in attributes.items():
            if v is not None and v != "" and v != []:
                if isinstance(v, list):
                    lines.append(f"  - {k}: {', '.join(str(i) for i in v)}")
                else:
                    lines.append(f"  - {k}: {v}")
    if transcription and transcription.strip():
        lines.append(f"Artisan Context: {transcription.strip()}")

    return "\n".join(lines)


def generate_seo_metadata(
    title: Optional[str] = None,
    description: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    transcription: Optional[str] = None,
    category: Optional[str] = None,
    client: Optional[Any] = None,
) -> SEOResult:
    """
    Generate marketplace SEO metadata from verified product information.

    Args:
        title: Optional product title.
        description: Optional product description or summary.
        attributes: Optional dictionary of visual or product attributes.
        transcription: Optional voice transcription or artisan notes.
        category: Optional product category.
        client: Optional injected mock client for testing.

    Returns:
        SEOResult with seo_title, meta_description, and keywords.

    Raises:
        ValueError: If all inputs are empty or blank.
        RuntimeError: If LLM service call fails and no provider is configured.
    """
    has_title = bool(title and title.strip())
    has_desc = bool(description and description.strip())
    has_attr = bool(attributes and any(v is not None and v != "" and v != [] for v in attributes.values()))
    has_trans = bool(transcription and transcription.strip())
    has_cat = bool(category and category.strip())

    if not (has_title or has_desc or has_attr or has_trans or has_cat):
        raise ValueError("Cannot generate SEO metadata: no product information provided.")

    # Check if emulator mode is enabled
    if os.getenv("AI_EMULATOR_MODE", "").lower() in ("1", "true", "yes") or os.getenv("SEO_EMULATOR_MODE", "").lower() in ("1", "true", "yes"):
        return _emulate_seo(title, description, attributes, transcription, category)

    # Injected test client / mock
    if client is not None:
        return _call_client(client, title, description, attributes, transcription, category)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if gemini_key:
        return _call_gemini(gemini_key, title, description, attributes, transcription, category)
    elif openai_key:
        return _call_openai(openai_key, title, description, attributes, transcription, category)
    else:
        raise RuntimeError("No LLM provider configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env.")


def _emulate_seo(
    title: Optional[str],
    description: Optional[str],
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    category: Optional[str],
) -> SEOResult:
    """
    Deterministic SEO emulator producing authentic, search-optimized metadata
    for known artisan handicrafts without external cloud dependencies.
    """
    attrs = attributes or {}
    product_name = title or attrs.get("product_name")
    material = attrs.get("material") or ""
    cat = category or attrs.get("category") or "Handicraft"
    craft_type = attrs.get("craft_type") or ""

    combined_text = " ".join(filter(None, [title, description, transcription, str(attrs)])).lower()

    if "bamboo" in combined_text or "बांबू" in combined_text or "basket" in combined_text:
        seo_title = "Handwoven Bamboo Basket | Handmade Indian Handicraft"
        meta_desc = "Discover authentic handwoven bamboo baskets crafted by rural Indian artisans. Eco-friendly, durable, and perfect for storage and home decor."
        keywords = [
            "bamboo basket",
            "handmade basket",
            "handwoven bamboo",
            "Indian handicraft",
            "eco friendly storage",
            "traditional cane craft",
        ]
    elif "terracotta" in combined_text or "clay" in combined_text or "मिट्टी" in combined_text or "diya" in combined_text:
        seo_title = "Handmade Terracotta Clay Diya | Traditional Indian Festive Pottery"
        meta_desc = "Authentic handcrafted clay diya shaped on a traditional potter's wheel. Ideal for festive pooja celebrations, Diwali, and traditional home ambiance."
        keywords = [
            "terracotta diya",
            "handmade clay lamp",
            "Indian festive pottery",
            "traditional clay diya",
            "pottery handicraft",
        ]
    else:
        name = product_name or f"Handmade {material} {cat}".strip()
        seo_title = f"{name} | Authentic Indian {cat}"
        meta_desc = f"Shop authentic {name.lower()} crafted by traditional Indian artisans. Sustainable, handmade, and culturally inspired."
        keywords = [
            name.lower(),
            f"handmade {cat.lower()}",
            "Indian handicraft",
            "artisan made",
        ]
        if material:
            keywords.append(f"{str(material).lower()} craft")

    return SEOResult(
        seo_title=seo_title,
        meta_description=meta_desc,
        keywords=keywords,
    )


def _call_client(
    client: Any,
    title: Optional[str],
    description: Optional[str],
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    category: Optional[str],
) -> SEOResult:
    """Execute SEO generation with an injected mock or client."""
    supplied_info = _format_supplied_info(title, description, attributes, transcription, category)
    prompt = SEO_PROMPT_TEMPLATE.format(supplied_info=supplied_info)

    if hasattr(client, "generate_content"):
        resp = client.generate_content(prompt)
        raw_text = getattr(resp, "text", "") or ""
    elif callable(client):
        res = client(title=title, description=description, attributes=attributes, transcription=transcription, category=category)
        if isinstance(res, SEOResult):
            return res
        raw_text = str(res)
    else:
        raise ValueError(f"Unsupported mock client type: {type(client)}")

    data = _parse_seo_json(raw_text)
    return SEOResult(**data)


def _call_gemini(
    api_key: str,
    title: Optional[str],
    description: Optional[str],
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    category: Optional[str],
) -> SEOResult:
    """Execute SEO generation via Gemini 2.5 Flash."""
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed. Run `pip install google-genai`.") from exc

    supplied_info = _format_supplied_info(title, description, attributes, transcription, category)
    prompt = SEO_PROMPT_TEMPLATE.format(supplied_info=supplied_info)

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
                    temperature=0.2,
                ),
            )
            break
        except Exception as exc:
            last_exc = exc
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str or "404" in err_str:
                continue
            logger.exception("Gemini SEO generation failed: %s", exc)
            raise RuntimeError(f"Gemini SEO generation failed: {exc}") from exc

    if response is None:
        logger.exception("Gemini SEO generation failed across models: %s", last_exc)
        raise RuntimeError(f"Gemini SEO generation failed: {last_exc}") from last_exc


    raw_text = getattr(response, "text", "") or ""
    data = _parse_seo_json(raw_text)
    return SEOResult(**data)


def _call_openai(
    api_key: str,
    title: Optional[str],
    description: Optional[str],
    attributes: Optional[Dict[str, Any]],
    transcription: Optional[str],
    category: Optional[str],
) -> SEOResult:
    """Execute SEO generation via OpenAI gpt-4o-mini."""
    try:
        import openai
    except ImportError as exc:
        raise RuntimeError("openai is not installed. Run `pip install openai`.") from exc

    supplied_info = _format_supplied_info(title, description, attributes, transcription, category)
    prompt = SEO_PROMPT_TEMPLATE.format(supplied_info=supplied_info)

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw_text = response.choices[0].message.content or ""
    except Exception as exc:
        logger.exception("OpenAI SEO generation failed: %s", exc)
        raise RuntimeError(f"OpenAI SEO generation failed: {exc}") from exc

    data = _parse_seo_json(raw_text)
    return SEOResult(**data)
