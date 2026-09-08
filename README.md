# KarigarConnect — AI-Powered Artisan Market Linkage Platform

> **Smart India Hackathon (SIH) Prototype — Round 2**

KarigarConnect bridges traditional Indian artisans with wholesale B2B buyers using AI-driven product cataloging, smart pricing, and automated market linkage.

---

## 🏗 Architecture

```
┌─────────────────────────┐
│   Flutter Mobile App    │
│  (Android / iOS / Web)  │
└───────────┬─────────────┘
            │ HTTPS (REST)
            ▼
┌─────────────────────────┐
│    FastAPI Backend       │
│    (Python 3.12)        │
└───┬───────┬─────────┬───┘
    │       │         │
    ▼       ▼         ▼
┌──────┐ ┌─────┐ ┌────────┐
│ Post │ │ AI  │ │Firebase│
│ greSQL│ │Svc  │ │ Auth   │
└──────┘ └─────┘ └────────┘
```

---

## 🚀 Quick Start

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Frontend (Flutter)
```bash
# Ensure Flutter SDK is on PATH
flutter pub get
flutter run                         # Android/iOS
flutter run -d web-server --web-port=3000  # Web (for demo)
```
- Web App: http://localhost:3000

### Permissions (real device)
**Android** — `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```
**iOS** — `ios/Runner/Info.plist`:
```xml
<key>NSCameraUsageDescription</key>
<string>Used to photograph products</string>
<key>NSMicrophoneUsageDescription</key>
<string>Used to record product descriptions</string>
```

---

## 📱 Frontend Screens

| Screen | Purpose |
|--------|---------|
| **Language Select** | Choose English or Hindi — the entire app switches language dynamically |
| **Login** | Phone + OTP (mock for hackathon — any 4-digit code works) |
| **Home** | Dashboard with 4-tab navigation: Shop · Buyers · Deals · Market |
| **Add Product** | 3-step wizard: Photo → Voice Description → Raw Material Cost |
| **Processing** | Animated interstitial while the AI pipeline runs |
| **Preview** | Shows AI output: transcription, translation, description, suggested price |
| **Catalog** | Create digital collections, group products, publish to marketplace |
| **Buyers** | Browse 8+ wholesale buyers, view AI match scores, send proposals |
| **Enquiries** | Track B2B deals (Pending/Contacted/Accepted/Rejected), respond to buyers |
| **Marketplace** | Public feed of all published products and collections |
| **Notifications** | In-app alerts with unread badge count |

---

## ⚙️ Backend API Endpoints

### Products (`/api/v1/products`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create a new draft product |
| `GET` | `/` | List artisan's own products |
| `GET` | `/{id}` | Get product details |
| `PUT` | `/{id}` | Update product |
| `DELETE` | `/{id}` | Delete product |
| `POST` | `/{id}/publish` | Toggle marketplace visibility |
| `POST` | `/{id}/images` | Upload product image |
| `GET` | `/{id}/images` | Get product images |
| `DELETE` | `/{id}/images/{image_id}` | Delete an image |
| `POST` | `/{id}/audio` | Upload voice recording |
| `GET` | `/{id}/audio` | Get audio recordings |
| `GET` | `/{id}/status` | Get processing status |
| `POST` | `/{id}/process` | Trigger full AI pipeline |
| `POST` | `/{id}/pricing` | Generate AI pricing |
| `GET` | `/{id}/pricing` | Get current price |
| `GET` | `/{id}/pricing/history` | Get pricing history |
| `GET` | `/{id}/buyers` | Get AI-matched wholesale buyers |
| `GET` | `/{id}/enquiries` | Get enquiries for this product |

### Buyers (`/api/v1/buyers`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all buyers (filter by category/location) |
| `GET` | `/{id}` | Get buyer details |
| `POST` | `/{id}/enquiries` | Send wholesale proposal to buyer |

### Enquiries (`/api/v1/enquiries`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/{id}` | Get enquiry details |
| `PUT` | `/{id}` | Update deal status + artisan response |

