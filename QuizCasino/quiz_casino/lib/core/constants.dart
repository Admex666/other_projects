class AppConstants {
  // Set this to true to use localhost, false for production (Render)
  static const bool useLocalServer = false;

  static const String _prodUrl = "https://other-projects-79dx.onrender.com";
  static const String _localUrl = "http://localhost:3000";

  static String get serverUrl => useLocalServer ? _localUrl : _prodUrl;
}
