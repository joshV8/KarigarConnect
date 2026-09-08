# AI Service API Contract — Person 2 (AI Pipeline) ↔ Person 3 (Backend)

This document specifies the exact contract between **Person 3's FastAPI Backend** and **Person 2's AI Microservice**.

---

## Architecture Flow

```
Flutter Mobile / Web App
        │
        ▼ (POST /products/{id}/process)
FastAPI Backend (Person 3)
        │
        ▼ (POST {AI_SERVICE_URL}/process)
AI Microservice (Person 2 - LLM / Multimodal / Vision)
        │
        ▼ (Returns JSON AI Catalog Metadata)
FastAPI Backend (Validates & Persists in PostgreSQL)
        │
        ▼
Flutter App (Displays AI-Generated Preview)
```

---

## Endpoint Specification

### `POST /process`

- **URL**: `{AI_SERVICE_URL}/process` (e.g. `http://localhost:9000/process`)
- **Headers**:
  - `Content-Type: application/json`

---

## 1. Request Payload (Sent by Person 3's Backend)

```json
{
  "product_id": 1,
  "image_url": "https://res.cloudinary.com/demo/image/upload/artisan/products/prod_1_a1b2c3d4.jpg",
  "voice_text": "ही बांबूची हाताने बनवलेली टोपली आहे, टिकाऊ आणि सुंदर",
  "language": "mr",
  "raw_material_cost": 300.0,
  "labour_cost": 250.0,
  "packaging_cost": 50.0
}
```

### Request Fields:

| Field Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `product_id` | `integer` | **Yes** | Catalog identifier for tracing |
| `image_url` | `string` | No | Cloudinary / CDN URL of the product photograph |
| `voice_text` | `string` | No | Artisan's raw speech transcript (if speech-to-text was used) |
| `language` | `string` | No | Artisan's input language code (e.g. `hi`, `mr`, `gu`, `ta`, `en`) |
| `raw_material_cost` | `number` | No | Raw material cost in INR |
| `labour_cost` | `number` | No | Artisan labour cost in INR |
| `packaging_cost` | `number` | No | Packaging cost in INR |

---

## 2. Response Payload (Expected from Person 2's AI Service)

Status: `200 OK`
Content-Type: `application/json`

```json
{
  "product_name": "Handwoven Bamboo Storage Basket",
  "description_en": "A beautifully handcrafted bamboo storage basket woven by master artisans using organic bamboo. Features intricate patterns and durable construction suitable for modern home decor.",
  "description_hi": "कुशल कारीगरों द्वारा जैविक बांस से बुनी गई सुंदर हस्तनिर्मित स्टोरेज टोकरी। आधुनिक घर की सजावट और भंडारण के लिए उपयुक्त और टिकाऊ।",
  "category": "Home Decor",
  "material": "Bamboo",
  "seo_title": "Eco-Friendly Handcrafted Bamboo Basket | Handwoven Storage Organizer",
  "seo_keywords": [
    "bamboo basket",
    "handcrafted home decor",
    "eco-friendly organizer",
    "indian artisan craft",
    "sustainable storage"
  ]
}
```

### Response Fields:

| Field Name | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `product_name` | `string` | **Yes** | Refined, market-ready title for e-commerce listings |
| `description_en` | `string` | **Yes** | Compelling, high-converting English product copy |
| `description_hi` | `string` | **Yes** | Accurate, natural Hindi product description |
| `category` | `string` | **Yes** | Standard marketplace category (e.g., `Home Decor`, `Textiles`, `Pottery`, `Jewelry`) |
| `material` | `string` | **Yes** | Primary craft material (e.g., `Bamboo`, `Brass`, `Terracotta`, `Cotton`) |
| `seo_title` | `string` | No | Search-engine-optimized title |
| `seo_keywords` | `array[string]`| No | Search tags for catalog indexing |

---

## 3. Error Handling & Status Codes

If Person 2's AI service encounters an error, return standard HTTP status codes with a JSON error body:

```json
{
  "detail": "Failed to process image: model timeout"
}
```

- `400 Bad Request`: Missing essential fields or invalid language code.
- `422 Unprocessable Entity`: Input payload fails schema validation.
- `500 Internal Server Error`: LLM / Vision model execution failure.

### Backend Fallback Behavior:
- When the AI service fails or times out, Person 3's backend updates the product status to `processing_failed` in PostgreSQL and returns an appropriate `502 Bad Gateway` / `504 Gateway Timeout` to the client.

---

## 4. Separation of Responsibilities

### Person 2 (AI Pipeline Engineer):
- Host/deploy the `/process` API endpoint.
- Visual reasoning and image understanding from `image_url`.
- Speech-to-text / Audio transcription processing.
- Translation and natural language generation in English and Hindi.
- Category classification and material extraction.
- SEO keyword generation.

### Person 3 (Backend Engineer):
- Managing client REST endpoints and Flutter integration.
- Database persistence (PostgreSQL).
- Image uploads & CDN hosting (Cloudinary).
- Invoking Person 2's service with structured requests.
- Strict Pydantic response validation and error containment.
- Managing lifecycle status (`draft` $\rightarrow$ `processing` $\rightarrow$ `processed` / `processing_failed`).
