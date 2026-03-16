import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'widgets/chunky_button.dart';
import 'widgets/cyber_loader.dart';

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
        child: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
              const SizedBox(height: 20),
              // Branded Logo
              Image.asset('assets/knowcoin.png', height: 140)
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scale(begin: const Offset(0.9, 0.9), end: const Offset(1.1, 1.1), duration: 2.seconds, curve: Curves.easeInOut),
              
              const SizedBox(height: 12),
              Text(
                "KNOWCOIN",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 6,
                  shadows: [
                    Shadow(color: AppTheme.neonCyan.withOpacity(0.5), blurRadius: 15)
                  ],
                ),
              ).animate().shimmer(duration: 3.seconds, color: AppTheme.neonCyan),
              
              const SizedBox(height: 60),
              
              // Auth Console
              Container(
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: const Color(0xFF151525).withOpacity(0.9),
                  borderRadius: BorderRadius.circular(30),
                  border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3), width: 2),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 50, spreadRadius: 5)
                  ],
                ),
                child: Column(
                  children: [
                    Text(
                      _isLogin ? "LOGIN" : "REGISTER",
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.w900, letterSpacing: 1.5, fontSize: 13),
                    ),
                    const SizedBox(height: 32),
                    
                    // Themed Fields
                    _buildField(
                      controller: _usernameController,
                      label: "USERNAME",
                      icon: Icons.person_rounded,
                    ),
                    const SizedBox(height: 24),
                    _buildField(
                      controller: _passwordController,
                      label: "PASSWORD",
                      icon: Icons.vpn_key_rounded,
                      isPassword: true,
                    ),
                    
                    const SizedBox(height: 48),
                    
                    // LOGIN BUTTON
                    Consumer<GameManager>(
                      builder: (context, game, child) {
                        return Column(
                          children: [
                            if (game.authError != null)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 20),
                                child: Text(
                                  game.authError!.toUpperCase(),
                                  style: const TextStyle(color: AppTheme.dangerRed, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1),
                                  textAlign: TextAlign.center,
                                ).animate().shake(hz: 8),
                              ),
                            
                            SizedBox(
                              width: double.infinity,
                              child: ChunkyButton(
                                onTap: game.isAuthLoading ? null : () {
                                  if (_isLogin) {
                                    game.login(_usernameController.text, _passwordController.text);
                                  } else {
                                    game.register(_usernameController.text, _passwordController.text);
                                  }
                                },
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                baseColor: AppTheme.neonCyan,
                                shadowColor: const Color(0xFF009989),
                                borderRadius: 30,
                                child: Center(
                                  child: game.isAuthLoading 
                                    ? const CyberLoader(size: 30) // Use new loader
                                    : Text(
                                        _isLogin ? "SIGN IN" : "CREATE ACCOUNT",
                                        style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2, color: Colors.black, fontSize: 16),
                                      ),
                                ),
                              ),
                            ),
                          ],
                        );
                      }
                    ),
                    
                    const SizedBox(height: 24),
                    
                    TextButton(
                      onPressed: () => setState(() => _isLogin = !_isLogin),
                      child: Text(
                        _isLogin ? "NEW PLAYER? REGISTER HERE" : "ALREADY A PLAYER? LOGIN HERE",
                        style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1),
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn(duration: 800.ms).slideY(begin: 0.1, end: 0),
                ],
              ),
            ),
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
