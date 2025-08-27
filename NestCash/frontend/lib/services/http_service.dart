import 'package:http/http.dart' as http;
import 'auth_service.dart';

class HttpService {
  static final AuthService _authService = AuthService();
  
  static Future<http.Response> authenticatedRequest({
    required String method,
    required String url,
    Map<String, String>? headers,
    Object? body,
  }) async {
    String? token = await _authService.getToken();
    
    Map<String, String> requestHeaders = {
      'Content-Type': 'application/json',
      ...?headers,
    };
    
    if (token != null) {
      requestHeaders['Authorization'] = 'Bearer $token';
    }
    
    http.Response response;
    
    switch (method.toUpperCase()) {
      case 'GET':
        response = await http.get(Uri.parse(url), headers: requestHeaders);
        break;
      case 'POST':
        response = await http.post(Uri.parse(url), headers: requestHeaders, body: body);
        break;
      case 'PUT':
        response = await http.put(Uri.parse(url), headers: requestHeaders, body: body);
        break;
      default:
        throw Exception('Unsupported HTTP method: $method');
    }
    
    // Ha 401-et kapunk, próbáljuk meg frissíteni a tokent
    if (response.statusCode == 401) {
      final refreshSuccess = await _authService.refreshToken();
      
      if (refreshSuccess) {
        // Újra próbáljuk a kérést az új tokennel
        token = await _authService.getToken();
        requestHeaders['Authorization'] = 'Bearer $token';
        
        switch (method.toUpperCase()) {
          case 'GET':
            response = await http.get(Uri.parse(url), headers: requestHeaders);
            break;
          case 'POST':
            response = await http.post(Uri.parse(url), headers: requestHeaders, body: body);
            break;
          case 'PUT':
            response = await http.put(Uri.parse(url), headers: requestHeaders, body: body);
            break;
        }
      }
    }
    
    return response;
  }
}