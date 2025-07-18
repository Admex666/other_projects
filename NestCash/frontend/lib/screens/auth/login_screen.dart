import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'register_screen.dart';
import '../dashboard_screen.dart';
import 'auth_wrapper.dart';

/// LoginScreen – NestCash bejelentkezés modern (gradient) dizájnnal.
///
/// A felhasználó bemehet **felhasználónévvel VAGY emaillel**.
/// A FastAPI backend `/auth/token` végpontját hívjuk (OAuth2 password flow form-data body-val).
/// Siker esetén token mentés (AuthService), majd Dashboard.
/// Hibánál SnackBar + inline hibaüzenet.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _loginCtrl = TextEditingController(); // username OR email
  final TextEditingController _pwCtrl = TextEditingController();
  final AuthService _auth = const AuthService();

  bool _isPasswordVisible = false;
  bool _isLoading = false;
  String? _errorMsg; // megjelenítjük a form fölött

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF00D4A3), Color(0xFFE8F6F3)],
            stops: [0.0, 0.5],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              const SizedBox(height: 40),
              const Text(
                'Üdvözlünk!',
                style: TextStyle(
                  color: Colors.black,
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 60),
              Expanded(
                child: Container(
                  decoration: const BoxDecoration(
                    color: Color(0xFFF0F8F0),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 20),
                        if (_errorMsg != null) ...[
                          Container(
                            width: double.infinity,
                            margin: const EdgeInsets.only(bottom: 16),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.red.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _errorMsg!,
                              style: const TextStyle(color: Colors.red, fontSize: 14),
                            ),
                          ),
                        ],
                        const Text(
                          'Felhasználónév vagy Email',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 8),
                        _buildInputField(
                          controller: _loginCtrl,
                          hintText: 'minta@minta.com',
                          keyboardType: TextInputType.emailAddress,
                        ),
                        const SizedBox(height: 24),
                        const Text(
                          'Jelszó',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 8),
                        _buildPasswordField(),
                        const SizedBox(height: 40),
                        SizedBox(
                          width: double.infinity,
                          height: 56,
                          child: ElevatedButton(
                            onPressed: _isLoading ? null : _handleLogin,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF00D4A3),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(28),
                              ),
                              elevation: 0,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      color: Colors.white,
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text(
                                    'Bejelentkezés',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        
                        SizedBox(
                          width: double.infinity,
                          height: 56,
                          child: OutlinedButton(
                            onPressed: _isLoading ? null : _goToRegister,
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.black87,
                              side: BorderSide(color: Colors.grey[300]!),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(28),
                              ),
                              backgroundColor: Colors.white.withOpacity(0.7),
                            ),
                            child: const Text(
                              'Kezdjünk bele!',
                              style: TextStyle(
                                color: Color(0xFF00D4AA),
                                fontSize: 18,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Center(
                          child: TextButton(
                            onPressed: _isLoading ? null : _onForgotPassword,
                            child: Text(
                              'Elfelejtett Jelszó?',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 14,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 40),
                        _buildSocialSection(),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ----------------- UI Helper Widgets -----------------
  Widget _buildInputField({
    required TextEditingController controller,
    required String hintText,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.7),
        borderRadius: BorderRadius.circular(12),
      ),
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: TextStyle(
            color: Colors.grey[500],
            fontSize: 14,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 16,
          ),
        ),
      ),
    );
  }

  Widget _buildPasswordField() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.7),
        borderRadius: BorderRadius.circular(12),
      ),
      child: TextField(
        controller: _pwCtrl,
        obscureText: !_isPasswordVisible,
        decoration: InputDecoration(
          hintText: '• • • • • • • •',
          hintStyle: TextStyle(
            color: Colors.grey[500],
            fontSize: 18,
            letterSpacing: 4,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 16,
          ),
          suffixIcon: GestureDetector(
            onTap: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
            child: Icon(
              _isPasswordVisible ? Icons.visibility : Icons.visibility_off,
              color: Colors.grey[600],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSocialSection() {
    return Column(
      children: [
        Text(
          'vagy jelentkezz be',
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 14,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildSocialButton('f', () {/* Facebook login TODO */}),
            const SizedBox(width: 16),
            _buildSocialButton('G', () {/* Google login TODO */}),
          ],
        ),
      ],
    );
  }

  Widget _buildSocialButton(String text, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          border: Border.all(color: Colors.grey[300]!),
        ),
        child: Center(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: text == 'f' ? Colors.blue[800] : Colors.red,
            ),
          ),
        ),
      ),
    );
  }

  // ----------------- Actions -----------------
  Future<void> _handleLogin() async {
    FocusScope.of(context).unfocus();
    final login = _loginCtrl.text.trim();
    final pw = _pwCtrl.text;

    if (login.isEmpty || pw.isEmpty) {
      setState(() => _errorMsg = 'Kérlek tölts ki minden mezőt.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMsg = null;
    });

    final ok = await _auth.login(login, pw);

    setState(() => _isLoading = false);

    if (!mounted) return;

    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Sikeres bejelentkezés!'),
          backgroundColor: Color(0xFF00D4A3),
        ),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const AuthWrapper()),
      );
    } else {
      setState(() => _errorMsg = 'Hibás felhasználónév/email vagy jelszó.');
    }
  }

  void _goToRegister() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const RegisterScreen()),
    );
  }

  void _onForgotPassword() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Password reset TODO.')),
    );
  }

  @override
  void dispose() {
    _loginCtrl.dispose();
    _pwCtrl.dispose();
    super.dispose();
  }
}
