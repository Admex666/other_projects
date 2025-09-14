// lib/services/csv_import_service.dart

import 'dart:async';
import 'dart:convert';
import 'package:file_selector/file_selector.dart';
import 'package:http/http.dart' as http;
import '../models/csv_import_models.dart';
import '../config/config.dart';
import '../services/http_service.dart';
import 'package:easy_localization/easy_localization.dart';

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
    print('DEBUG CSV: Starting file selection');

    try {
      const XTypeGroup typeGroup = XTypeGroup(
        label: 'CSV files',
        extensions: <String>['csv'],
      );

      print('DEBUG CSV: About to call openFile');
      final XFile? file = await openFile(
        acceptedTypeGroups: <XTypeGroup>[typeGroup],
      );
      print('DEBUG CSV: openFile completed, file: ${file?.name}');

      if (file != null) {
        print('DEBUG CSV: File selected, checking size...');
        final int fileSize = await file.length();
        print('DEBUG CSV: File size: $fileSize bytes');

        if (fileSize > 1024 * 1024) { // 1MB
          throw Exception('csvi_service.file_too_large'.tr(namedArgs: {'size': fileSize.toString()}));
        }

        print('DEBUG CSV: Starting to read file content...');
        // Próbáljunk csak string olvasást, base64 nélkül
        final String content = await file.readAsString();
        print('DEBUG CSV: File read completed, content length: ${content.length} chars');

        print('DEBUG CSV: Starting base64 encoding...');
        final String base64Data = base64Encode(utf8.encode(content));
        print('DEBUG CSV: Base64 encoding completed, length: ${base64Data.length}');

        return base64Data;
      } else {
        print('DEBUG CSV: No file selected');
        return null;
      }

    } catch (e, stackTrace) {
      print('DEBUG CSV: ERROR occurred: $e');
      print('DEBUG CSV: Stack trace: $stackTrace');
      throw Exception('csvi_service.file_selection_error'.tr(namedArgs: {'error': e.toString()}));
    }
  }

  // CSV előnézet lekérése
  static Future<CSVPreviewResponse> getCSVPreview(String base64Data) async {
    print('DEBUG API: getCSVPreview started, data length: ${base64Data.length}');

    try {
      print('DEBUG API: About to make HTTP request');

      final response = await HttpService.authenticatedRequest(
        method: 'POST',
        url: '${ApiConfig.baseUrl}$baseUrl/csv/preview',
        body: {'file_data': base64Data},
      ).timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          print('DEBUG API: Request timed out');
          throw TimeoutException('csvi_service.request_timeout'.tr(namedArgs: {'duration': '30'}));
        },
      );

      print('DEBUG API: HTTP request completed, status: ${response.statusCode}');

      if (response.statusCode == 200) {
        print('DEBUG API: Response successful, parsing JSON');
        final Map<String, dynamic> jsonData = json.decode(response.body);
        print('DEBUG API: JSON parsed successfully');
        return CSVPreviewResponse.fromJson(jsonData);
      } else {
        print('DEBUG API: HTTP error: ${response.statusCode}, body: ${response.body}');
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'csvi_service.preview_error'.tr());
      }
    } on TimeoutException catch (e) {
      print('DEBUG API: Timeout exception: $e');
      throw Exception('csvi_service.request_timeout_short'.tr());
    } catch (e) {
      print('DEBUG API: General exception: $e');
      if (e is Exception) rethrow;
      throw Exception('csvi_service.network_error'.tr(namedArgs: {'error': e.toString()}));
    }
  }

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
      ).timeout(
        const Duration(seconds: 60), // 60 másodperc az importhoz
        onTimeout: () {
          throw TimeoutException('csvi_service.import_timeout'.tr(namedArgs: {'duration': '60'}));
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        return ImportResult.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'csvi_service.import_execute_error'.tr());
      }
    } on TimeoutException {
      throw Exception('csvi_service.import_timeout_short'.tr());
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('csvi_service.network_error'.tr(namedArgs: {'error': e.toString()}));
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
        throw Exception(errorData['detail'] ?? 'csvi_service.user_data_error'.tr());
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('csvi_service.network_error'.tr(namedArgs: {'error': e.toString()}));
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
        throw Exception(errorData['detail'] ?? 'csvi_service.validation_error'.tr());
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('csvi_service.network_error'.tr(namedArgs: {'error': e.toString()}));
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
        String fieldName = _getFieldDisplayName(requiredField);
        errors.add('csvi_service.missing_field'.tr(namedArgs: {'field': fieldName}));
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
        errors.add('csvi_service.duplicate_field'.tr(namedArgs: {'field': _getFieldDisplayName(field)}));
      }
    });

    return errors;
  }

  // Segédfüggvény: Mező display név lekérése
  static String _getFieldDisplayName(CSVColumnType field) {
    switch (field) {
      case CSVColumnType.date:
        return 'csvi_service.date'.tr();
      case CSVColumnType.amount:
        return 'csvi_service.amount'.tr();
      case CSVColumnType.description:
        return 'csvi_service.description'.tr();
      case CSVColumnType.type:
        return 'csvi_service.type'.tr();
      case CSVColumnType.currency:
        return 'csvi_service.currency'.tr();
      case CSVColumnType.category:
        return 'csvi_service.category'.tr();
      case CSVColumnType.ignore:
        return 'csvi_service.ignore'.tr();
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