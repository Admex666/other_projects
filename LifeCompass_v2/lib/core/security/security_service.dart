import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SecurityService {
  final FlutterSecureStorage _storage;
  final LocalAuthentication _localAuth;

  static const _pinKey = 'user_pin_hash';
  static const _biometricKey = 'biometric_enabled';

  SecurityService(this._storage, this._localAuth);

  Future<bool> hasPin() async {
    final pin = await _storage.read(key: _pinKey);
    return pin != null;
  }

  Future<void> setPin(String pin) async {
    final hash = _hashPin(pin);
    await _storage.write(key: _pinKey, value: hash);
  }

  Future<bool> verifyPin(String pin) async {
    final storedHash = await _storage.read(key: _pinKey);
    if (storedHash == null) return false;
    return storedHash == _hashPin(pin);
  }

  String _hashPin(String pin) {
    final bytes = utf8.encode(pin);
    return sha256.convert(bytes).toString();
  }

  Future<bool> isBiometricAvailable() async {
    final canAuthenticateWithBiometrics = await _localAuth.canCheckBiometrics;
    final canAuthenticate = canAuthenticateWithBiometrics || await _localAuth.isDeviceSupported();
    return canAuthenticate;
  }

  Future<bool> isBiometricEnabled() async {
    final enabled = await _storage.read(key: _biometricKey);
    return enabled == 'true';
  }

  Future<void> setBiometricEnabled(bool enabled) async {
    await _storage.write(key: _biometricKey, value: enabled.toString());
  }

  Future<bool> authenticateBiometric(String localizedReason) async {
    try {
      return await _localAuth.authenticate(
        localizedReason: localizedReason,
      );
    } catch (e) {
      return false;
    }
  }
}

final securityServiceProvider = Provider<SecurityService>((ref) {
  return SecurityService(
    const FlutterSecureStorage(),
    LocalAuthentication(),
  );
});
