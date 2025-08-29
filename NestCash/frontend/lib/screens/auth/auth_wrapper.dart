// auth_wrapper.dart - Frissített verzió
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'login_screen.dart';
import '/main.dart';
import 'package:frontend/screens/loading_screen.dart';

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  _AuthWrapperState createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  final AuthService _authService = AuthService();
  bool _isLoading = true;
  bool _isLoggedIn = false;
  String? _username;
  String? _userId;

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    const minDisplayTime = Duration(seconds: 2);
    final startTime = DateTime.now();

    try {
      // Ellenőrizzük, hogy van-e token
      final token = await _authService.getToken();
      debugPrint('AuthWrapper: token exists? ${token != null}');

      if (token != null) {
        // Ellenőrizzük a token érvényességét
        debugPrint('AuthWrapper: Validating token...');
        final isValid = await _authService.isTokenValid();
        
        if (isValid) {
          // Token érvényes, töltjük be a felhasználói adatokat
          final username = await _authService.getCurrentUsername();
          final userId = await _authService.getUserId();
          
          debugPrint('AuthWrapper: Token valid, username = $username, userId = $userId');

          if (username != null && userId != null) {
            // Indítsuk el a session tracking-et
            await _authService.initializeSessionTracking();
            
            setState(() {
              _isLoggedIn = true;
              _username = username;
              _userId = userId;
            });
          } else {
            debugPrint('AuthWrapper: Missing username or userId, logging out');
            await _authService.logout();
            setState(() {
              _isLoggedIn = false;
              _username = null;
              _userId = null;
            });
          }
        } else {
          debugPrint('AuthWrapper: Token invalid or refresh failed');
          setState(() {
            _isLoggedIn = false;
            _username = null;
            _userId = null;
          });
        }
      } else {
        debugPrint('AuthWrapper: No token found');
        setState(() {
          _isLoggedIn = false;
          _username = null;
          _userId = null;
        });
      }
    } catch (e) {
      debugPrint('AuthWrapper error: $e');
      // Hiba esetén biztonsági okokból kijelentkeztetjük
      await _authService.logout();
      setState(() {
        _isLoggedIn = false;
        _username = null;
        _userId = null;
      });
    }

    // Minimum megjelenítési idő biztosítása
    final elapsedTime = DateTime.now().difference(startTime);
    if (elapsedTime < minDisplayTime) {
      final remainingTime = minDisplayTime - elapsedTime;
      await Future.delayed(remainingTime);
    }

    setState(() {
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const LoadingScreen(
        message: 'Alkalmazás betöltése...',
        showLogo: true,
      );
    } else {
      return _isLoggedIn && _username != null && _userId != null
          ? MainScreen(username: _username!, userId: _userId!)
          : const LoginScreen();
    }
  }
}