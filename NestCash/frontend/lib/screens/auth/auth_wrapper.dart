// auth_wrapper.dart - Frissített verzió
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'login_screen.dart';
import '/main.dart';
import 'package:frontend/screens/loading_screen.dart';
import 'package:frontend/services/nestcash_analytics_service.dart';

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
      print('🔍 AuthWrapper: Starting auth check...');
      
      final token = await _authService.getToken();
      debugPrint('AuthWrapper: token exists? ${token != null}');

      if (token != null && token.isNotEmpty) {
        debugPrint('AuthWrapper: Validating token...');
        
        bool isValid = false;
        try {
          isValid = await _authService.isTokenValid();
          
          // Token validation analytics
          await NestCashAnalyticsService.trackAuthAction(
            'token_validation',
            success: isValid,
          );
          
        } catch (e) {
          await NestCashAnalyticsService.trackAuthError(
            authOperation: 'token_validation',
            error: e,
            stackTrace: StackTrace.current,
          );
          isValid = false;
        }
        
        if (isValid) {
          try {
            final username = await _authService.getCurrentUsername();
            final userId = await _authService.getUserId();
            
            if (username != null && username.isNotEmpty && 
                userId != null && userId.isNotEmpty) {
              
              // User initialization analytics
              await NestCashAnalyticsService.initializeUser(
                userId: userId,
                username: username,
              );
              
              try {
                await _authService.initializeSessionTracking();
              } catch (e) {
                await NestCashAnalyticsService.trackError(
                  error: e,
                  context: 'session_tracking_initialization',
                  screenName: 'auth_wrapper',
                );
              }
              
              setState(() {
                _isLoggedIn = true;
                _username = username;
                _userId = userId;
              });
            } else {
              await NestCashAnalyticsService.trackAuthAction(
                'missing_user_data',
                success: false,
                errorMessage: 'Missing username or userId',
              );
              await _authService.logout();
              setState(() {
                _isLoggedIn = false;
                _username = null;
                _userId = null;
              });
            }
          } catch (e) {
            await NestCashAnalyticsService.trackAuthError(
              authOperation: 'get_user_data',
              error: e,
              stackTrace: StackTrace.current,
            );
            await _authService.logout();
            setState(() {
              _isLoggedIn = false;
              _username = null;
              _userId = null;
            });
          }
        } else {
          debugPrint('AuthWrapper: Token invalid or refresh failed');
          // Tisztítsuk meg az érvénytelen tokeneket
          await _authService.logout();
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
      await NestCashAnalyticsService.trackError(
        error: e,
        context: 'auth_check_critical_failure',
        screenName: 'auth_wrapper',
        fatal: true,
      );
      // Hiba esetén biztonsági okokból kijelentkeztetjük
      try {
        await _authService.logout();
      } catch (logoutError) {
        debugPrint('AuthWrapper: Logout also failed: $logoutError');
      }
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