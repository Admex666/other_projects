import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../theme.dart';
import 'class_selection_screen.dart';
import 'explore_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLogin = true; // Toggle between Login and Register
  bool _isLoading = false;

  Future<void> _submit() async {
    setState(() => _isLoading = true);
    final auth = context.read<AuthService>();
    final username = _usernameController.text.trim();
    final password = _passwordController.text.trim();

    String? error;
    if (_isLogin) {
      error = await auth.login(username, password);
    } else {
      error = await auth.register(username, password);
    }

    setState(() => _isLoading = false);

    if (error == null) {
      // Success
      if (!mounted) return;
      // MainApp handles routing based on AuthService state
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error),
          backgroundColor: Colors.redAccent,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GeolixoTheme.background,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo placeholder
              const Icon(Icons.map_outlined, size: 80, color: GeolixoTheme.accent),
              const SizedBox(height: 16),
              Text(
                "GEOLIXO",
                style: GeolixoTheme.darkTheme.textTheme.displayMedium,
              ),
              const SizedBox(height: 8),
              Text(
                _isLogin ? "Jelentkezz be a kalandhoz" : "Készítsd el fiókodat",
                style: GeolixoTheme.darkTheme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 48),

              TextField(
                controller: _usernameController,
                decoration: InputDecoration(
                  labelText: "Felhasználónév",
                  prefixIcon: const Icon(Icons.person),
                  filled: true,
                  fillColor: Colors.white10,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: const TextStyle(color: Colors.white),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "Jelszó",
                  prefixIcon: const Icon(Icons.lock),
                  filled: true,
                  fillColor: Colors.white10,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: const TextStyle(color: Colors.white),
              ),
              const SizedBox(height: 32),

              _isLoading
                  ? const CircularProgressIndicator(color: GeolixoTheme.accent)
                  : SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _submit,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: GeolixoTheme.accent,
                          foregroundColor: GeolixoTheme.background,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: Text(_isLogin ? "BEJELENTKEZÉS" : "REGISZTRÁCIÓ"),
                      ),
                    ),
              
              const SizedBox(height: 24),
              TextButton(
                onPressed: () => setState(() => _isLogin = !_isLogin),
                child: Text(
                  _isLogin ? "Nincs még fiókod? Regisztrálj!" : "Van már fiókod? Jelentkezz be!",
                  style: const TextStyle(color: Colors.white70),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
