/// Central configuration for the Artisan Flutter App.
/// Supports runtime switching and build-time environment variable injection:
///
/// Build for Production:
/// `flutter build web --dart-define=API_BASE_URL=https://your-artisan-api.onrender.com`
///
/// Run locally against local FastAPI backend:
/// `flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000`
class AppConfig {
  /// When true, simulates backend responses with local mock data.
  /// When false, sends real HTTP requests to the FastAPI backend.
  static const bool useMockApi = false;

  /// FastAPI Backend base URL.
  /// Configurable via `--dart-define=API_BASE_URL=https://...` or defaults to local dev server.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  /// Default bearer token for authenticated requests (mock artisan ID or Firebase ID token)
  static String authToken = 'artisan_demo_user';
}
