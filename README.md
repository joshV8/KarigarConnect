# KarigarConnect — Flutter MVP scaffold

Person 1's slice: mobile app + UX. This is a working skeleton with the
full user flow wired up end-to-end using a **mocked AI response**, so
you can demo the whole experience even if Person 2/3's real API isn't
ready by tomorrow.

## Get running

```bash
flutter create . --platforms=android,ios   # if you haven't already got native folders
flutter pub get
flutter run
```

If `flutter create .` complains the folder isn't empty, that's fine —
it just regenerates the missing `android/` and `ios/` folders around
your existing `lib/`.

## Permissions (add before you demo on a real device)

**Android** — `android/app/src/main/AndroidManifest.xml`, inside `<manifest>`:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

**iOS** — `ios/Runner/Info.plist`, inside the top-level `<dict>`:
```xml
<key>NSCameraUsageDescription</key>
<string>Used to photograph products</string>
<key>NSMicrophoneUsageDescription</key>
<string>Used to record product descriptions</string>
```

## What's real vs mocked

- **Real:** camera capture (`image_picker`), voice recording (`record`),
  full navigation flow, in-memory catalog.
- **Mocked:** `ApiService.processNewProduct()` fakes a 3-second AI
  delay and returns a canned Hindi/English description + a price
  computed from the raw material cost you entered. This is the one
  method to replace with a real `http.post` to Person 3's FastAPI
  endpoint — no screen code needs to change when you do.
- **Fake login:** any phone number + any 4-digit code gets you in.
  Swap for Firebase Auth post-hackathon.

## Structure

```
lib/
  main.dart                     entry point, routes to language select
  theme.dart                    colors, big-button styling
  models/product.dart           Product + ProductDraft
  services/api_service.dart     mocked AI call + in-memory catalog
  screens/
    language_select_screen.dart
    login_screen.dart
    home_screen.dart
    add_product_screen.dart     photo -> voice -> price, PageView
    processing_screen.dart
    preview_screen.dart
    catalog_screen.dart
```

## Next, if you have time

1. Wire `ApiService.processNewProduct` to the real endpoint once
   Person 3 has one — pass the photo file + audio file as multipart.
2. Add "retake photo" / "re-record" actions on the Preview screen.
3. Persist the catalog (currently wiped on app restart) — even
   `shared_preferences` with JSON would survive a demo restart.
