# KarigarConnect — Live Hackathon Demo Flow

This document details the exact 12-step sequence executed by the mobile app and backend during the live hackathon demonstration.

---

## 1. Authentication
* **Endpoint**: `GET /api/v1/users/me`
* **Method**: `GET`
* **Header**: `Authorization: Bearer <firebase_id_token>` (or `Bearer artisan_demo_1` in mock dev)
* **Purpose**: Resolves or auto-provisions the authenticated artisan profile.
* **Expected Result**: `200 OK` returning artisan name, phone, language preference, and location.

---

## 2. Product Draft Creation
* **Endpoint**: `POST /api/v1/products`
* **Method**: `POST`
* **Request**:
  ```json
  {
    "name": "Handmade Bamboo Lamp",
    "raw_material_cost": 150.0,
    "labour_cost": 75.0,
    "packaging_cost": 25.0,
    "category": "Home Decor",
    "material": "Bamboo"
  }
  ```
* **Purpose**: Records initial artisan input with status `"draft"`.
* **Expected Result**: `201 Created` returning generated `product_id`.

---

## 3. Product Photo Upload
* **Endpoint**: `POST /api/v1/products/{id}/images`
* **Method**: `POST` (Multipart form-data: `file` field)
* **Purpose**: Uploads craft photo to Cloudinary / static storage.
* **Expected Result**: `201 Created` returning CDN `original_url`.

---

## 4. Artisan Voice Recording Upload
* **Endpoint**: `POST /api/v1/products/{id}/audio`
* **Method**: `POST` (Multipart form-data: `file`, `language=hi`, `duration=5.5`)
* **Purpose**: Uploads spoken craft description (`.m4a`/`.wav`).
* **Expected Result**: `201 Created` returning `audio_url`.

---

## 5. Multimodal AI Processing & Listing Generation
* **Endpoint**: `POST /api/v1/products/{id}/process`
* **Method**: `POST`
* **Request**:
  ```json
  {
    "voice_text": "हाथ से बना हुआ सुंदर बांस का लैंप",
    "language": "hi"
  }
  ```
* **Purpose**: Identifies craft, executes speech-to-text, translates to English, produces dual-language descriptions, and computes fair pricing.
* **Expected Result**: `200 OK` with status `"processed"`, bilingual descriptions, transcription, and recommended price.

---

## 6. Price Recommendation Verification
* **Endpoint**: `GET /api/v1/products/{id}/pricing`
* **Method**: `GET`
* **Purpose**: Validates transparent cost breakdown (materials + labour + packaging + 20% margin).
* **Expected Result**: `200 OK` with `recommended_price`, `minimum_price`, and `maximum_price`.

---

## 7. Digital Catalog Creation & Publishing
* **Endpoint**: `POST /api/v1/catalogs`
* **Method**: `POST` (`{"title": "Eco Bamboo Collection", "description": "Export quality handwoven items"}`)
* **Endpoint**: `POST /api/v1/catalogs/{id}/products/{product_id}`
* **Method**: `POST`
* **Purpose**: Groups products into a sharable digital catalog.
* **Expected Result**: `200 OK` returning catalog with linked product.

---

## 8. B2B Wholesale Buyer Matching
* **Endpoint**: `GET /api/v1/products/{id}/buyers`
* **Method**: `GET`
* **Purpose**: Ranks prospective B2B wholesale buyers based on category, craft material, and target procurement budget.
* **Expected Result**: `200 OK` returning scored and sorted prospective buyers with alignment reasons.

---

## 9. Buyer Enquiry Submission
* **Endpoint**: `POST /api/v1/buyers/{buyer_id}/enquiries`
* **Method**: `POST`
* **Request**:
  ```json
  {
    "product_id": 1,
    "message": "We have 50 units ready for immediate wholesale dispatch."
  }
  ```
* **Purpose**: Connects the artisan with the buyer.
* **Expected Result**: `201 Created` returning enquiry record with status `"pending"`.

---

## 10. In-App Notification Delivery
* **Endpoint**: `GET /api/v1/notifications`
* **Method**: `GET`
* **Endpoint**: `GET /api/v1/notifications/unread-count`
* **Purpose**: Informs artisan of buyer interest (`"New Buyer Enquiry"`).
* **Expected Result**: `200 OK` returning unread notifications list and count.

---

## 11. Artisan Enquiry Response & Negotiation
* **Endpoint**: `PUT /api/v1/enquiries/{enquiry_id}`
* **Method**: `PUT`
* **Request**:
  ```json
  {
    "status": "contacted",
    "artisan_response": "Sample units have been dispatched to your procurement hub."
  }
  ```
* **Purpose**: Artisan negotiates and accepts/contacts the buyer.
* **Expected Result**: `200 OK` with status `"contacted"` and recorded `responded_at` timestamp.

---

## 12. Notification Read Confirmation
* **Endpoint**: `PUT /api/v1/notifications/read-all`
* **Method**: `PUT`
* **Purpose**: Clears badge counter once notifications are reviewed.
* **Expected Result**: `200 OK` updating unread count to `0`.
