import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'login_screen.dart';

/// RegisterScreen – NestCash fiók létrehozása modern (gradient) dizájnnal.
///
/// Mezők:
/// • Felhasználónév (kötelező)
/// • E‑mail (kötelező)
/// • Telefonszám (nem kötelező)
/// • Jelszó + megerősítés (kötelező)
///
/// Siker esetén visszadob a LoginScreen-re, ahol be lehet lépni.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _mobileCtrl = TextEditingController();
  final _pwCtrl = TextEditingController();
  final _pw2Ctrl = TextEditingController();
  final _authService = const AuthService();

  bool _pwVisible = false;
  bool _pw2Visible = false;
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _emailCtrl.dispose();
    _mobileCtrl.dispose();
    _pwCtrl.dispose();
    _pw2Ctrl.dispose();
    super.dispose();
  }

  // --- UI építő helper ---
  Widget _buildInputField({
    required String label,
    required TextEditingController controller,
    required String hintText,
    bool isPassword = false,
    bool isVisible = false,
    VoidCallback? onVisibilityToggle,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: const Color(0xFFE8F5E8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: TextFormField(
            controller: controller,
            obscureText: isPassword && !isVisible,
            keyboardType: keyboardType,
            style: const TextStyle(fontSize: 16, color: Colors.black87),
            decoration: InputDecoration(
              hintText: hintText,
              hintStyle: TextStyle(color: Colors.grey[600], fontSize: 16),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              suffixIcon: isPassword
                  ? IconButton(
                      icon: Icon(
                        isVisible ? Icons.visibility : Icons.visibility_off,
                        color: Colors.grey[600],
                      ),
                      onPressed: onVisibilityToggle,
                    )
                  : null,
            ),
            validator: validator,
          ),
        ),
      ],
    );
  }

  Future<void> _submit() async {
    final form = _formKey.currentState;
    if (form == null) return;
    if (!form.validate()) return;

    setState(() {
      _submitting = true;
      _error = null;
    });

    final ok = await _authService.register(
      _usernameCtrl.text.trim(),
      _emailCtrl.text.trim(),
      mobile: _mobileCtrl.text.trim().isEmpty ? null : _mobileCtrl.text.trim(),
      _pwCtrl.text,
    );

    if (!mounted) return;
    setState(() => _submitting = false);

    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sikeres regisztráció. Jelentkezz be!')),
      );
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    } else {
      setState(() => _error = 'Regisztráció sikertelen.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              child: const Text(
                'Hozz létre egy fiókot!',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            // Form Container
            Expanded(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                decoration: const BoxDecoration(
                  color: Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      children: [
                        const SizedBox(height: 20),
                        // Username Field (Full Name helyett)
                        _buildInputField(
                          label: 'Felhasználónév',
                          controller: _usernameCtrl,
                          hintText: 'pl. adam123',
                          keyboardType: TextInputType.name,
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) {
                              return 'Add meg a felhasználónevet';
                            }
                            if (v.trim().length < 3) {
                              return 'Legalább 3 karakter';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),
                        // Email Field
                        _buildInputField(
                          label: 'E‑mail',
                          controller: _emailCtrl,
                          hintText: 'example@example.com',
                          keyboardType: TextInputType.emailAddress,
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) {
                              return 'Add meg az e‑mail címet';
                            }
                            final emailRegex = RegExp(r'^.+@.+\..+$');
                            if (!emailRegex.hasMatch(v.trim())) {
                              return 'Érvénytelen e‑mail';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),
                        // Mobile (nem kötelező)
                        _buildInputField(
                          label: 'Telefonszám (nem kötelező)',
                          controller: _mobileCtrl,
                          hintText: '+36 30 123 4567',
                          keyboardType: TextInputType.phone,
                          validator: (v) {
                            // Üres -> OK
                            if (v == null || v.trim().isEmpty) return null;
                            // Minimális laza validáció
                            if (v.trim().length < 5) return 'Túl rövid';
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),
                        // Password
                        _buildInputField(
                          label: 'Jelszó',
                          controller: _pwCtrl,
                          hintText: '● ● ● ● ● ● ● ●',
                          isPassword: true,
                          isVisible: _pwVisible,
                          onVisibilityToggle: () {
                            setState(() => _pwVisible = !_pwVisible);
                          },
                          validator: (v) {
                            if (v == null || v.isEmpty) {
                              return 'Adj meg egy jelszót';
                            }
                            if (v.length < 6) {
                              return 'Legalább 6 karakter';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),
                        // Confirm Password
                        _buildInputField(
                          label: 'Jelszó megerősítése',
                          controller: _pw2Ctrl,
                          hintText: '● ● ● ● ● ● ● ●',
                          isPassword: true,
                          isVisible: _pw2Visible,
                          onVisibilityToggle: () {
                            setState(() => _pw2Visible = !_pw2Visible);
                          },
                          validator: (v) {
                            if (v == null || v.isEmpty) {
                              return 'Ismételd meg a jelszót';
                            }
                            if (v != _pwCtrl.text) {
                              return 'A jelszavak nem egyeznek';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 30),
                        // Terms text
                        RichText(
                          textAlign: TextAlign.center,
                          text: TextSpan(
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                              height: 1.5,
                            ),
                            children: const [
                              TextSpan(text: 'A folytatással elfogadod a\n'),
                              TextSpan(
                                text: 'Felhasználási feltételeket',
                                style: TextStyle(
                                  color: Color(0xFF00D4AA),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              TextSpan(text: ' és a '),
                              TextSpan(
                                text: 'Adatkezelési tájékoztatót',
                                style: TextStyle(
                                  color: Color(0xFF00D4AA),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              TextSpan(text: '.'),
                            ],
                          ),
                        ),
                        const SizedBox(height: 30),
                        // Error
                        if (_error != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Text(
                              _error!,
                              style: const TextStyle(color: Colors.red),
                            ),
                          ),
                        // Sign Up Button
                        SizedBox(
                          width: double.infinity,
                          height: 56,
                          child: ElevatedButton(
                            onPressed: _submitting ? null : _submit,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF00D4AA),
                              foregroundColor: Colors.white,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                              ),
                            ),
                            child: _submitting
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Text(
                                    'Regisztrálok',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                          ),
                        ),
                        const SizedBox(height: 20),
                        // Already have an account
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              'Már van fiókod? ',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey[600],
                              ),
                            ),
                            GestureDetector(
                              onTap: () {
                                Navigator.of(context).pushReplacement(
                                  MaterialPageRoute(
                                    builder: (_) => const LoginScreen(),
                                  ),
                                );
                              },
                              child: const Text(
                                'Bejelentkezés',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Color(0xFF00D4AA),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 30),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
