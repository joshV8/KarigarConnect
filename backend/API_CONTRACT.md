# KarigarConnect / Artisan App — Final API Contract

All endpoints support `/api/v1` prefix and root routing. Protected endpoints require `Authorization: Bearer <token>`.

---

## 1. System & Health

### `GET /health`
- **Auth**: None (Public)
- **Response** `200 OK`:
  ```json
  {
    "status": "ok",
    "service": "artisan-api",
    "version": "1.0.0",
    "environment": "production"
  }
  ```

### `GET /health/db`
- **Auth**: None (Public)
- **Response** `200 OK`:
  ```json
  {
    "status": "ok",
    "service": "artisan-api",
    "database": "connected"
  }
  ```
- **Error** `503 Service Unavailable`: `{"status": "unhealthy", "service": "artisan-api", "database": "disconnected"}`

---

## 2. Authentication & User Profile

### `GET /api/v1/users/me`
- **Auth**: Bearer Token required
- **Response** `200 OK`:
  ```json
  {
    "id": 1,
    "firebase_uid": "user_uid_123",
    "name": "Ramesh Kumar",
    "phone": "+91-98765-43210",
    "language": "hi",
    "location": "Jaipur, Rajasthan",
    "created_at": "2026-09-08T10:00:00Z"
  }
  ```

### `PUT /api/v1/users/me`
- **Auth**: Bearer Token required
- **Request Body**:
  ```json
  {
    "name": "Ramesh Kumar",
    "language": "hi",
    "location": "Jaipur, Rajasthan"
  }
  ```
- **Response** `200 OK`: Updated user profile schema.

---

## 3. Products

### `POST /api/v1/products`
- **Auth**: Bearer Token required (Owner)
- **Request Body**:
  ```json
  {
    "name": "Terracotta Pot",
    "raw_material_cost": 150.0,
    "labour_cost": 60.0,
    "packaging_cost": 20.0,
    "category": "Pottery",
    "material": "Clay"
  }
  ```
- **Response** `201 Created`: Full product record (status: `draft`).

### `GET /api/v1/products`
- **Auth**: Bearer Token required
- **Response** `200 OK`: List of products owned by authenticated artisan.

### `GET /api/v1/products/{id}`
- **Auth**: Bearer Token required (Owner)
- **Response** `200 OK`: Complete product details including embedded images, audio recordings, pricing, and voice transcriptions.

### `GET /api/v1/products/{id}/status`
- **Auth**: Bearer Token required
- **Response** `200 OK`:
  ```json
  {
    "product_id": 1,
    "status": "processed"
  }
  ```

### `PUT /api/v1/products/{id}`
- **Auth**: Bearer Token required (Owner)
- **Response** `200 OK`: Updated product record.

### `DELETE /api/v1/products/{id}`
- **Auth**: Bearer Token required (Owner)
- **Response** `200 OK`: `{"status": "success", "message": "Product deleted successfully"}`.

---

## 4. Product Images

### `POST /api/v1/products/{id}/images`
- **Auth**: Bearer Token required (Owner)
- **Request**: Multipart Form Data with `file` (image/jpeg, image/png, image/webp)
- **Response** `201 Created`:
  ```json
  {
    "id": 1,
    "product_id": 1,
    "original_url": "https://res.cloudinary.com/.../image.jpg",
    "thumbnail_url": null,
    "is_primary": true,
    "created_at": "2026-09-08T10:00:00Z"
  }
  ```

### `GET /api/v1/products/{id}/images`
- **Auth**: Bearer Token required
- **Response** `200 OK`: List of images attached to product.

---

## 5. Product Audio (Voice Recording)

### `POST /api/v1/products/{id}/audio`
- **Auth**: Bearer Token required (Owner)
- **Request**: Multipart Form Data with `file` (`.m4a`, `.wav`, `.aac`, `.mp3`), `language` (`hi`), `duration` (`5.5`)
- **Response** `201 Created`:
  ```json
  {
    "id": 1,
    "product_id": 1,
    "audio_url": "https://res.cloudinary.com/.../voice.m4a",
    "language": "hi",
    "duration": 5.5,
    "created_at": "2026-09-08T10:00:00Z"
  }
  ```

### `GET /api/v1/products/{id}/audio`
- **Auth**: Bearer Token required
- **Response** `200 OK`: List of audio voice recordings attached to product.

---

## 6. AI Multimodal Processing Pipeline

### `POST /api/v1/products/{id}/process`
- **Auth**: Bearer Token required (Owner)
- **Request Body**:
  ```json
  {
    "voice_text": "हाथ से बना हुआ सुंदर मिट्टी का घड़ा",
    "language": "hi"
  }
  ```
