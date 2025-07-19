import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'login_screen.dart';
import '/main.dart';

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

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
  final token = await _authService.getToken();
  debugPrint('AuthWrapper: token? ${token != null}');

  if (token != null) {
    final username = await _authService.getCurrentUsername();
    debugPrint('AuthWrapper: /auth/me username = $username');

    setState(() {
      _isLoggedIn = username != null;
      _username = username;
    });
  } else {
    // Fontos: explicit töröljük a korábbi állapotot
    setState(() {
      _isLoggedIn = false;
      _username = null;
    });
  }

  setState(() {
    _isLoading = false;
  });
}


  @override
  Widget build(BuildContext context) {
    if (_isLoading) return Center(child: CircularProgressIndicator());
    return _isLoggedIn && _username != null
        ? MainScreen(username: _username!)
        : LoginScreen();
  }
}