### Catalogs (`/api/v1/catalogs`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create new collection |
| `GET` | `/` | List artisan's catalogs |
| `GET` | `/{id}` | Get catalog details |
| `PUT` | `/{id}` | Update catalog |
| `DELETE` | `/{id}` | Delete catalog |
| `POST` | `/{id}/publish` | Publish to marketplace |
| `POST` | `/{id}/products/{pid}` | Add product to catalog |
| `DELETE` | `/{id}/products/{pid}` | Remove product from catalog |

### Marketplace (`/api/v1/marketplace`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/products` | Public feed of published products |
| `GET` | `/catalogs` | Public feed of published collections |

### Notifications (`/api/v1/notifications`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List notifications |
| `GET` | `/unread-count` | Get unread count (for badge) |
| `PUT` | `/{id}/read` | Mark one as read |
| `PUT` | `/read-all` | Mark all as read |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Backend health check |
| `GET` | `/health/db` | Database connectivity check |
| `GET` | `/version` | API version info |

### Users (`/api/v1/users`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/me` | Get current user profile |
| `PUT` | `/me` | Update user profile |

---

## 🗄 Database Models (PostgreSQL + SQLAlchemy)

| Model | Key Fields |
|-------|------------|
| `User` | id, firebase_uid, phone, name, role |
| `Product` | id, user_id, name, description_hi, description_en, price, status, is_published |
| `ProductImage` | id, product_id, url, cloudinary_id |
| `ProductAudio` | id, product_id, url, transcription, translation |
| `Price` | id, product_id, suggested_price, reasoning, raw_material_cost |
| `Catalog` | id, user_id, title, description, status (draft/published) |
| `CatalogProduct` | catalog_id, product_id (many-to-many join) |
| `Buyer` | id, name, company, email, phone, location, category |
| `Enquiry` | id, buyer_id, product_id, message, status, artisan_response, responded_at |
| `Notification` | id, user_id, type, title, message, is_read |

---

## 🌐 Internationalization

The app supports **full bilingual UI** (English & Hindi):
- Language is selected on the first screen
- All UI strings are centralized in `lib/language.dart`
- The entire app rebuilds instantly when language changes
- No bilingual mixing — choosing English shows only English; choosing Hindi shows only Hindi

---

## 🎯 Hackathon Design Decisions

1. **Mock Authentication**: Any phone number + any 4-digit OTP works. Ensures the live demo never fails due to SMS delays or API limits.
2. **Synchronous AI Pipeline**: The `/process` endpoint runs synchronously (no Celery/Redis/Kafka). Simpler to demo, no background worker failures.
3. **Database Seeding**: 8 realistic B2B buyers are auto-seeded on startup so the matching algorithm and buyer directory have data immediately.
4. **No External Dependencies Required**: Cloudinary, Firebase, and AI services are all mocked. The app runs fully offline with just Python + PostgreSQL + Flutter.

---

## 📂 Project Structure

```
KarigarConnect/
├── lib/                          # Flutter frontend
│   ├── main.dart                 # Entry point
│   ├── theme.dart                # App theme (teal palette)
│   ├── language.dart             # Bilingual string maps + language provider
│   ├── config.dart               # API base URL config
│   ├── models/                   # Data models (Product, Buyer, Enquiry, etc.)
│   ├── screens/                  # All UI screens (11 screens)
│   ├── services/api_service.dart # HTTP client singleton
│   ├── widgets/                  # Reusable UI components
│   └── utils/                    # Page transitions, helpers
│
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py               # FastAPI app + CORS + startup
│   │   ├── config.py             # Environment configuration
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   ├── firebase.py           # Firebase Admin SDK integration
│   │   ├── seed.py               # Demo data seeder
│   │   ├── api/                  # Route handlers (products, buyers, etc.)
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── services/             # Business logic (AI, pricing, matching)
│   ├── alembic/                  # Database migrations
│   ├── tests/                    # Automated backend tests
│   ├── requirements.txt          # Python dependencies
│   ├── Procfile                  # Render/Railway deployment
│   └── Dockerfile                # Container deployment
│
└── pubspec.yaml                  # Flutter dependencies
```

---

## 👥 Team Roles

| Person | Responsibility |
|--------|---------------|
| **Person 1** | Flutter UI/UX, mobile app, camera/audio capture |
| **Person 2** | ML models, computer vision, speech-to-text, AI pricing |
| **Person 3** | FastAPI backend, PostgreSQL, APIs, marketplace, buyer matching |
