class ApiConfig {
  // Fejlesztési és production URL-ek
  static const String _devBaseUrl = 'http://10.0.2.2:8000';
  static const String _prodBaseUrl = 'https://other-projects-ofaj.onrender.com';
  
  // Automatikus környezet észlelés vagy manuális beállítás
  static const bool _isProduction = true; //bool.fromEnvironment('dart.vm.product');
  
  // Aktuális BASE URL
  static String get baseUrl => _isProduction ? _prodBaseUrl : _devBaseUrl;
  
  // API végpontok
  static String get apiUrl => '$baseUrl/api/v1';
}

// Alternatív megoldás környezeti változókkal
class ApiConfigEnv {
  static String get baseUrl {
    // Először próbáljuk meg környezeti változóból
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    
    // Ha nincs környezeti változó, akkor használjuk az alapértelmezett értékeket
    const bool isProduction = bool.fromEnvironment('dart.vm.product');
    return isProduction 
        ? 'https://your-render-app.onrender.com'
        : 'http://localhost:8000';
  }
}