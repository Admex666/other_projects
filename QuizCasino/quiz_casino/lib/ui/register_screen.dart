import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'widgets/chunky_button.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundDarkNavy,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 40),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Image.asset('assets/knowcoin.png', height: 120)
                  .animate()
                  .fadeIn()
                  .scale(curve: Curves.elasticOut, duration: 1.seconds),
                const SizedBox(height: 32),
                const Text(
                  "WELCOME TO KNOWCOIN",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 2,
                  ),
                ).animate().fadeIn(delay: 400.ms),
                const SizedBox(height: 12),
                const Text(
                  "ENTER YOUR LEGENDARY NAME",
                  style: TextStyle(
                    color: AppTheme.neonCyan,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 4,
                  ),
                ).animate().fadeIn(delay: 600.ms),
                const SizedBox(height: 40),
                TextField(
                  controller: _controller,
                  maxLength: 15,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
                  decoration: InputDecoration(
                    counterStyle: const TextStyle(color: Colors.white24),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(20),
                      borderSide: const BorderSide(color: AppTheme.neonCyan, width: 2),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(20),
                      borderSide: const BorderSide(color: AppTheme.purpleGlow, width: 3),
                    ),
                    filled: true,
                    fillColor: Colors.white.withOpacity(0.05),
                    hintText: "USERNAME",
                    hintStyle: TextStyle(color: Colors.white.withOpacity(0.2)),
                  ),
                ).animate().fadeIn(delay: 800.ms).slideY(begin: 0.2, end: 0),
                const SizedBox(height: 48),
                _isLoading 
                  ? const CircularProgressIndicator(color: AppTheme.neonCyan)
                  : SizedBox(
                      width: double.infinity,
                      height: 80,
                      child: ChunkyButton(
                        onTap: () async {
                          if (_controller.text.trim().isEmpty) return;
                          setState(() => _isLoading = true);
                          await context.read<GameManager>().registerUser(_controller.text.trim());
                        },
                        baseColor: AppTheme.neonCyan,
                        shadowColor: const Color(0xFF009989),
                        borderRadius: 40,
                        child: const Center(
                          child: Text(
                            "START EARNING",
                            style: TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 20, letterSpacing: 2),
                          ),
                        ),
                      ),
                    ).animate().fadeIn(delay: 1.seconds).scale(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
