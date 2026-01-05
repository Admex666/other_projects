
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/story_engine.dart';
import '../services/api_service.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLogin = true;
  bool _isLoading = false;
  String? _error;

  final ApiService _api = ApiService();

  Future<void> _submit() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final engine = Provider.of<StoryEngine>(context, listen: false);
      final user = _isLogin 
          ? await _api.login(_usernameController.text, _passwordController.text)
          : await _api.register(_usernameController.text, _passwordController.text);
      
      engine.setUser(user);
      // Save user to local storage if needed, but StoryEngine already handles it? 
      // Actually we should save user ID to SharedPreferences for auto-login.
    } catch (e) {
      setState(() => _error = e.toString().replaceAll("Exception: ", ""));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(32.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.auto_stories, size: 60, color: Colors.blueAccent),
                const SizedBox(height: 24),
                Text(
                  "StoryTurak",
                  textAlign: TextAlign.center,
                  style: GoogleFonts.outfit(fontSize: 32, fontWeight: FontWeight.bold),
                ),
                Text(
                  "A város mesélni akar.",
                  textAlign: TextAlign.center,
                  style: GoogleFonts.outfit(fontSize: 16, color: Colors.white38),
                ),
                const SizedBox(height: 48),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Text(_error!, style: const TextStyle(color: Colors.redAccent), textAlign: TextAlign.center),
                  ),
                TextField(
                  controller: _usernameController,
                  decoration: InputDecoration(
                    hintText: "Felhasználónév",
                    filled: true,
                    fillColor: Colors.white.withOpacity(0.05),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    hintText: "Jelszó",
                    filled: true,
                    fillColor: Colors.white.withOpacity(0.05),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading 
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : Text(_isLogin ? "BEJELENTKEZÉS" : "REGISZTRÁCIÓ"),
                ),
                TextButton(
                  onPressed: () => setState(() => _isLogin = !_isLogin),
                  child: Text(_isLogin ? "Nincs még fiókod? Regisztrálj!" : "Már van fiókod? Jelentkezz be!"),
                ),
                const Spacer(),
                Consumer<StoryEngine>(
                  builder: (context, engine, _) => FutureBuilder<bool>(
                    future: SharedPreferences.getInstance().then((p) => p.getBool('use_local_backend') ?? false),
                    builder: (context, snapshot) {
                      bool isLocal = snapshot.data ?? false;
                      return Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (isLocal)
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 8),
                              child: TextField(
                                style: const TextStyle(color: Colors.white70, fontSize: 12),
                                textAlign: TextAlign.center,
                                decoration: const InputDecoration(
                                  hintText: "Gép IP címe (pl. 192.168.1.15)",
                                  hintStyle: TextStyle(color: Colors.white24),
                                  isDense: true,
                                ),
                                onChanged: (val) async {
                                  final prefs = await SharedPreferences.getInstance();
                                  await prefs.setString('local_ip', val);
                                },
                              ),
                            ),
                          TextButton(
                            onPressed: () async {
                              final prefs = await SharedPreferences.getInstance();
                              await prefs.setBool('use_local_backend', !isLocal);
                              setState(() {}); // Refresh UI
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text(!isLocal ? "Átváltva: Localhost" : "Átváltva: Cloud")),
                              );
                            },
                            child: Text(
                              isLocal ? "DEV MODE: LOCALHOST (8001)" : "CLOUD MODE: RENDER",
                              style: const TextStyle(color: Colors.white24, fontSize: 10),
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                ),
                const Text(
                  "Early Access v0.2",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white12, fontSize: 10),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
