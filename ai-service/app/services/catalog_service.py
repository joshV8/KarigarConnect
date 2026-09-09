"""
Catalog Orchestration Service — Gate 11.

Connects the completed AI modules into one unified end-to-end pipeline:
Image -> Validation -> Background Removal -> Enhancement -> Vision -> Voice -> Translation -> Description -> SEO -> Pricing -> Catalog JSON.

Per 11_GATE_CATALOG_ORCHESTRATION.md:
- Reuses existing service functions without duplicating logic.
- Returns complete catalog response with product, images, description, seo, and pricing.
"""

import base64
import logging
from typing import Any, Dict, Optional

from app.models.catalog import (
    CatalogDescriptions,
    CatalogImages,
    CatalogPricing,
    CatalogProductInfo,
    CatalogResult,
    CatalogSEO,
)
from app.services.background_service import remove_background
from app.services.description_service import generate_product_description
from app.services.enhancement_service import enhance_image
from app.services.image_service import validate_image
from app.services.pricing_service import calculate_price_recommendation
from app.services.seo_service import generate_seo_metadata
from app.services.speech_service import transcribe_audio
from app.services.translation_service import translate_text
from app.services.vision_service import analyze_product

logger = logging.getLogger("artisan_ai_service.catalog")


def _bytes_to_data_uri(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """Convert raw image bytes to a base64 Data URI."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def orchestrate_catalog(
    image_bytes: bytes,
    image_filename: str = "product.jpg",
    image_mime_type: str = "image/jpeg",
    audio_bytes: Optional[bytes] = None,
    audio_filename: str = "audio.wav",
    raw_material_cost: float = 0.0,
    labour_cost: float = 0.0,
    packaging_cost: float = 0.0,
    other_cost: float = 0.0,
    quality: Optional[str] = "standard",
    demand: Optional[str] = "medium",
    artisan_notes: Optional[str] = None,
    skip_bg_removal: bool = False,
) -> CatalogResult:
    """
    Execute full catalog orchestration pipeline from raw artisan inputs.

    Args:
        image_bytes: Raw product image bytes.
        image_filename: Name of the uploaded photo.
        image_mime_type: MIME type of the uploaded photo.
        audio_bytes: Optional raw audio bytes of artisan voice description.
        audio_filename: Audio file name.
        raw_material_cost: Cost of raw materials in INR.
        labour_cost: Cost of artisan labour in INR.
        packaging_cost: Packaging cost in INR.
        other_cost: Miscellaneous overhead in INR.
        quality: Artisan quality level ('standard', 'high', 'premium').
        demand: Market demand level ('low', 'medium', 'high').
        artisan_notes: Optional textual artisan commentary.
        skip_bg_removal: If True, skips background removal (useful for fast testing).

    Returns:
        Consolidated CatalogResult.
    """
    logger.info("Starting catalog orchestration for %s", image_filename)

    # 1. Image Validation (Gate 2)
    validate_image(image_bytes)

    # 2. Background Removal (Gate 3) & Image Enhancement (Gate 4)
    if skip_bg_removal:
        processed_bytes = image_bytes
    else:
        try:
            bg_removed_bytes = remove_background(image_bytes)
            processed_bytes = enhance_image(bg_removed_bytes)
        except Exception as exc:
            logger.warning("Background removal or enhancement failed, falling back to original: %s", exc)
            processed_bytes = image_bytes

    # 3. Product Vision / Attribute Extraction (Gate 5)
    vision_result = analyze_product(processed_bytes, mime_type="image/png")
    detected_name = vision_result.product_name or "Handcrafted Artisan Product"
    detected_cat = vision_result.category or "Handicrafts"
    detected_mat = vision_result.material or "Artisanal Material"

    vision_attrs = {
        "product_name": detected_name,
        "category": detected_cat,
        "material": detected_mat,
        "color": vision_result.color,
        "craft_type": vision_result.craft_type,
        "style": vision_result.style,
        "visible_features": vision_result.visible_features,
    }

    # 4. Speech-to-Text (Gate 6) & Translation (Gate 7) [Optional]
    transcription_text: Optional[str] = None
    translated_en: Optional[str] = None
    translated_hi: Optional[str] = None
    original_voice_text: Optional[str] = None

    if audio_bytes and len(audio_bytes) > 0:
        try:
            trans_res = transcribe_audio(audio_bytes, filename=audio_filename)
            transcription_text = trans_res.text
            original_voice_text = trans_res.text

            # If voice transcription is present, translate directly
            trans_result = translate_text(transcription_text, source_language=trans_res.language)
            translated_en = trans_result.translations.get("en")
            translated_hi = trans_result.translations.get("hi")
        except Exception as exc:
            logger.warning("Voice transcription or translation skipped due to error: %s", exc)

    # 5. Product Description Generation (Gate 8)
    combined_voice = translated_en or transcription_text
    desc_result_en = generate_product_description(
        attributes=vision_attrs,
        transcription=combined_voice,
        artisan_notes=artisan_notes,
        language="en",
    )

    desc_result_hi = generate_product_description(
        attributes=vision_attrs,
        transcription=translated_hi or combined_voice,
        artisan_notes=artisan_notes,
        language="hi",
    )

    # 6. SEO Metadata (Gate 9)
    seo_result = generate_seo_metadata(
        title=desc_result_en.title,
        description=desc_result_en.short_description,
        attributes=vision_attrs,
        transcription=combined_voice,
        category=detected_cat,
    )

    # 7. Pricing Recommendation (Gate 10)
    # If costs are unspecified (0.0), supply realistic artisan baseline defaults for the category
    mat_cost = raw_material_cost if raw_material_cost > 0 else 250.0
    lab_cost = labour_cost if labour_cost > 0 else 200.0
    pkg_cost = packaging_cost if packaging_cost > 0 else 40.0
    oth_cost = other_cost if other_cost > 0 else 20.0

    pricing_result = calculate_price_recommendation(
        raw_material_cost=mat_cost,
        labour_cost=lab_cost,
        packaging_cost=pkg_cost,
        other_cost=oth_cost,
        category=detected_cat,
        material=detected_mat,
        quality=quality,
        demand=demand,
    )

    # Build Images output
    orig_uri = _bytes_to_data_uri(image_bytes, image_mime_type)
    proc_uri = _bytes_to_data_uri(processed_bytes, "image/png")

    return CatalogResult(
        product=CatalogProductInfo(
            name=desc_result_en.title,
            category=detected_cat,
            material=detected_mat,
        ),
        images=CatalogImages(
            original=orig_uri,
            processed=proc_uri,
        ),
        description=CatalogDescriptions(
            english=desc_result_en.description,
            hindi=desc_result_hi.description,
            original=original_voice_text or artisan_notes or desc_result_en.description,
        ),
        seo=CatalogSEO(
            title=seo_result.seo_title,
            keywords=seo_result.keywords,
        ),
        pricing=CatalogPricing(
            recommended=pricing_result.recommended,
            minimum=pricing_result.minimum,
            maximum=pricing_result.maximum,
            currency=pricing_result.currency,
            explanation=pricing_result.explanation,
        ),
    )
