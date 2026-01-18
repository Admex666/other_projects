import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsService extends ChangeNotifier {
  String _mapStyle = 'dark';
  bool _hapticsEnabled = true;

  String get mapStyle => _mapStyle;
  bool get hapticsEnabled => _hapticsEnabled;

  SettingsService() {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    _mapStyle = prefs.getString('map_style') ?? 'dark';
    _hapticsEnabled = prefs.getBool('haptics_enabled') ?? true;
    notifyListeners();
  }

  Future<void> setMapStyle(String style) async {
    if (_mapStyle == style) return;
    _mapStyle = style;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('map_style', style);
    notifyListeners();
  }

  Future<void> setHapticsEnabled(bool enabled) async {
    if (_hapticsEnabled == enabled) return;
    _hapticsEnabled = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('haptics_enabled', enabled);
    notifyListeners();
  }
}
