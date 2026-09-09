"""
Catalog router — Gate 11: Catalog Orchestration.

Exposes POST /ai/generate-catalog.
Accepts an artisan product photo, optional voice recording, and optional cost details,
and returns the complete, unified catalog JSON structure.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.models.catalog import CatalogResult
from app.services.catalog_service import orchestrate_catalog

router = APIRouter(tags=["catalog"])


@router.post("/ai/generate-catalog", response_model=CatalogResult)
async def generate_catalog(
    image: Optional[UploadFile] = File(None, description="Product photograph to be validated, segmented, and analyzed."),
    photo: Optional[UploadFile] = File(None, description="Product photograph alias."),
    file: Optional[UploadFile] = File(None, description="Product photograph alias."),
    audio: Optional[UploadFile] = File(None, description="Optional artisan voice audio file."),
    raw_material_cost: Optional[float] = Form(0.0, description="Raw material cost in INR."),
    labour_cost: Optional[float] = Form(0.0, description="Artisan labour cost in INR."),
    packaging_cost: Optional[float] = Form(0.0, description="Packaging cost in INR."),
    other_cost: Optional[float] = Form(0.0, description="Miscellaneous overhead in INR."),
    quality: Optional[str] = Form("standard", description="Artisan craft quality ('standard', 'high', 'premium')."),
    demand: Optional[str] = Form("medium", description="Market demand ('low', 'medium', 'high')."),
    artisan_notes: Optional[str] = Form(None, description="Optional artisan story or notes."),
    skip_bg_removal: Optional[bool] = Form(False, description="Optional flag to skip background removal for faster processing."),
) -> CatalogResult:
    """
    Generate a full marketplace product listing from a photo and optional audio.

    Coordinates:
        - Image validation, background removal, and enhancement
        - Product vision & attribute extraction
        - Voice transcription & multilingual translation
        - AI description generation (English & Hindi)
        - SEO title & keyword generation
        - Pricing recommendation and cost breakdown
    """
    img = image or photo or file
    if img is None:
        raise HTTPException(status_code=400, detail="Image file is missing.")
    image_bytes = await img.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    audio_bytes: Optional[bytes] = None
    audio_filename: str = "audio.wav"
    if audio is not None:
        audio_bytes = await audio.read()
        audio_filename = audio.filename or "audio.wav"

    try:
        result = orchestrate_catalog(
            image_bytes=image_bytes,
            image_filename=img.filename or "product.jpg",
            image_mime_type=img.content_type or "image/jpeg",
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            raw_material_cost=raw_material_cost or 0.0,
            labour_cost=labour_cost or 0.0,
            packaging_cost=packaging_cost or 0.0,
            other_cost=other_cost or 0.0,
            quality=quality,
            demand=demand,
            artisan_notes=artisan_notes,
            skip_bg_removal=bool(skip_bg_removal),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Catalog orchestration failed: {exc}",
        )


@router.post("/products/process")
@router.post("/ai/products/process")
async def process_product_contract(
    photo: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    raw_material_cost: Optional[float] = Form(0.0),
):
    """
    Person 1 (Flutter) ↔ Person 2/3 Contract endpoint per API_CONTRACT.md section 1.

    Accepts:
        photo: file (jpg/png)
        audio: file (m4a/wav) — optional voice description
        raw_material_cost: number

    Returns 200:
        {
            "image_url": "...",
            "description_hi": "...",
            "description_en": "...",
            "price": 850,
            "price_reason": "Cost ₹250 + labour + market rate for similar items"
        }
    """
    img = photo or image or file
    if img is None:
        raise HTTPException(status_code=400, detail="Photo file is missing.")
    img_bytes = await img.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="Photo file is empty.")

    aud_bytes: Optional[bytes] = None
    aud_fname = "audio.wav"
    if audio is not None:
        aud_bytes = await audio.read()
        aud_fname = audio.filename or "audio.wav"

    try:
        result = orchestrate_catalog(
            image_bytes=img_bytes,
            image_filename=img.filename or "product.jpg",
            image_mime_type=img.content_type or "image/jpeg",
            audio_bytes=aud_bytes,
            audio_filename=aud_fname,
            raw_material_cost=raw_material_cost or 0.0,
        )
        return {
            "id": f"prod_{uuid.uuid4().hex[:8]}",
            "image_url": result.images.processed or result.images.original or "",
            "description_hi": result.description.hindi or "",
            "description_en": result.description.english or "",
            "price": result.pricing.recommended,
            "price_reason": result.pricing.explanation or "",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Product processing failed: {exc}")


class BackendAIProcessRequest(BaseModel):
    product_id: Optional[int] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    voice_text: Optional[str] = None
    language: Optional[str] = "hi"
    raw_material_cost: Optional[float] = 0.0
    labour_cost: Optional[float] = 0.0
    packaging_cost: Optional[float] = 0.0


@router.post("/process")
async def process_backend_product(payload: BackendAIProcessRequest):
    """
    Complete AI Pipeline endpoint integrating:
    1. rembg (U^2-Net) -> Background removal & product cutout
    2. Pillow -> Contrast & sharpness image enhancement
    3. OpenAI Whisper -> Automatic vernacular voice note speech-to-text
    4. Gemini 2.5 Flash -> Multimodal vision extraction & bilingual copywriting
    """
    import os
    import json
    import re
    import uuid
    import httpx
    from app.services.background_service import remove_background
    from app.services.enhancement_service import enhance_image
    from app.services.speech_service import transcribe_audio

    # -------------------------------------------------------------
    # 1. Resolve Audio and Run Whisper Speech-to-Text
    # -------------------------------------------------------------
    transcribed_text: Optional[str] = payload.voice_text
    detected_audio_lang: str = payload.language or "hi"

    if payload.audio_url:
        audio_bytes: Optional[bytes] = None
        audio_fname = "voice_note.m4a"

        # Check local disk
        if "/uploads/audio/" in payload.audio_url:
            afname = payload.audio_url.split("/uploads/audio/")[-1]
            local_audio_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "uploads", "audio", afname)
            )
            if os.path.exists(local_audio_path):
                with open(local_audio_path, "rb") as f:
                    audio_bytes = f.read()
                audio_fname = afname

        # Or fetch over HTTP
        if not audio_bytes and payload.audio_url.startswith("http"):
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.get(payload.audio_url)
                    if resp.status_code == 200:
                        audio_bytes = resp.content
            except Exception as exc:
                print(f"[AI_SERVICE] Could not download audio_url: {exc}")

        # Run Whisper STT
        if audio_bytes and len(audio_bytes) > 0:
            try:
                whisper_res = transcribe_audio(audio_bytes, filename=audio_fname)
                if whisper_res and whisper_res.text:
                    transcribed_text = whisper_res.text.strip()
                    detected_audio_lang = whisper_res.language or detected_audio_lang
                    print(f"[WHISPER] Transcribed audio ({detected_audio_lang}): {transcribed_text}")
            except Exception as exc:
                print(f"[WHISPER] Speech transcription error: {exc}")

    # -------------------------------------------------------------
    # 2. Resolve Image and Run rembg Background Removal & Enhancement
    # -------------------------------------------------------------
    image_bytes: Optional[bytes] = None
    image_mime = "image/jpeg"
    original_local_filename: Optional[str] = None

    if payload.image_url:
        if "/uploads/products/" in payload.image_url:
            original_local_filename = payload.image_url.split("/uploads/products/")[-1]
            local_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "uploads", "products", original_local_filename)
            )
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    image_bytes = f.read()
                if original_local_filename.endswith(".png"):
                    image_mime = "image/png"
                elif original_local_filename.endswith(".webp"):
                    image_mime = "image/webp"

        if not image_bytes and payload.image_url.startswith("http"):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(payload.image_url)
                    if resp.status_code == 200:
                        image_bytes = resp.content
                        image_mime = resp.headers.get("content-type", "image/jpeg")
            except Exception as exc:
                print(f"[AI_SERVICE] Image download skipped/failed: {exc}")

    # Fallback placeholder if no image provided
    if not image_bytes:
        from PIL import Image
        import io
        img = Image.new("RGB", (300, 300), color=(180, 100, 60))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()
        image_mime = "image/jpeg"

    # Run rembg background removal + Pillow enhancement
    processed_image_bytes = image_bytes
    processed_image_url = payload.image_url

    try:
        bg_removed = remove_background(image_bytes)
        enhanced_bytes = enhance_image(bg_removed)
        processed_image_bytes = enhanced_bytes
        image_mime = "image/png"

        # Save enhanced cutout image to disk so frontend can display clean product photo
        uploads_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "uploads", "products")
        )
        os.makedirs(uploads_dir, exist_ok=True)
        out_filename = f"prod_{payload.product_id or 'item'}_{uuid.uuid4().hex[:8]}_enhanced.png"
        out_path = os.path.join(uploads_dir, out_filename)
        with open(out_path, "wb") as f:
            f.write(enhanced_bytes)

        processed_image_url = f"http://127.0.0.1:8000/uploads/products/{out_filename}"
        print(f"[REMBG] Background removed & enhanced image saved to: {out_filename}")
    except Exception as exc:
        print(f"[REMBG] Background removal or enhancement fallback: {exc}")

    # -------------------------------------------------------------
    # 3. Multimodal Vision & Bilingual Copywriting via Gemini 2.5 Flash
    # -------------------------------------------------------------
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            prompt = f"""You are an authentic Indian artisan handicraft catalog expert.
Analyze the provided product image and artisan voice notes.
Artisan voice notes / spoken details: {transcribed_text or 'None provided'}

