// lib/services/account_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/config/config.dart';

class AccountService {
  static const _storage = FlutterSecureStorage();

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  /// Számlák lekérése
  Future<Map<String, dynamic>> getAccounts() async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 404) {
        // Ha nincs számla, akkor üres struktúrát adunk vissza
        return {
          'likvid': {'alszamlak': {}, 'foosszeg': 0.0},
          'befektetes': {'alszamlak': {}, 'foosszeg': 0.0},
          'megtakaritas': {'alszamlak': {}, 'foosszeg': 0.0},
        };
      } else {
        throw Exception('Failed to load accounts: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting accounts: $e');
      throw Exception('Failed to load accounts: $e');
    }
  }

  /// Számlák összesítése
  Future<Map<String, double>> getAccountSummary() async {
    try {
      final accounts = await getAccounts();
      
      double totalLikvid = 0.0;
      double totalBefektetes = 0.0;
      double totalMegtakaritas = 0.0;
      double totalBalance = 0.0;

      // Likvid számlák összesítése
      if (accounts['likvid'] != null) {
        totalLikvid = (accounts['likvid']['foosszeg'] as num?)?.toDouble() ?? 0.0;
      }

      // Befektetési számlák összesítése
      if (accounts['befektetes'] != null) {
        totalBefektetes = (accounts['befektetes']['foosszeg'] as num?)?.toDouble() ?? 0.0;
      }

      // Megtakarítási számlák összesítése
      if (accounts['megtakaritas'] != null) {
        totalMegtakaritas = (accounts['megtakaritas']['foosszeg'] as num?)?.toDouble() ?? 0.0;
      }

      totalBalance = totalLikvid + totalBefektetes + totalMegtakaritas;

      return {
        'likvid': totalLikvid,
        'befektetes': totalBefektetes,
        'megtakaritas': totalMegtakaritas,
        'total': totalBalance,
      };
    } catch (e) {
      print('Error getting account summary: $e');
      return {
        'likvid': 0.0,
        'befektetes': 0.0,
        'megtakaritas': 0.0,
        'total': 0.0,
      };
    }
  }

  /// Alszámla hozzáadása
  Future<bool> addSubAccount({
    required String mainAccount,
    required String subAccountName,
    required double balance,
    String currency = 'HUF',
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.put(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me/$mainAccount/$subAccountName'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'balance': balance,
          'currency': currency,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error adding sub account: $e');
      return false;
    }
  }

  /// Alszámla törlése
  Future<bool> deleteSubAccount({
    required String mainAccount,
    required String subAccountName,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me/$mainAccount/$subAccountName'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200 || response.statusCode == 204;
    } catch (e) {
      print('Error deleting sub account: $e');
      return false;
    }
  }

  /// Egyenleg frissítése
  Future<bool> updateBalance({
    required String mainAccount,
    required String subAccountName,
    required double newBalance,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.patch(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me/$mainAccount/$subAccountName/balance'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'balance': newBalance,
        }),
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Error updating balance: $e');
      return false;
    }
  }

  /// Főszámla típusok lekérése
  List<String> getMainAccountTypes() {
    return ['likvid', 'befektetes', 'megtakaritas'];
  }

  /// Alszámlák lekérése egy főszámla alatt
  Future<List<String>> getSubAccounts(String mainAccount) async {
    try {
      final accounts = await getAccounts();
      if (accounts[mainAccount] != null && accounts[mainAccount]['alszamlak'] != null) {
        final subAccounts = accounts[mainAccount]['alszamlak'] as Map<String, dynamic>;
        return subAccounts.keys.toList();
      }
      return [];
    } catch (e) {
      print('Error getting sub accounts: $e');
      return [];
    }
  }

  /// Számla adatok formázása megjelenítéshez
  Map<String, dynamic> formatAccountsForDisplay(Map<String, dynamic> accounts) {
    final formatted = <String, dynamic>{};
    
    for (final mainAccountKey in accounts.keys) {
      final mainAccount = accounts[mainAccountKey];
      if (mainAccount == null) continue;

      final subAccounts = <String, Map<String, dynamic>>{};
      final alszamlak = mainAccount['alszamlak'] as Map<String, dynamic>?;
      
      if (alszamlak != null) {
        for (final subAccountKey in alszamlak.keys) {
          final subAccount = alszamlak[subAccountKey];
          subAccounts[subAccountKey] = {
            'balance': (subAccount['balance'] as num?)?.toDouble() ?? 0.0,
            'currency': subAccount['currency'] ?? 'HUF',
            'formatted_balance': _formatCurrency((subAccount['balance'] as num?)?.toDouble() ?? 0.0),
          };
        }
      }

      formatted[mainAccountKey] = {
        'name': _formatAccountName(mainAccountKey),
        'total': (mainAccount['foosszeg'] as num?)?.toDouble() ?? 0.0,
        'formatted_total': _formatCurrency((mainAccount['foosszeg'] as num?)?.toDouble() ?? 0.0),
        'sub_accounts': subAccounts,
      };
    }

    return formatted;
  }

  String _formatAccountName(String key) {
    switch (key) {
      case 'likvid':
        return 'Likvid számlák';
      case 'befektetes':
        return 'Befektetési számlák';
      case 'megtakaritas':
        return 'Megtakarítási számlák';
      default:
        return key.toUpperCase();
    }
  }

  String _formatCurrency(double amount) {
    final absAmount = amount.abs();
    final sign = amount < 0 ? '-' : '';
    
    if (absAmount >= 1000000) {
      return '${sign}${(absAmount / 1000000).toStringAsFixed(1)}M Ft';
    } else if (absAmount >= 1000) {
      return '${sign}${(absAmount / 1000).toStringAsFixed(0)}k Ft';
    } else {
      return '${sign}${absAmount.toStringAsFixed(0)} Ft';
    }
  }
}