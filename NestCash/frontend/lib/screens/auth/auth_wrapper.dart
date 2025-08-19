import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'login_screen.dart';
import '/main.dart';
import 'package:frontend/screens/loading_screen.dart';

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key}); // + key

  @override
  _AuthWrapperState createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  final AuthService _authService = AuthService();
  bool _isLoading = true;
  bool _isLoggedIn = false;
  String? _username;
  String? _userId; // Győződj meg róla, hogy ez a sor megvan

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    // Minimum megjelenítési idő (pl. 2 másodperc)
    const minDisplayTime = Duration(seconds: 3);
    final startTime = DateTime.now();

    final token = await _authService.getToken();
    debugPrint('AuthWrapper: token? ${token != null}');

    if (token != null) {
      final username = await _authService.getCurrentUsername(); // Győződj meg róla, hogy ez a metódus létezik és működik
      final userId = await _authService.getUserId();     // Győződj meg róla, hogy ez a metódus létezik és működik
      debugPrint('AuthWrapper: username = $username, userId = $userId');

      setState(() {
        // Ellenőrizzük, hogy mind a felhasználónév, mind az ID megvan-e
        _isLoggedIn = username != null && userId != null;
        _username = username;
        _userId = userId;
      });
    } else {
      setState(() {
        _isLoggedIn = false;
        _username = null;
        _userId = null;
      });
    }

    // Ellenőrizzük, hogy eltelt-e a minimum idő
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
      // Itt a kulcs: ha be van jelentkezve, akkor MainScreen-re, különben LoginScreen-re
      return _isLoggedIn && _username != null && _userId != null
          ? MainScreen(username: _username!, userId: _userId!) // Itt adod át a MainScreen-nek
          : const LoginScreen();
    }
  }
}