Generate a complete, high-conversion e-commerce marketplace listing for this handcrafted piece.
Respond STRICTLY with a valid JSON object matching this schema:
{{
  "product_name": "Clear, appealing marketplace product title (e.g. Handcrafted Terracotta Water Pot)",
  "description_en": "Rich, authentic 2-3 paragraph English story describing the craftsmanship, material, utility, and cultural charm of the item visible in the photo.",
  "description_hi": "2-3 पैराग्राफ का सुंदर और प्रामाणिक हिंदी विवरण जो इस हस्तनिर्मित वस्तु की कारीगरी, बनावट और सांस्कृतिक सुंदरता का वर्णन करता है।",
  "category": "Marketplace category (e.g. Pottery & Ceramics, Handloom & Textiles, Woodcraft, Brass & Metalcraft, Jewelry, Home Decor)",
  "material": "Primary material identified in photo (e.g. Terracotta Clay, Pure Silk, Brass, Teak Wood)",
  "seo_title": "SEO Optimized Product Title | Authentic Indian Handicrafts",
  "seo_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"]
}}
"""
            part = types.Part.from_bytes(data=processed_image_bytes, mime_type=image_mime)
            models_to_try = [
                os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
                "gemini-3.6-flash",
                "gemini-3.5-flash-lite",
                "gemini-flash-latest",
                "gemini-3.7-flash",
                "gemini-2.5-flash",
            ]
            seen = set()
            models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

            response = None
            last_err = None
            for model_to_use in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_to_use,
                        contents=[part, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.3,
                        ),
                    )
                    if response and getattr(response, "text", None):
                        print(f"[GEMINI] Successfully generated listing with model: {model_to_use}")
                        break
                except Exception as e:
                    last_err = e
                    print(f"[GEMINI] Model {model_to_use} failed ({e}), trying next available model...")
                    continue

            if response is None or not getattr(response, "text", None):
                raise RuntimeError(f"All Gemini models exhausted: {last_err}")

            raw_text = getattr(response, "text", "") or ""
            if "```" in raw_text:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                if match:
                    raw_text = match.group(1)
            parsed = json.loads(raw_text.strip())

            return {
                "product_name": parsed.get("product_name", "Handcrafted Artisan Product"),
                "description_en": parsed.get("description_en", "Authentic handcrafted piece made with traditional artistry."),
                "description_hi": parsed.get("description_hi", "पारंपरिक भारतीय कारीगरी से निर्मित प्रामाणिक हस्तशिल्प।"),
                "category": parsed.get("category", "Handicrafts"),
                "material": parsed.get("material", "Artisanal Material"),
                "seo_title": parsed.get("seo_title", f"{parsed.get('product_name', 'Handcrafted Product')} | Indian Crafts"),
                "seo_keywords": parsed.get("seo_keywords", ["handcrafted", "artisan", "traditional", "indian crafts"]),
                "transcription": transcribed_text,
                "translated_text": parsed.get("description_en", "")[:120] if transcribed_text else None,
                "processed_image_url": processed_image_url,
            }
        except Exception as exc:
            print(f"[AI_SERVICE] Gemini multimodal generation failed, using rule-based fallback: {exc}")

    # Deterministic rule-based fallback
    notes = (transcribed_text or "").lower()
    mat = "Terracotta Clay" if "clay" in notes or "terracotta" in notes else ("Brass" if "brass" in notes else "Natural Wood")
    cat = "Pottery & Ceramics" if "clay" in notes else ("Brass & Metalcraft" if "brass" in notes else "Home Decor")
    title = f"Handcrafted {mat} Artisan Piece"

    return {
        "product_name": title,
        "description_en": f"This exquisite {title.lower()} is handcrafted with authentic artisanal techniques, reflecting the rich heritage of traditional Indian craftsmanship.",
        "description_hi": f"यह सुंदर {title} पारंपरिक भारतीय कारीगरों द्वारा हस्तनिर्मित है, जो उच्च गुणवत्ता और सांस्कृतिक विरासत को दर्शाता है।",
        "category": cat,
        "material": mat,
        "seo_title": f"{title} | Authentic Indian Handicraft",
        "seo_keywords": ["handcrafted", "artisan", "traditional crafts", "indian heritage"],
        "transcription": transcribed_text,
        "translated_text": transcribed_text,
        "processed_image_url": processed_image_url,
    }



class PublishProductRequest(BaseModel):
    image_url: Optional[str] = None
    description_hi: Optional[str] = None
    description_en: Optional[str] = None
    price: float = 0.0
    price_reason: Optional[str] = None
    artisan_id: Optional[str] = "default"


CATALOG_STORAGE: list = []


@router.post("/products")
@router.post("/ai/products")
async def publish_product(payload: PublishProductRequest):
    """
    Person 3 Contract endpoint per API_CONTRACT.md section 2.
    Accepts:
        image_url: str
        description_hi: str
        description_en: str
        price: number
        price_reason: str
    Returns 200:
        {"id": "abc123"}
    """
    product_id = f"prod_{uuid.uuid4().hex[:8]}"
    item = {
        "id": product_id,
        "image_url": payload.image_url or "",
        "description_hi": payload.description_hi or "",
        "description_en": payload.description_en or "",
        "price": payload.price,
        "price_reason": payload.price_reason or "",
        "artisan_id": payload.artisan_id or "default",
    }
    CATALOG_STORAGE.append(item)
    return {"id": product_id}


@router.get("/products")
@router.get("/ai/products")
async def get_catalog(artisan_id: Optional[str] = None):
    """
    Person 3 Contract endpoint per API_CONTRACT.md section 3.
    Returns 200:
        List of product objects matching the contract schema.
    """
    if artisan_id:
        return [p for p in CATALOG_STORAGE if p.get("artisan_id") == artisan_id]
    return CATALOG_STORAGE

