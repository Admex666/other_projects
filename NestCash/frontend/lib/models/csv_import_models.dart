// lib/models/csv_import_models.dart

enum CSVColumnType {
  date('date'),
  amount('amount'),
  description('description'),
  type('type'),
  currency('currency'),
  category('category'),
  ignore('ignore');

  const CSVColumnType(this.value);
  final String value;

  static CSVColumnType fromString(String value) {
    return values.firstWhere((e) => e.value == value, orElse: () => ignore);
  }
}

class ColumnMapping {
  final String csvColumnName;
  final CSVColumnType appField;
  final bool required;

  ColumnMapping({
    required this.csvColumnName,
    required this.appField,
    required this.required,
  });

  factory ColumnMapping.fromJson(Map<String, dynamic> json) {
    return ColumnMapping(
      csvColumnName: json['csv_column_name'] as String,
      appField: CSVColumnType.fromString(json['app_field'] as String),
      required: json['required'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'csv_column_name': csvColumnName,
      'app_field': appField.value,
      'required': required,
    };
  }

  ColumnMapping copyWith({
    String? csvColumnName,
    CSVColumnType? appField,
    bool? required,
  }) {
    return ColumnMapping(
      csvColumnName: csvColumnName ?? this.csvColumnName,
      appField: appField ?? this.appField,
      required: required ?? this.required,
    );
  }
}

class CSVPreviewRow {
  final int rowIndex;
  final Map<String, dynamic> data;
  final Map<String, dynamic>? parsedData;
  final List<String> errors;

  CSVPreviewRow({
    required this.rowIndex,
    required this.data,
    this.parsedData,
    required this.errors,
  });

  factory CSVPreviewRow.fromJson(Map<String, dynamic> json) {
    return CSVPreviewRow(
      rowIndex: json['row_index'] as int,
      data: Map<String, dynamic>.from(json['data'] as Map),
      parsedData: json['parsed_data'] != null 
          ? Map<String, dynamic>.from(json['parsed_data'] as Map)
          : null,
      errors: List<String>.from(json['errors'] as List),
    );
  }

  bool get hasErrors => errors.isNotEmpty;
}

class CSVPreviewResponse {
  final List<String> headers;
  final List<CSVPreviewRow> sampleRows;
  final int totalRows;
  final List<ColumnMapping> detectedMappings;

  CSVPreviewResponse({
    required this.headers,
    required this.sampleRows,
    required this.totalRows,
    required this.detectedMappings,
  });

  factory CSVPreviewResponse.fromJson(Map<String, dynamic> json) {
    return CSVPreviewResponse(
      headers: List<String>.from(json['headers'] as List),
      sampleRows: (json['sample_rows'] as List)
          .map((row) => CSVPreviewRow.fromJson(row as Map<String, dynamic>))
          .toList(),
      totalRows: json['total_rows'] as int,
      detectedMappings: (json['detected_mappings'] as List)
          .map((mapping) => ColumnMapping.fromJson(mapping as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ImportConfiguration {
  final String mainAccount;
  final String subAccountName;
  final String? defaultCategory;
  final List<ColumnMapping> columnMappings;
  final bool skipDuplicates;
  final String dateFormat;

  ImportConfiguration({
    required this.mainAccount,
    required this.subAccountName,
    this.defaultCategory,
    required this.columnMappings,
    this.skipDuplicates = true,
    this.dateFormat = '%Y-%m-%d %H:%M:%S',
  });

  Map<String, dynamic> toJson() {
    return {
      'main_account': mainAccount,
      'sub_account_name': subAccountName,
      'default_category': defaultCategory,
      'column_mappings': columnMappings.map((m) => m.toJson()).toList(),
      'skip_duplicates': skipDuplicates,
      'date_format': dateFormat,
    };
  }
}

class ImportResult {
  final int successCount;
  final int errorCount;
  final int duplicateCount;
  final List<Map<String, dynamic>> errors;
  final List<String> importedTransactionIds;

  ImportResult({
    required this.successCount,
    required this.errorCount,
    required this.duplicateCount,
    required this.errors,
    required this.importedTransactionIds,
  });

  factory ImportResult.fromJson(Map<String, dynamic> json) {
    return ImportResult(
      successCount: json['success_count'] as int,
      errorCount: json['error_count'] as int,
      duplicateCount: json['duplicate_count'] as int,
      errors: List<Map<String, dynamic>>.from(json['errors'] as List),
      importedTransactionIds: List<String>.from(json['imported_transaction_ids'] as List),
    );
  }

  bool get hasErrors => errorCount > 0 || errors.isNotEmpty;
  int get totalProcessed => successCount + errorCount + duplicateCount;
}

class UserImportData {
  final List<String> categories;
  final Map<String, List<String>> subAccounts;
  final List<String> supportedCurrencies;

  UserImportData({
    required this.categories,
    required this.subAccounts,
    required this.supportedCurrencies,
  });

  factory UserImportData.fromJson(Map<String, dynamic> json) {
    final accounts = json['accounts'] as Map<String, dynamic>;
    final subAccountsMap = accounts['sub_accounts'] as Map<String, dynamic>;
    
    return UserImportData(
      categories: List<String>.from(json['categories'] as List),
      subAccounts: subAccountsMap.map((key, value) => 
          MapEntry(key, List<String>.from(value as List))),
      supportedCurrencies: List<String>.from(json['supported_currencies'] as List),
    );
  }

  List<String> get mainAccounts => subAccounts.keys.toList();
}