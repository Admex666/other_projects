// lib/services/habit_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/models/habit.dart';

class HabitService {
  static const _storage = FlutterSecureStorage();
  final String baseUrl;

  const HabitService({this.baseUrl = 'http://10.0.2.2:8000'});

  Future<String?> _getToken() async {
    return await _storage.read(key: 'token');
  }

  Map<String, String> _getHeaders(String token) {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Szokások listázása
  Future<List<Habit>> getHabits({
    bool activeOnly = true,
    HabitCategory? category,
    int limit = 50,
    int skip = 0,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final queryParams = <String, String>{
        'active_only': activeOnly.toString(),
        'limit': limit.toString(),
        'skip': skip.toString(),
      };

      if (category != null) {
        queryParams['category'] = category.value;
      }

      final uri = Uri.parse('$baseUrl/habits/').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri, headers: _getHeaders(token));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final habits = (data['habits'] as List<dynamic>)
            .map((json) => Habit.fromJson(json))
            .toList();
        return habits;
      } else {
        throw Exception('Failed to load habits: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting habits: $e');
      throw Exception('Szokások betöltése sikertelen: $e');
    }
  }

  /// Egy szokás lekérése
  Future<Habit> getHabit(String habitId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('$baseUrl/habits/$habitId'),
        headers: _getHeaders(token),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return Habit.fromJson(data);
      } else {
        throw Exception('Failed to load habit: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting habit: $e');
      throw Exception('Szokás betöltése sikertelen: $e');
    }
  }

  /// Új szokás létrehozása
  Future<Habit> createHabit(Habit habit) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.post(
        Uri.parse('$baseUrl/habits/'),
        headers: _getHeaders(token),
        body: jsonEncode(habit.toJson()),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return Habit.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to create habit');
      }
    } catch (e) {
      print('Error creating habit: $e');
      throw Exception('Szokás létrehozása sikertelen: $e');
    }
  }

  /// Szokás frissítése
  Future<Habit> updateHabit(String habitId, Map<String, dynamic> updates) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.put(
        Uri.parse('$baseUrl/habits/$habitId'),
        headers: _getHeaders(token),
        body: jsonEncode(updates),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return Habit.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to update habit');
      }
    } catch (e) {
      print('Error updating habit: $e');
      throw Exception('Szokás frissítése sikertelen: $e');
    }
  }

  /// Szokás törlése
  Future<void> deleteHabit(String habitId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.delete(
        Uri.parse('$baseUrl/habits/$habitId'),
        headers: _getHeaders(token),
      );

      if (response.statusCode != 204) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to delete habit');
      }
    } catch (e) {
      print('Error deleting habit: $e');
      throw Exception('Szokás törlése sikertelen: $e');
    }
  }

  /// Szokás teljesítés rögzítése
  Future<HabitLog> logHabitCompletion(
    String habitId, {
    required bool completed,
    double? value,
    String? notes,
    String? date,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final body = <String, dynamic>{
        'completed': completed,
      };

      if (value != null) body['value'] = value;
      if (notes != null && notes.isNotEmpty) body['notes'] = notes;
      if (date != null) body['date'] = date;

      final response = await http.post(
        Uri.parse('$baseUrl/habits/$habitId/logs'),
        headers: _getHeaders(token),
        body: jsonEncode(body),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return HabitLog.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Sikertelen rögzítés');
      }
    } catch (e) {
      print('Error logging habit: $e');
      throw Exception('Szokás rögzítése sikertelen: $e');
    }
  }

  /// Szokás logok lekérése
  Future<List<HabitLog>> getHabitLogs(
    String habitId, {
    int limit = 30,
    int skip = 0,
    String? fromDate,
    String? toDate,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final queryParams = <String, String>{
        'limit': limit.toString(),
        'skip': skip.toString(),
      };

      if (fromDate != null) queryParams['from_date'] = fromDate;
      if (toDate != null) queryParams['to_date'] = toDate;

      final uri = Uri.parse('$baseUrl/habits/$habitId/logs').replace(
        queryParameters: queryParams,
      );

      final response = await http.get(uri, headers: _getHeaders(token));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final logs = (data['logs'] as List<dynamic>)
            .map((json) => HabitLog.fromJson(json))
            .toList();
        return logs;
      } else {
        throw Exception('Failed to load habit logs: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting habit logs: $e');
      throw Exception('Szokás előzmények betöltése sikertelen: $e');
    }
  }

  /// Szokás statisztikák
  Future<HabitStats> getHabitStats(String habitId, {int days = 30}) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final uri = Uri.parse('$baseUrl/habits/$habitId/stats').replace(
        queryParameters: {'days': days.toString()},
      );

      final response = await http.get(uri, headers: _getHeaders(token));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return HabitStats.fromJson(data);
      } else {
        throw Exception('Failed to load habit stats: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting habit stats: $e');
      throw Exception('Szokás statisztikák betöltése sikertelen: $e');
    }
  }

  /// Felhasználó szokás áttekintő
  Future<UserHabitOverview> getUserHabitOverview() async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('$baseUrl/habits/overview/stats'),
        headers: _getHeaders(token),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return UserHabitOverview.fromJson(data);
      } else {
        throw Exception('Failed to load overview: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting habit overview: $e');
      throw Exception('Áttekintő betöltése sikertelen: $e');
    }
  }

  /// Előre definiált szokások
  Future<Map<HabitCategory, List<PredefinedHabit>>> getPredefinedHabits() async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.get(
        Uri.parse('$baseUrl/habits/predefined/list'),
        headers: _getHeaders(token),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List<dynamic>;
        final Map<HabitCategory, List<PredefinedHabit>> result = {};

        for (final categoryData in data) {
          final category = HabitCategory.fromString(categoryData['category']);
          final habits = (categoryData['habits'] as List<dynamic>)
              .map((json) => PredefinedHabit.fromJson(json))
              .toList();
          result[category] = habits;
        }

        return result;
      } else {
        throw Exception('Failed to load predefined habits: ${response.statusCode}');
      }
    } catch (e) {
      print('Error getting predefined habits: $e');
      throw Exception('Előre definiált szokások betöltése sikertelen: $e');
    }
  }

  /// Előre definiált szokás létrehozása
  Future<Habit> createHabitFromPredefined(
    HabitCategory category,
    int habitIndex,
  ) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.post(
        Uri.parse('$baseUrl/habits/predefined/${category.value}/$habitIndex'),
        headers: _getHeaders(token),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return Habit.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Szokás létrehozása sikertelen');
      }
    } catch (e) {
      print('Error creating predefined habit: $e');
      throw Exception('Előre definiált szokás létrehozása sikertelen: $e');
    }
  }

  /// Szokás log frissítése
  Future<HabitLog> updateHabitLog(
    String habitId,
    String logId,
    Map<String, dynamic> updates,
  ) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.put(
        Uri.parse('$baseUrl/habits/$habitId/logs/$logId'),
        headers: _getHeaders(token),
        body: jsonEncode(updates),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return HabitLog.fromJson(data);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Log frissítése sikertelen');
      }
    } catch (e) {
      print('Error updating habit log: $e');
      throw Exception('Szokás bejegyzés frissítése sikertelen: $e');
    }
  }

  /// Szokás log törlése
  Future<void> deleteHabitLog(String habitId, String logId) async {
    try {
      final token = await _getToken();
      if (token == null) throw Exception('Not authenticated');

      final response = await http.delete(
        Uri.parse('$baseUrl/habits/$habitId/logs/$logId'),
        headers: _getHeaders(token),
      );

      if (response.statusCode != 204) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Log törlése sikertelen');
      }
    } catch (e) {
      print('Error deleting habit log: $e');
      throw Exception('Szokás bejegyzés törlése sikertelen: $e');
    }
  }
}