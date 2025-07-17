import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'login_screen.dart';

/// RegisterScreen – felhasználói fiók létrehozása.
///
/// Bekért adatok: felhasználónév, e‑mail, jelszó, jelszó megerősítés.
/// Sikeres regisztráció után visszadob a LoginScreen-re (egyelőre nincs auto-login).
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _pwCtrl = TextEditingController();
  final _pw2Ctrl = TextEditingController();
  final _authService = const AuthService();

  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _emailCtrl.dispose();
    _pwCtrl.dispose();
    _pw2Ctrl.dispose();
    super.dispose();
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
      _pwCtrl.text,
    );

    setState(() => _submitting = false);

    if (!mounted) return;

    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Sikeres regisztráció. Jelentkezz be!')),
      );
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => LoginScreen()),
      );
    } else {
      setState(() => _error = 'Regisztráció sikertelen.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Regisztráció')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _usernameCtrl,
                decoration: const InputDecoration(labelText: 'Felhasználónév'),
                textInputAction: TextInputAction.next,
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
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailCtrl,
                decoration: const InputDecoration(labelText: 'E‑mail'),
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
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
              const SizedBox(height: 16),
              TextFormField(
                controller: _pwCtrl,
                decoration: const InputDecoration(labelText: 'Jelszó'),
                obscureText: true,
                textInputAction: TextInputAction.next,
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
              const SizedBox(height: 16),
              TextFormField(
                controller: _pw2Ctrl,
                decoration: const InputDecoration(labelText: 'Jelszó megerősítése'),
                obscureText: true,
                textInputAction: TextInputAction.done,
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
              const SizedBox(height: 24),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              _submitting
                  ? const Center(child: CircularProgressIndicator())
                  : ElevatedButton(
                      onPressed: _submit,
                      child: const Text('Regisztrálok'),
                    ),
              TextButton(
                onPressed: () {
                  Navigator.of(context).pushReplacement(
                    MaterialPageRoute(builder: (_) => LoginScreen()),
                  );
                },
                child: const Text('Már van fiókom – Bejelentkezés'),
              )
            ],
          ),
        ),
      ),
    );
  }
}
