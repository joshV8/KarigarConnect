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
│    FastAPI Backend      │ ◄────► ┌─────────────────────────┐
│    (Python 3.12/3.13)   │        │   Artisan AI Service    │
└───┬───────┬─────────┬───┘        │  (FastAPI + ML Pipeline)│
    │       │         │            └─────────────────────────┘
    ▼       ▼         ▼
┌──────┐ ┌─────┐ ┌────────┐
│ Post │ │AI-  │ │Firebase│
│ greSQL│ │Svc  │ │ Auth   │
└──────┘ └─────┘ └────────┘
```

---

## 🚀 Quick Start

### 1. Backend Service (Person 3)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 2. AI Services (Person 2)
```bash
cd ai-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```
- Interactive AI Dashboard: http://localhost:9000/dashboard
- AI Service Docs: http://localhost:9000/docs

### 3. Frontend (Flutter — Person 1)
```bash
# Ensure Flutter SDK is on PATH
flutter pub get
flutter run                         # Android/iOS
flutter run -d web-server --web-port=3000  # Web (for demo)
```
- Web App: http://localhost:3000

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
| **Product Detail** | Inspect, edit AI descriptions/prices, delete listings |
| **Catalog** | Create digital collections, group products, publish to marketplace |
| **Buyers** | Browse wholesale buyers, view AI match scores, send proposals |
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
| `GET` | `/` | List all enquiries for the artisan |
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

## 👥 Team Roles & Responsibilities

| Person | Responsibility |
|--------|---------------|
| **Person 1** | Flutter UI/UX, mobile app, camera/audio capture, localization |
| **Person 2** | ML models, computer vision, background removal, speech-to-text, AI pricing (`ai-service/`) |
| **Person 3** | FastAPI backend, PostgreSQL, APIs, marketplace, buyer matching (`backend/`) |
