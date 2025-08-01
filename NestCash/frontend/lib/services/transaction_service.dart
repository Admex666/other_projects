// lib/services/transaction_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TransactionService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const TransactionService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  /// Tranzakciók lekérése
  Future<List<Map<String, dynamic>>> getTransactions({
    int limit = 20,
    int skip = 0,
    String? type, // 'income' vagy 'expense'
    String? category,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final queryParams = <String, String>{
        'limit': limit.toString(),
        'skip': skip.toString(),
      };

      if (type != null) queryParams['type'] = type;
      if (category != null) queryParams['category'] = category;
      
      // Javított dátum formátum - több formátumot próbálunk
      if (startDate != null) {
        queryParams['start_date'] = _formatDate(startDate);
      }
      if (endDate != null) {
        queryParams['end_date'] = _formatDate(endDate);
      }

      final uri = Uri.parse('$baseUrl/transactions/').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      print('Requesting transactions from: ${uri.toString()}'); // Debug log

      final response = await http.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      print('Transaction response status: ${response.statusCode}'); // Debug log
      print('Transaction response body: ${response.body}'); // Debug log

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Több lehetséges response struktúrát kezelünk
        if (data is List) {
          return List<Map<String, dynamic>>.from(data);
        } else if (data is Map && data.containsKey('transactions')) {
          return List<Map<String, dynamic>>.from(data['transactions']);
        } else if (data is Map && data.containsKey('data')) {
          return List<Map<String, dynamic>>.from(data['data']);
        } else {
          // Ha a válasz egy objektum, akkor egy elemű listába tesszük
          return [Map<String, dynamic>.from(data)];
        }
      } else {
        print('Transaction request failed: ${response.statusCode} - ${response.body}');
        throw Exception('Failed to load transactions: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting transactions: $e');
      // Ne dobjunk exception-t, hanem adjunk vissza üres listát
      return [];
    }
  }

  /// Legutóbbi tranzakciók
  Future<List<Map<String, dynamic>>> getRecentTransactions({int limit = 5}) async {
    return await getTransactions(limit: limit);
  }

  /// Tranzakció létrehozása
  Future<Map<String, dynamic>> createTransaction({
    required String type,
    required double amount,
    required String description,
    required DateTime date,
    String? category,
    String? mainAccount,
    String? subAccountName,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final payload = {
        'type': type,
        'amount': amount,
        'description': description,
        'date': date.toIso8601String().split('T')[0],
        if (category != null) 'kategoria': category,
        if (mainAccount != null) 'main_account': mainAccount,
        if (subAccountName != null) 'sub_account_name': subAccountName,
      };

      final response = await http.post(
        Uri.parse('$baseUrl/transactions/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return jsonDecode(response.body);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to create transaction');
      }
    } catch (e) {
      print('Error creating transaction: $e');
      throw Exception('Failed to create transaction: $e');
    }
  }

  /// Tranzakció frissítése
  Future<void> updateTransaction(String transactionId, Map<String, dynamic> transactionData) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Nincs autentikációs token');

      final response = await http.put(
        Uri.parse('$baseUrl/transactions/$transactionId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(transactionData),
      );

      if (response.statusCode != 200) {
        final errorData = jsonDecode(response.body);
        final error = errorData['detail'] ?? 'Ismeretlen hiba';
        throw Exception(error);
      }
    } catch (e) {
      print('Error updating transaction: $e');
      throw Exception('Failed to update transaction: $e');
    }
  }

  /// Tranzakció törlése
  Future<void> deleteTransaction(String transactionId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.delete(
        Uri.parse('$baseUrl/transactions/$transactionId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode != 200 && response.statusCode != 204) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to delete transaction');
      }
    } catch (e) {
      print('Error deleting transaction: $e');
      throw Exception('Failed to delete transaction: $e');
    }
  }

  /// Havi összesítés lekérése
  Future<Map<String, dynamic>> getMonthlyStats({
    DateTime? month,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final targetMonth = month ?? DateTime.now();
      final startDate = DateTime(targetMonth.year, targetMonth.month, 1);
      final endDate = DateTime(targetMonth.year, targetMonth.month + 1, 0);

      // Először próbáljuk a /summary endpoint-ot
      try {
        final summaryUri = Uri.parse('$baseUrl/transactions/summary').replace(
          queryParameters: {
            'start_date': _formatDate(startDate),
            'end_date': _formatDate(endDate),
          },
        );

        print('Requesting summary from: ${summaryUri.toString()}'); // Debug log

        final summaryResponse = await http.get(
          summaryUri,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $token',
          },
        );

        print('Summary response status: ${summaryResponse.statusCode}'); // Debug log
        
        if (summaryResponse.statusCode == 200) {
          final data = jsonDecode(summaryResponse.body);
          return _processSummaryData(data);
        }
      } catch (e) {
        print('Summary endpoint failed: $e');
      }

      // Ha a /summary nem működik, próbáljuk a /stats endpoint-ot
      try {
        final statsUri = Uri.parse('$baseUrl/transactions/stats').replace(
          queryParameters: {
            'start_date': _formatDate(startDate),
            'end_date': _formatDate(endDate),
          },
        );

        print('Requesting stats from: ${statsUri.toString()}'); // Debug log

        final statsResponse = await http.get(
          statsUri,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $token',
          },
        );

        print('Stats response status: ${statsResponse.statusCode}'); // Debug log
        
        if (statsResponse.statusCode == 200) {
          final data = jsonDecode(statsResponse.body);
          return _processSummaryData(data);
        }
      } catch (e) {
        print('Stats endpoint failed: $e');
      }

      // Fallback: számoljuk ki a tranzakciókból
      return await _calculateStatsFromTransactions(month);
    } catch (e) {
      print('Error getting monthly stats: $e');
      // Fallback: számoljuk ki a tranzakciókból
      return await _calculateStatsFromTransactions(month);
    }
  }

  /// Backup: stats számítása tranzakciókból
  Future<Map<String, dynamic>> _calculateStatsFromTransactions(DateTime? month) async {
    try {
      print('Calculating stats from transactions...'); // Debug log
      
      final targetMonth = month ?? DateTime.now();
      final startDate = DateTime(targetMonth.year, targetMonth.month, 1);
      final endDate = DateTime(targetMonth.year, targetMonth.month + 1, 0);

      // Próbáljuk meg lekérni a tranzakciókat dátum szűrés nélkül először
      List<Map<String, dynamic>> transactions = [];
      
      try {
        transactions = await getTransactions(
          startDate: startDate,
          endDate: endDate,
          limit: 1000,
        );
      } catch (e) {
        print('Failed to get transactions with date filter, trying without: $e');
        // Ha dátum szűréssel nem megy, próbáljuk dátum nélkül
        try {
          transactions = await getTransactions(limit: 1000);
          // Saját magunk szűrjük a dátumokat
          transactions = transactions.where((transaction) {
            try {
              final dateStr = transaction['date'] ?? transaction['datum'];
              if (dateStr == null) return false;
              
              final transactionDate = DateTime.tryParse(dateStr.toString());
              if (transactionDate == null) return false;
              
              return transactionDate.isAfter(startDate.subtract(Duration(days: 1))) &&
                    transactionDate.isBefore(endDate.add(Duration(days: 1)));
            } catch (e) {
              return false;
            }
          }).toList();
        } catch (e2) {
          print('Failed to get any transactions: $e2');
          return _getDefaultStats();
        }
      }

      print('Processing ${transactions.length} transactions'); // Debug log

      double totalIncome = 0;
      double totalExpenses = 0;

      for (final transaction in transactions) {
        try {
          final amount = (transaction['amount'] ?? transaction['osszeg'] ?? 0 as num).toDouble();
          final type = transaction['type'] ?? transaction['tipus'];
          
          if (type == 'income' || type == 'bevetel' || amount > 0) {
            totalIncome += amount.abs();
          } else if (type == 'expense' || type == 'kiadas' || amount < 0) {
            totalExpenses += amount.abs();
          }
        } catch (e) {
          print('Error processing transaction: $transaction, error: $e');
          continue;
        }
      }

      print('Calculated stats: income=$totalIncome, expenses=$totalExpenses'); // Debug log

      return {
        'total_income': totalIncome,
        'total_expenses': totalExpenses,
        'net_balance': totalIncome - totalExpenses,
        'transaction_count': transactions.length,
      };
    } catch (e) {
      print('Error calculating stats from transactions: $e');
      return _getDefaultStats();
    }
  }

  /// Dátum formázás - több formátumot támogat
  String _formatDate(DateTime date) {
    // ISO 8601 formátum (YYYY-MM-DD)
    return date.toIso8601String().split('T')[0];
  }

  /// Summary adatok feldolgozása
  Map<String, dynamic> _processSummaryData(Map<String, dynamic> data) {
    return {
      'total_income': (data['total_income'] ?? data['bevetel_osszeg'] ?? data['income'] ?? 0 as num).toDouble(),
      'total_expenses': (data['total_expenses'] ?? data['kiadas_osszeg'] ?? data['expenses'] ?? 0 as num).toDouble(),
      'net_balance': (data['net_balance'] ?? data['netto_egyenleg'] ?? data['balance'] ?? 0 as num).toDouble(),
      'transaction_count': (data['transaction_count'] ?? data['tranzakcio_szam'] ?? data['count'] ?? 0 as num).toInt(),
    };
  }

  /// Alapértelmezett stats ha minden más elbukik
  Map<String, dynamic> _getDefaultStats() {
    return {
      'total_income': 0.0,
      'total_expenses': 0.0,
      'net_balance': 0.0,
      'transaction_count': 0,
    };
  }
}