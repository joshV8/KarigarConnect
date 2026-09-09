# KarigarConnect — AI Services Architecture & Specification

This document provides a comprehensive technical overview and API reference for the **Artisan AI Services** backend (Person 2's subsystem) in **KarigarConnect**.

The AI service empowers rural and traditional Indian artisans to digitize, price, describe, and market their handcrafted products effortlessly by processing photos and natural vernacular voice notes into studio-grade marketplace listings.

---

## 1. System Architecture & Tech Stack

The AI service is built on **FastAPI (Python 3.10+)** engineered for high throughput, asynchronous I/O, and seamless integration with state-of-the-art AI/ML models:

| Subsystem | Technology | Purpose |
|---|---|---|
| **Web Framework** | FastAPI + Uvicorn | Async REST API & OpenAPI auto-documentation |
| **Multimodal Vision** | Google Gemini 1.5 / 2.5 Flash | Craft identification, material extraction, visual attributes |
| **Generative Copywriting** | Google Gemini 1.5 Flash | Bilingual storytelling & SEO optimization |
| **Speech-to-Text** | OpenAI Whisper (`base` / `small`) | Vernacular voice note transcription |
| **Background Removal** | `rembg` (U^2-Net ONNX runtime) | Automated product isolation & clean cutout |
| **Image Enhancement** | Pillow (PIL) + OpenCV | Contrast, sharpness, brightness & white balance correction |
| **Data Validation** | Pydantic v2 | Strict schema typing, input validation, and serialization |
| **Testing** | Pytest (14 test suites) | Unit, integration, mocked AI, E2E, and security tests |

---

## 2. Directory Structure

The complete AI service resides under `ai-service/`:

```text
ai-service/
├── app/
│   ├── main.py                     # FastAPI application factory & router registration
│   ├── models/                     # Pydantic request & response schemas
│   │   ├── catalog.py              # Catalog orchestration schemas (/products/process)
│   │   ├── description.py          # Bilingual description generation schemas
│   │   ├── jobs.py                 # Async background job schemas
│   │   ├── pricing.py              # Fair pricing calculation schemas
│   │   ├── seo.py                  # SEO tags & metadata schemas
│   │   ├── speech.py               # Audio transcription schemas
│   │   └── translation.py          # Multilingual translation schemas
│   ├── routers/                    # FastAPI route handlers
│   │   ├── background.py           # /image/remove-background
│   │   ├── catalog.py              # /products/process, /products
│   │   ├── description.py          # /description/generate
│   │   ├── enhancement.py          # /image/enhance
│   │   ├── image.py                # /image/validate
│   │   ├── jobs.py                 # /jobs/submit, /jobs/{job_id}
│   │   ├── pricing.py              # /pricing/calculate
│   │   ├── seo.py                  # /seo/optimize
│   │   ├── speech.py               # /speech/transcribe
│   │   ├── translation.py          # /translation/translate
│   │   └── vision.py               # /vision/analyze
│   ├── services/                   # Core business logic & model inference
│   │   ├── background_service.py   # U^2-Net segmentation logic
│   │   ├── catalog_service.py      # End-to-end catalog pipeline orchestrator
│   │   ├── description_service.py  # Prompt engineering & description generation
│   │   ├── enhancement_service.py  # Image tuning & color correction
│   │   ├── image_service.py        # Blur detection & dimension validation
│   │   ├── job_service.py          # In-memory background task queue
│   │   ├── pricing_service.py      # Fair artisan pricing algorithm
│   │   ├── seo_service.py          # Keyword & tag generation
│   │   ├── speech_service.py       # Whisper speech recognition pipeline
│   │   ├── translation_service.py  # Indic language translation
│   │   └── vision_service.py       # Multimodal visual feature extraction
│   └── utils/                      # Shared utility functions
├── tests/                          # 14 Pytest automated test suites
├── .env.example                    # Template for environment configuration
├── .gitignore                      # Python/cache/secrets ignore rules
├── gen_voice.ps1                   # Sample TTS test audio generator
├── requirements.txt                # Python package dependencies
├── run_pipeline_test.py            # End-to-end integration test runner
└── test_dashboard.html             # Interactive HTML test dashboard
```

---

## 3. Comprehensive Service Catalog

### Service 1: Health & Liveness Service
- **Endpoint:** `GET /health`
- **Purpose:** Fast liveness probe for orchestrators (Docker, Kubernetes, Render) and mobile network reachability checks.
- **Response:**
  ```json
  {
    "status": "ok",
    "version": "1.0.0"
  }
  ```

---

### Service 2: Image Quality & Security Validation (Gate 2)
- **Endpoint:** `POST /image/validate`
- **Content-Type:** `multipart/form-data` (Field: `image`)
- **Purpose:** Verifies whether uploaded artisan product photos meet minimum marketplace quality standards before running expensive AI pipelines.
- **Checks Performed:**
  - **MIME & Format:** Validates JPEG, PNG, or WebP headers. Rejects corrupted files.
  - **Resolution & Aspect Ratio:** Enforces minimum 300x300 dimensions and flags extreme panoramas.
  - **Blur Detection:** Computes the Laplacian variance of the image. Low variance (< 100.0) flags blurry photos and instructs the artisan to retake the shot with better focus.
- **Sample Response:**
  ```json
  {
    "valid": true,
    "width": 1200,
    "height": 900,
    "format": "JPEG",
    "file_size_kb": 142.5,
    "blur_score": 284.12,
    "is_blurry": false,
    "issues": []
  }
  ```

---

### Service 3: AI Background Removal (Gate 3)
- **Endpoint:** `POST /image/remove-background`
- **Content-Type:** `multipart/form-data` (Field: `image`)
- **Purpose:** Automatically removes cluttered artisan workshop backgrounds (tools, uneven flooring, bedsheets) to isolate the product cleanly with an alpha transparency mask.
- **Model:** U^2-Net neural network via `rembg` with ONNX Runtime acceleration.
- **Output:** `image/png` with transparent background.

---

### Service 4: Studio Image Enhancement (Gate 4)
- **Endpoint:** `POST /image/enhance`
- **Content-Type:** `multipart/form-data` (Field: `image`)
- **Purpose:** Simulates professional studio lighting for photos taken in dimly lit village workshops.
- **Operations:**
  - Auto-contrast adjustment
  - Dynamic range and sharpness boost
  - Adaptive brightness & saturation calibration
  - Color balance normalization
- **Output:** `image/jpeg` enhanced image bytes.

---

### Service 5: Multimodal Product Vision Analysis (Gate 5)
- **Endpoint:** `POST /vision/analyze`
- **Content-Type:** `multipart/form-data` (Field: `image`)
- **Purpose:** Examines the visual product photo and identifies craft category, raw materials, primary colors, craft technique, and physical characteristics.
- **Model:** Google Gemini 1.5 Flash Multimodal Vision.
- **Sample Response:**
  ```json
  {
    "craft_type": "Blue Pottery",
    "material": "Quartz powder, glass, natural dye",
    "colors": ["Cobalt Blue", "Turquoise", "White"],
    "condition": "New / Handcrafted",
    "visible_features": [
      "Traditional floral arabesque motif",
      "Hand-glazed glossy ceramic finish",
      "Symmetrical flared rim"
    ],
    "confidence_score": 0.94
  }
  ```

---

### Service 6: Fair Artisan Pricing Engine (Gate 6)
- **Endpoint:** `POST /pricing/calculate`
- **Content-Type:** `application/json`
- **Purpose:** Protects artisans from exploitation and undervaluation by computing fair market prices based on raw material costs, skilled manual labor hours, craft tier, and market demand benchmarks.
- **Request Body:**
  ```json
  {
    "raw_material_cost": 350.0,
    "craft_type": "Blue Pottery",
    "estimated_hours": 4.5
  }
  ```
- **Sample Response:**
  ```json
  {
    "suggested_price": 950.0,
    "min_price": 850.0,
    "max_price": 1100.0,
    "labor_cost": 360.0,
    "margin_percentage": 25.0,
    "price_reason": "Cost ₹350 + skilled pottery labor (4.5 hrs) + fair artisan margin"
  }
  ```

---

### Service 7: Multilingual Indic Translation Service (Gate 7)
- **Endpoint:** `POST /translation/translate`
- **Content-Type:** `application/json`
- **Purpose:** Translates product titles, craft stories, and descriptions across Indian regional languages so local buyers and global markets can discover products seamlessly.
- **Supported Languages:** Hindi (`hi`), English (`en`), Bengali (`bn`), Tamil (`ta`), Telugu (`te`), Marathi (`mr`), Gujarati (`gu`), Kannada (`kn`), Malayalam (`ml`), Odia (`or`), Punjabi (`pa`).
- **Request Body:**
  ```json
  {
    "text": "हाथ से बनी जयपुरी नीली मिट्टी की फूलदान।",
    "source_language": "hi",
    "target_language": "en"
  }
  ```
- **Sample Response:**
  ```json
  {
    "translated_text": "Handcrafted Jaipuri blue pottery flower vase.",
    "source_language": "hi",
    "target_language": "en"
  }
  ```

---

### Service 8: Multilingual Speech-to-Text Service (Gate 8)
- **Endpoint:** `POST /speech/transcribe`
- **Content-Type:** `multipart/form-data` (Field: `audio`)
- **Purpose:** Many artisans are more comfortable speaking about their craft than typing. This service transcribes natural voice notes recorded on the mobile app into text with high accuracy.
- **Model:** OpenAI Whisper (optimized with fallback heuristics).
- **Sample Response:**
  ```json
  {
    "transcript": "यह फूलदान मैंने मुल्तानी मिट्टी और नीले रंग से तीन दिन में तैयार किया है।",
    "detected_language": "hi",
    "duration_seconds": 6.8
  }
  ```

---

### Service 9: SEO & Marketplace Discovery Optimization (Gate 9)
- **Endpoint:** `POST /seo/optimize`
- **Content-Type:** `application/json`
- **Purpose:** Generates high-ranking search keywords, categorical tags, meta descriptions, and search-engine optimized product titles to maximize catalog visibility across e-commerce platforms and ONDC.
- **Sample Response:**
  ```json
  {
    "seo_title": "Authentic Handcrafted Blue Pottery Flower Vase | Jaipur Artisan Craft",
    "tags": ["blue pottery", "jaipur handicraft", "ceramic vase", "traditional decor", "handmade pottery"],
    "category": "Home Decor > Vases & Planters",
    "target_audience": "Art collectors, eco-conscious home decorators, cultural gifting",
    "meta_description": "Exquisite handmade blue pottery vase crafted with natural mineral dyes by traditional Rajasthani artisans. Free shipping across India."
  }
  ```

---

### Service 10: Rich Bilingual Description Generator (Gate 10)
- **Endpoint:** `POST /description/generate`
- **Content-Type:** `application/json`
- **Purpose:** Synthesizes the artisan's voice transcript and visual attributes into compelling, culturally respectful product descriptions in both Hindi and English.
- **Sample Response:**
  ```json
  {
    "description_hi": "यह सुंदर नीली मिट्टी का फूलदान जयपुर के कुशल कारीगरों द्वारा पारंपरिक विधि से तैयार किया गया है। इसमें प्राकृतिक रंगों और जटिल पुष्प डिजाइनों का उपयोग किया गया है जो आपके घर को एक पारंपरिक आकर्षण प्रदान करते हैं।",
    "description_en": "This exquisite blue pottery vase is handcrafted by master artisans of Jaipur using time-honored techniques. Featuring natural mineral pigments and intricate floral motifs, it brings cultural elegance and artisan authenticity into any living space."
  }
  ```

---

### Service 11: Unified Catalog Orchestration Pipeline (Gate 11 & Mobile Contract)
- **Endpoint:** `POST /products/process`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `photo`: Product image file (`image/jpeg` or `image/png`)
  - `audio`: Optional voice note audio file (`audio/wav`, `audio/m4a`, `audio/mp3`)
  - `raw_material_cost`: Numeric float representing material cost in ₹ (INR)
- **Purpose:** The flagship unified endpoint consumed directly by the KarigarConnect mobile application. In a single call, it orchestrates:
  1. Image validation & enhancement
  2. Voice note transcription via Whisper
  3. Visual craft analysis via Gemini Vision
  4. Fair pricing calculation
  5. Bilingual Hindi and English description generation
  6. Returns a production-ready product listing
- **Response Shape (conforming to `API_CONTRACT.md`):**
  ```json
  {
    "id": "1725884920000",
    "image_url": "data:image/jpeg;base64,...",
    "description_hi": "हाथ से तैयार की गई पारंपरिक कलाकृति...",
    "description_en": "Handcrafted traditional artwork made with authentic materials...",
    "price": 850.0,
    "price_reason": "Cost ₹250 + skilled labor (3.5 hrs) + fair artisan margin"
  }
  ```

#### Additional Catalog Persistence Routes:
- `POST /products`: Persists a published product to the catalog database.
- `GET /products`: Retrieves all published products (optionally filtered by `?artisan_id=...`).

---

### Service 12: Asynchronous Job Processing Queue (Gate 12)
- **Endpoints:**
  - `POST /jobs/submit`: Submits an intensive AI pipeline task for background processing. Returns `{ "job_id": "...", "status": "queued" }`.
  - `GET /jobs/{job_id}`: Polls task execution status (`queued` -> `processing` -> `completed` / `failed`) with progress percentage and resulting payload.

---

## 4. Mobile App Integration (KarigarConnect)

The Flutter mobile app (`lib/`) interacts directly with these AI services through clean, abstracted service classes:

1. **`lib/config.dart` (`AppConfig`):**
   - Contains `apiBaseUrl` (`http://10.0.2.2:8000` for Android emulator, `http://localhost:8000` for iOS/Web, or cloud URL).
   - Flag `useMockApi`: set to `false` to communicate with the live FastAPI service.
2. **`lib/services/api_service.dart` (`ApiService`):**
   - `processNewProduct(ProductDraft draft)`: Sends multipart request to `POST /products/process` and decodes the real AI response.
   - `publish(Product product)`: Synchronizes newly confirmed products to `POST /products`.
   - `fetchCatalog()`: Loads server-persisted artisan products via `GET /products`.
3. **`lib/widgets/safe_image.dart` (`SafeImage`):**
   - Intelligently renders data URIs (`data:image/...;base64,...`), remote URLs (`Image.network`), or local files (`Image.file`).
4. **`lib/screens/catalog_screen.dart` (`CatalogScreen`):**
   - Auto-refreshes and queries live catalog items on view mount and swipe-to-refresh.

---

## 5. Verification & Testing Suite

The repository includes a comprehensive 14-suite automated test suite covering all gates and edge cases:

```bash
cd ai-service
pytest -v
```

### Included Test Modules:
1. `tests/test_health.py` — Health probe validation
2. `tests/test_image_validation.py` — Blur, corrupt file, and aspect ratio checks
3. `tests/test_background_removal.py` — U^2-Net alpha mask and PNG generation
4. `tests/test_image_enhancement.py` — Studio color and contrast boost
5. `tests/test_product_vision.py` — Gemini visual attribute extraction
6. `tests/test_pricing.py` — Cost calculation and margin validation
7. `tests/test_translation.py` — Multilingual Indic translation
8. `tests/test_speech_to_text.py` — Whisper voice note transcription
9. `tests/test_seo.py` — SEO keyword and meta generation
10. `tests/test_description.py` — Bilingual storytelling synthesis
11. `tests/test_catalog_orchestration.py` — End-to-end `/products/process` pipeline
12. `tests/test_async_jobs.py` — Background job submission and status polling
13. `tests/test_integration_e2e.py` — Cross-service workflow integration
14. `tests/test_security_production.py` — Payload limits, CORS, and sanitization

### Interactive Tools:
- **`run_pipeline_test.py`:** Runs a complete end-to-end test against a live or auto-started uvicorn server.
  ```bash
  python run_pipeline_test.py --start-server
  ```
- **`test_dashboard.html`:** Beautiful browser-based test workbench for testing image upload, background removal, pricing, and description generation interactively.

---

## 6. Quick Start & Execution

### Prerequisites
- Python 3.10 or higher
- (Optional) Google Gemini API Key for online generative AI features

### Setup
```bash
# 1. Navigate to the AI service directory
cd ai-service

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and insert your GEMINI_API_KEY if testing online models

# 5. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, interactive Swagger API documentation is available at:
👉 **`http://localhost:8000/docs`**
