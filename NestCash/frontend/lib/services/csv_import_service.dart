// lib/services/csv_import_service.dart

import 'dart:convert';
import 'package:file_selector/file_selector.dart';
import 'package:http/http.dart' as http;
import '../models/csv_import_models.dart';
import '../config/config.dart';
import '../services/http_service.dart';

class CSVImportService {
  static const String baseUrl = '/import';

  // HTTP client segédfüggvények
  static Future<http.Response> _post(String endpoint, {
    required String body,
    required Map<String, String> headers,
  }) async {
    return await HttpService.authenticatedRequest(
      method: 'POST',
      url: '${ApiConfig.baseUrl}$endpoint',
      body: json.decode(body), // ha JSON string-ként jön
    );
  }

  static Future<http.Response> _get(String endpoint) async {
    return await HttpService.authenticatedRequest(
      method: 'GET',
      url: '${ApiConfig.baseUrl}$endpoint',
    );
  }

  static Future<String?> pickAndConvertCSVFile() async {
    try {
      const XTypeGroup typeGroup = XTypeGroup(
        label: 'CSV files',
        extensions: <String>['csv'],
      );
      
      final XFile? file = await openFile(
        acceptedTypeGroups: <XTypeGroup>[typeGroup],
      );

      if (file != null) {
        // Fájlméret ellenőrzése
        final int fileSize = await file.length();
        if (fileSize > 5 * 1024 * 1024) {
          throw Exception('A fájl túl nagy (max 5MB engedélyezett)');
        }

        // Fájl beolvasása és base64 kódolása
        final List<int> fileBytes = await file.readAsBytes();
        return base64Encode(fileBytes);
      }
      
      return null;
    } catch (e) {
      throw Exception('Hiba a fájl kiválasztásakor: $e');
    }
  }

  // CSV előnézet lekérése
  static Future<CSVPreviewResponse> getCSVPreview(String base64Data) async {
    try {
      final response = await _post(
        '$baseUrl/csv/preview',
        body: json.encode(base64Data),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        return CSVPreviewResponse.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'Hiba az előnézet lekérésekor');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Hálózati hiba: $e');
    }
  }

  // Felhasználó import adatok lekérése
  static Future<UserImportData> getUserImportData() async {
    try {
      final response = await _get('$baseUrl/csv/user-data');

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        return UserImportData.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'Hiba a felhasználói adatok lekérésekor');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Hálózati hiba: $e');
    }
  }

  // Oszlop mapping validálása
  static Future<Map<String, dynamic>> validateColumnMapping(
    List<ColumnMapping> mappings
  ) async {
    try {
      final mappingsJson = mappings.map((m) => m.toJson()).toList();
      
      final response = await _post(
        '$baseUrl/csv/validate-mapping',
        body: json.encode(mappingsJson),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'Hiba a validáláskor');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Hálózati hiba: $e');
    }
  }

  // Import végrehajtása
  static Future<ImportResult> executeImport({
    required String base64Data,
    required ImportConfiguration configuration,
  }) async {
    try {
      final requestBody = {
        'file_data': base64Data,
        'configuration': configuration.toJson(),
      };

      final response = await _post(
        '$baseUrl/csv/execute',
        body: json.encode(requestBody),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        return ImportResult.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'Hiba az import végrehajtásakor');
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Hálózati hiba: $e');
    }
  }

  // Segédfüggvény: Kötelező mezők ellenőrzése
  static List<String> validateRequiredMappings(List<ColumnMapping> mappings) {
    final errors = <String>[];
    final requiredFields = [CSVColumnType.date, CSVColumnType.amount, CSVColumnType.description];
    
    final mappedFields = mappings
        .where((m) => m.appField != CSVColumnType.ignore)
        .map((m) => m.appField)
        .toList();

    for (final requiredField in requiredFields) {
      if (!mappedFields.contains(requiredField)) {
        String fieldName;
        switch (requiredField) {
          case CSVColumnType.date:
            fieldName = 'Dátum';
            break;
          case CSVColumnType.amount:
            fieldName = 'Összeg';
            break;
          case CSVColumnType.description:
            fieldName = 'Leírás';
            break;
          default:
            fieldName = requiredField.value;
        }
        errors.add('A(z) "$fieldName" mező nincs hozzárendelve');
      }
    }

    // Duplikált mapping ellenőrzése
    final fieldCounts = <CSVColumnType, int>{};
    for (final mapping in mappings) {
      if (mapping.appField == CSVColumnType.ignore) continue;
      fieldCounts[mapping.appField] = (fieldCounts[mapping.appField] ?? 0) + 1;
    }

    fieldCounts.forEach((field, count) {
      if (count > 1) {
        errors.add('A(z) "${_getFieldDisplayName(field)}" mező többször van hozzárendelve');
      }
    });

    return errors;
  }

  // Segédfüggvény: Mező display név lekérése
  static String _getFieldDisplayName(CSVColumnType field) {
    switch (field) {
      case CSVColumnType.date:
        return 'Dátum';
      case CSVColumnType.amount:
        return 'Összeg';
      case CSVColumnType.description:
        return 'Leírás';
      case CSVColumnType.type:
        return 'Típus';
      case CSVColumnType.currency:
        return 'Deviza';
      case CSVColumnType.category:
        return 'Kategória';
      case CSVColumnType.ignore:
        return 'Kihagyás';
    }
  }

  // Segédfüggvény: CSV oszlop típus opciók lekérése
  static List<CSVColumnType> getColumnTypeOptions() {
    return CSVColumnType.values;
  }

  // Segédfüggvény: CSV oszlop típus display név
  static String getColumnTypeDisplayName(CSVColumnType type) {
    return _getFieldDisplayName(type);
  }
}