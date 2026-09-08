# KarigarConnect — Live Hackathon Demo Checklist

### 1. Before Demo Setup
* [ ] **FastAPI Backend Active**: `GET /health` returns `200 OK` (`"status": "ok"`).
* [ ] **Database Connected**: `GET /health/db` returns `200 OK` (`"database": "connected"`).
* [ ] **Interactive Documentation**: Swagger UI accessible at `/docs` and `/api/v1/docs`.
* [ ] **Demo Buyers Seeded**: Executed `python seed_demo_data.py` (8 verified fictional buyers in DB).
* [ ] **CORS Configured**: Mobile/Web client origins allowed via `ALLOWED_ORIGINS` or dev `*`.
* [ ] **Automated Test Suite Clean**: `pytest -v` runs with 100% pass rate.
* [ ] **Flutter Production URL**: Flutter `--dart-define=API_BASE_URL=https://...` verified against deployed instance.

---

### 2. During Live Demo Sequence
* [ ] **1. Authentication**: Login screen authenticates artisan smoothly.
* [ ] **2. Photo Capture**: Camera / gallery picture loaded with local preview.
* [ ] **3. Voice Description**: Speak Hindi/regional voice note with live waveform.
* [ ] **4. Cost Input**: Enter raw material, labour, and packaging costs.
* [ ] **5. AI Processing**: Animated processing screen with status transitions (`draft` ➔ `processing` ➔ `processed`).
* [ ] **6. Listing Generation**: Professional bilingual descriptions (Hindi + English) displayed.
* [ ] **7. Transparent Pricing**: Explainable pricing breakdown with margin calculation displayed.
* [ ] **8. Catalog Publishing**: Product published and preserved in digital catalog.
* [ ] **9. B2B Buyer Matching**: Scored prospective wholesale distributors displayed.
* [ ] **10. Wholesale Enquiry**: Send procurement message to top-matched buyer.
* [ ] **11. Notification Alert**: In-app notification received with unread counter.
* [ ] **12. Artisan Response**: Update enquiry status (`contacted`/`accepted`) and reply.

---

### 3. Backup Plan & Offline Resiliency

| Failure Scenario | Fallback Mechanism | Impact on Live Demo |
|------------------|--------------------|---------------------|
| **External AI Service Offline / Slow** | Set `AI_MODE=mock` in `.env` or environment | Zero downtime: Mock AI generates rich, contextual bilingual listings & transcriptions instantly. |
| **Cloudinary / Asset Storage Unavailable** | Local fallback storage `/uploads/products` & `/uploads/audio` | Zero interruption: FastAPI serves uploaded media locally via StaticFiles. |
| **Internet / WiFi Unstable** | Run backend locally on `http://localhost:8000` with local PostgreSQL / SQLite | Complete end-to-end demo functions 100% offline without external dependencies. |
| **Accidental Double Click** | `POST /process` rejects concurrent runs with `409 Conflict` | Protects database from race conditions. |
