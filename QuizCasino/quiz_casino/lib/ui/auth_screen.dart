import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'widgets/chunky_button.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLogin = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundDarkNavy,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
          child: Column(
            children: [
              const SizedBox(height: 20),
              // Animated Logo
              Image.asset('assets/knowcoin.png', height: 120)
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scaleXY(begin: 0.9, end: 1.1, duration: 2.seconds, curve: Curves.easeInOut),
              
              const SizedBox(height: 12),
              Text(
                "KNOWCOIN",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 4,
                  shadows: [
                    Shadow(color: AppTheme.neonCyan.withOpacity(0.5), blurRadius: 10)
                  ],
                ),
              ).animate().shimmer(duration: 3.seconds, color: AppTheme.neonCyan),
              
              const SizedBox(height: 60),
              
              // Auth Card
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: AppTheme.panelGlassColor,
                  borderRadius: BorderRadius.circular(30),
                  border: Border.all(color: AppTheme.neonCyan.withOpacity(0.2)),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 40, spreadRadius: 10)
                  ],
                ),
                child: Column(
                  children: [
                    Text(
                      _isLogin ? "WELCOME BACK" : "JOIN THE CASINO",
                      style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, letterSpacing: 1),
                    ),
                    const SizedBox(height: 32),
                    
                    // Fields
                    _buildField(
                      controller: _usernameController,
                      label: "USERNAME",
                      icon: Icons.person_rounded,
                    ),
                    const SizedBox(height: 20),
                    _buildField(
                      controller: _passwordController,
                      label: "PASSWORD",
                      icon: Icons.lock_rounded,
                      isPassword: true,
                    ),
                    
                    const SizedBox(height: 40),
                    
                    // Action Button
                    Consumer<GameManager>(
                      builder: (context, game, child) {
                        return Column(
                          children: [
                            if (game.authError != null)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 16),
                                child: Text(
                                  game.authError!,
                                  style: const TextStyle(color: Colors.redAccent, fontSize: 12, fontWeight: FontWeight.bold),
                                  textAlign: TextAlign.center,
                                ).animate().shake(),
                              ),
                            
                            SizedBox(
                              width: double.infinity,
                              height: 60,
                              child: ChunkyButton(
                                onTap: game.isAuthLoading ? null : () {
                                  if (_isLogin) {
                                    game.login(_usernameController.text, _passwordController.text);
                                  } else {
                                    game.register(_usernameController.text, _passwordController.text);
                                  }
                                },
                                baseColor: AppTheme.neonCyan,
                                shadowColor: const Color(0xFF009989),
                                child: Center(
                                  child: game.isAuthLoading 
                                    ? const SizedBox(
                                        height: 24, width: 24,
                                        child: CircularProgressIndicator(color: Colors.black, strokeWidth: 3),
                                      )
                                    : Text(
                                        _isLogin ? "LOGIN" : "REGISTER",
                                        style: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 2),
                                      ),
                                ),
                              ),
                            ),
                          ],
                        );
                      }
                    ),
                    
                    const SizedBox(height: 20),
                    
                    // Switch
                    TextButton(
                      onPressed: () => setState(() => _isLogin = !_isLogin),
                      child: Text(
                        _isLogin ? "NEED AN ACCOUNT? SIGN UP" : "ALREADY HAVE AN ACCOUNT? LOGIN",
                        style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn(duration: 800.ms).slideY(begin: 0.1, end: 0),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool isPassword = false,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          obscureText: isPassword,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            prefixIcon: Icon(icon, color: AppTheme.neonCyan, size: 20),
            filled: true,
            fillColor: Colors.black.withOpacity(0.2),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: const BorderSide(color: AppTheme.neonCyan, width: 1),
            ),
          ),
        ),
      ],
    );
  }
}
