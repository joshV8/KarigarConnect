/// Central place for backend integration settings. Person 3 sets
/// [apiBaseUrl] once the FastAPI server is deployed; until then,
/// [useMockApi] keeps the whole app working against ApiService's
/// mock data so mobile work isn't blocked on backend readiness.
///
/// See API_CONTRACT.md at the project root for the exact request/
/// response shapes ApiService expects once useMockApi is false.
class AppConfig {
  static const bool useMockApi = true;

  /// Replace with Person 3's deployed FastAPI base URL, e.g.
  /// 'https://artisan-api.onrender.com'
  static const String apiBaseUrl = 'https://REPLACE_WITH_BACKEND_URL';
}
