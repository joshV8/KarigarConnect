# API Contract — Flutter ↔ Backend

This is what the Flutter app (Person 1) expects from Person 2's AI
pipeline and Person 3's backend. Building to this contract means
integration only ever touches `lib/services/api_service.dart` and
`lib/config.dart` — no screen code changes.

Until this is wired in, `AppConfig.useMockApi` (in `lib/config.dart`)
is `true` and the whole app runs on fake data, so Person 2 and
Person 3 can build and test their parts independently without
waiting on each other or on Person 1.

## Base URL

Set once in `lib/config.dart` → `AppConfig.apiBaseUrl`, provided by
Person 3 once the FastAPI server is deployed.

## 1. Process new product (Person 2's AI pipeline, via Person 3's FastAPI gateway)

```
POST {baseUrl}/products/process
Content-Type: multipart/form-data

Fields:
  photo: file (jpg/png)
  audio: file (m4a/wav) — voice description
  raw_material_cost: number
```

Response `200`:
```json
{
  "image_url": "https://.../enhanced.jpg",
  "description_hi": "हाथ से बनी पारंपरिक कलाकृति...",
  "description_en": "Handcrafted traditional piece...",
  "price": 850,
  "price_reason": "Cost ₹250 + labour + market rate for similar items"
}
```

## 2. Publish product (Person 3)

```
POST {baseUrl}/products
Content-Type: application/json
```
Body: same shape as the response above.

Response `200`: `{ "id": "abc123" }`

## 3. Fetch catalog (Person 3)

```
GET {baseUrl}/products?artisan_id=...
```

Response `200`: an array of the same product object shape, each with an `id`.

## 4. Auth (Person 3, Firebase Auth)

Flutter currently fakes phone/OTP login locally (any number, any
4-digit code). When Firebase Auth is ready, `LoginScreen` swaps its
local state for Firebase's phone-auth flow directly via the SDK —
no custom REST endpoint needed for this one.

## Notes

- Images are always referenced by URL (Cloudinary/S3), never sent
  back as raw bytes — Flutter displays them via a network image.
- Prices are numbers (INR), no currency symbol, no string formatting.
- `price_reason` is a short human-readable string — shown as-is under
  the price on the Preview screen.
