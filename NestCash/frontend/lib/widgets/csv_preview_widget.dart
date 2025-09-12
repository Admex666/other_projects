// lib/widgets/csv_preview_widget.dart

import 'package:flutter/material.dart';
import '../models/csv_import_models.dart';

class CSVPreviewWidget extends StatelessWidget {
  final CSVPreviewResponse preview;

  const CSVPreviewWidget({
    Key? key,
    required this.preview,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.table_chart,
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'CSV Előnézet',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Összesen ${preview.totalRows} sor, '
                  'ebből ${preview.sampleRows.length} minta',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          
          const Divider(height: 1),
          
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: SingleChildScrollView(
                child: _buildDataTable(context),
              ),
            ),
          ),
          
          if (_hasErrors()) ...[
            const Divider(height: 1),
            _buildErrorSummary(context),
          ],
        ],
      ),
    );
  }

  Widget _buildDataTable(BuildContext context) {
    return DataTable(
      headingRowColor: MaterialStateProperty.all(
        Theme.of(context).colorScheme.surfaceVariant,
      ),
      columns: preview.headers.map((header) => DataColumn(
        label: Container(
          constraints: const BoxConstraints(maxWidth: 150),
          child: Text(
            header,
            style: const TextStyle(fontWeight: FontWeight.bold),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      )).toList(),
      rows: preview.sampleRows.map((row) => DataRow(
        color: row.hasErrors 
            ? MaterialStateProperty.all(Colors.red.shade50)
            : null,
        cells: preview.headers.map((header) {
          final cellValue = row.data[header]?.toString() ?? '';
          final parsedValue = row.parsedData?[_getFieldKey(header)]?.toString();
          
          return DataCell(
            Container(
              constraints: const BoxConstraints(maxWidth: 150),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    cellValue,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12),
                  ),
                  if (parsedValue != null && parsedValue != cellValue)
                    Text(
                      '→ $parsedValue',
                      style: TextStyle(
                        fontSize: 10,
                        color: Colors.green.shade600,
                        fontStyle: FontStyle.italic,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                ],
              ),
            ),
          );
        }).toList(),
      )).toList(),
    );
  }

  String _getFieldKey(String header) {
    final mapping = preview.detectedMappings.firstWhere(
      (m) => m.csvColumnName == header,
      orElse: () => ColumnMapping(
        csvColumnName: header,
        appField: CSVColumnType.ignore,
        required: false,
      ),
    );
    return mapping.appField.value;
  }

  bool _hasErrors() {
    return preview.sampleRows.any((row) => row.hasErrors);
  }

  Widget _buildErrorSummary(BuildContext context) {
    final errorsCount = preview.sampleRows.where((row) => row.hasErrors).length;
    final allErrors = preview.sampleRows
        .where((row) => row.hasErrors)
        .expand((row) => row.errors)
        .toSet()
        .toList();

    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.warning,
                color: Colors.orange.shade700,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'Figyelmeztetések ($errorsCount/${preview.sampleRows.length} sorban)',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.orange.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...allErrors.take(5).map((error) => Padding(
            padding: const EdgeInsets.only(left: 28, bottom: 4),
            child: Text(
              '• $error',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey.shade700,
              ),
            ),
          )),
          if (allErrors.length > 5)
            Padding(
              padding: const EdgeInsets.only(left: 28),
              child: Text(
                '... és további ${allErrors.length - 5} hiba',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade600,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
        ],
      ),
    );
  }
}