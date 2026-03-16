class AppConstants {
  // Set this to true to use localhost, false for production (Render)
  static const bool useLocalServer = true;

  static const String _prodUrl = "https://other-projects-79dx.onrender.com";
  static const String _localUrl = "http://10.0.2.2:3000"; // Updated for Android Emulator

  static String get serverUrl => useLocalServer ? _localUrl : _prodUrl;
}