- **Response** `200 OK`:
  ```json
  {
    "product": {
      "id": 1,
      "name": "Handcrafted Terracotta Pot",
      "description_hi": "पारंपरिक तकनीकों से बना सुंदर घड़ा...",
      "description_en": "A beautiful handcrafted terracotta pot...",
      "voice_transcription": "हाथ से बना हुआ सुंदर मिट्टी का घड़ा",
      "translated_voice_text": "A beautiful handcrafted terracotta pot",
      "status": "processed",
      "images": [...],
      "audio_recordings": [...]
    },
    "pricing": {
      "recommended_price": 276.0,
      "minimum_price": 235.0,
      "maximum_price": 345.0,
      "reason": "Calculated from materials (₹150) + labour (₹60) + packaging (₹20) with a 20% margin."
    }
  }
  ```

---

## 7. Pricing Engine

### `POST /api/v1/products/{id}/pricing`
- **Auth**: Bearer Token required (Owner)
- **Response** `201 Created`: Calculated price recommendation.

### `GET /api/v1/products/{id}/pricing`
- **Auth**: Bearer Token required
- **Response** `200 OK`: Latest price record.

### `GET /api/v1/products/{id}/pricing/history`
- **Auth**: Bearer Token required
- **Response** `200 OK`: Historical price computations.

---

## 8. Digital Catalogs

### `POST /api/v1/catalogs`
- **Auth**: Bearer Token required (Owner)
- **Request Body**: `{"title": "Jaipur Ceramics", "description": "Handmade pottery collection"}`
- **Response** `201 Created`: Catalog schema.

### `GET /api/v1/catalogs`
- **Auth**: Bearer Token required
- **Response** `200 OK`: List of catalogs owned by user.

### `POST /api/v1/catalogs/{id}/products/{product_id}`
- **Auth**: Bearer Token required (Verifies ownership of both catalog and product)
- **Response** `200 OK`: Catalog with updated product list.

---

## 9. B2B Buyers & Market Linkage

### `GET /api/v1/buyers`
- **Auth**: None (Public)
- **Query Params**: `category`, `location`
- **Response** `200 OK`: List of wholesale verified buyers with procurement requirements.

### `GET /api/v1/buyers/{id}`
- **Auth**: None (Public)
- **Response** `200 OK`: Buyer profile.

### `POST /api/v1/buyers/{id}/enquiries`
- **Auth**: Bearer Token required (Owner of product)
- **Request Body**:
  ```json
  {
    "product_id": 1,
    "message": "We have 50 units ready for wholesale dispatch."
  }
  ```
- **Response** `201 Created`: Enquiry record confirmation. Triggers in-app notification for the product owner.

---

## 10. Buyer Enquiries Tracking & Lifecycle

### `GET /api/v1/products/{id}/enquiries`
- **Auth**: Bearer Token required (Owner)
- **Response** `200 OK`: List of enquiries for the specified product.

### `GET /api/v1/enquiries/{enquiry_id}`
- **Auth**: Bearer Token required (Owner of associated product)
- **Response** `200 OK`: Single enquiry details.

### `PUT /api/v1/enquiries/{enquiry_id}`
- **Auth**: Bearer Token required (Owner of associated product)
- **Request Body**:
  ```json
  {
    "status": "contacted",
    "artisan_response": "We have dispatched sample units to your procurement office."
  }
  ```
- **Supported Statuses**: `pending`, `contacted`, `accepted`, `rejected`
- **Response** `200 OK`: Updated enquiry with server-timestamped `responded_at` and `updated_at`.

---

## 11. In-App Notifications

### `GET /api/v1/notifications`
- **Auth**: Bearer Token required
- **Query Params**: `unread_only` (`true`/`false`), `limit` (default: 20), `offset` (default: 0)
- **Response** `200 OK`:
  ```json
  {
    "notifications": [
      {
        "id": 1,
        "user_id": 1,
        "type": "new_enquiry",
        "title": "New Buyer Enquiry",
        "message": "FabIndia Wholesale is interested in your Handwoven Silk Saree.",
        "related_product_id": 1,
        "related_enquiry_id": 1,
        "is_read": false,
        "created_at": "2026-09-08T10:00:00Z"
      }
    ],
    "total": 1,
    "unread_count": 1
  }
  ```

### `GET /api/v1/notifications/unread-count`
- **Auth**: Bearer Token required
- **Response** `200 OK`:
  ```json
  {
    "count": 1
  }
  ```

### `PUT /api/v1/notifications/{id}/read`
- **Auth**: Bearer Token required (Owner)
- **Response** `200 OK`: Notification marked with `is_read = true`.

### `PUT /api/v1/notifications/read-all`
- **Auth**: Bearer Token required
- **Response** `200 OK`: `{"status": "success", "message": "Marked 3 notifications as read", "updated_count": 3}`.
