/// Central place for backend integration settings.
///
/// See API_CONTRACT.md at the project root for the exact request/
/// response shapes ApiService expects.
class AppConfig {
  /// Toggle between mock data and the live FastAPI AI Service backend.
  /// Set to false to communicate with the real AI pipeline.
  static const bool useMockApi = false;

  /// Base URL of the live FastAPI AI Service backend.
  /// - Android Emulator: 'http://10.0.2.2:8000'
  /// - iOS Simulator / Flutter Web / Desktop: 'http://localhost:8000'
  /// - Physical Phone on same WiFi: 'http://<YOUR_COMPUTER_IP>:8000'
  /// - Cloud Deployment: 'https://artisan-api.onrender.com'
  static const String apiBaseUrl = 'http://10.0.2.2:8000';
}
