import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'security_service.dart';
import '../navigation/main_navigation_screen.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final TextEditingController _pinController = TextEditingController();
  bool _isChecking = true;
  bool _hasPin = false;

  @override
  void initState() {
    super.initState();
    _checkSecurity();
  }

  Future<void> _checkSecurity() async {
    final security = ref.read(securityServiceProvider);
    final hasPin = await security.hasPin();
    
    if (mounted) {
      setState(() {
        _hasPin = hasPin;
        _isChecking = false;
      });
      
      if (hasPin && await security.isBiometricEnabled()) {
        await _authenticateBiometric();
      }
    }
  }

  Future<void> _authenticateBiometric() async {
    final security = ref.read(securityServiceProvider);
    final success = await security.authenticateBiometric('Please authenticate to open LifeCompass');
    if (success && mounted) {
      _onAuthenticated();
    }
  }

  void _onAuthenticated() {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const MainNavigationScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isChecking) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: Text(_hasPin ? 'Enter PIN' : 'Create PIN')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            TextField(
              controller: _pinController,
              keyboardType: TextInputType.number,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'PIN'),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () async {
                final pin = _pinController.text;
                final security = ref.read(securityServiceProvider);
                if (_hasPin) {
                  final isValid = await security.verifyPin(pin);
                  if (!context.mounted) return;
                  if (isValid) {
                    _onAuthenticated();
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Invalid PIN')),
                    );
                  }
                } else {
                  await security.setPin(pin);
                  if (mounted) _checkSecurity();
                }
              },
              child: Text(_hasPin ? 'Unlock' : 'Setup'),
            ),
          ],
        ),
      ),
    );
  }
}
