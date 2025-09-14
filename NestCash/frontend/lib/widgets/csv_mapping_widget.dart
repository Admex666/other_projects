// lib/widgets/csv_mapping_widget.dart

import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../models/csv_import_models.dart';
import '../services/csv_import_service.dart';

class CSVMappingWidget extends StatefulWidget {
  final List<ColumnMapping> mappings;
  final Function(List<ColumnMapping>) onMappingChanged;

  const CSVMappingWidget({
    Key? key,
    required this.mappings,
    required this.onMappingChanged,
  }) : super(key: key);

  @override
  State<CSVMappingWidget> createState() => _CSVMappingWidgetState();
}

class _CSVMappingWidgetState extends State<CSVMappingWidget> {
  List<ColumnMapping> _mappings = [];
  List<String> _validationErrors = [];

  @override
  void initState() {
    super.initState();
    _mappings = List.from(widget.mappings);
    _validateMappings();
  }

  @override
  void didUpdateWidget(CSVMappingWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.mappings != widget.mappings) {
      _mappings = List.from(widget.mappings);
      _validateMappings();
    }
  }

  void _validateMappings() {
    setState(() {
      _validationErrors = CSVImportService.validateRequiredMappings(_mappings);
    });
  }

  void _updateMapping(int index, CSVColumnType newType) {
    setState(() {
      _mappings[index] = _mappings[index].copyWith(appField: newType);
      _validateMappings();
    });
    widget.onMappingChanged(_mappings);
  }

  @override
  Widget build(BuildContext context) {
    return Card(
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
                      Icons.map,
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'csvi_widget_map.title'.tr(),
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'csvi_widget_map.description'.tr(),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          
          if (_validationErrors.isNotEmpty) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: Colors.red.shade50,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.error,
                        color: Colors.red.shade700,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'csvi_widget_map.errors_title'.tr(),
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.red.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ..._validationErrors.map((error) => Padding(
                    padding: const EdgeInsets.only(left: 28, bottom: 4),
                    child: Text(
                      '• $error',
                      style: TextStyle(
                        color: Colors.red.shade700,
                        fontSize: 12,
                      ),
                    ),
                  )),
                ],
              ),
            ),
          ],

          const Divider(height: 1),

          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                // Header sor
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: Text(
                          'csvi_widget_map.csv_column_header'.tr(),
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        flex: 2,
                        child: Text(
                          'csvi_widget_map.app_field_header'.tr(),
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                      ),
                      const SizedBox(width: 16),
                      SizedBox(
                        width: 80,
                        child: Text(
                          'csvi_widget_map.required_header'.tr(),
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const Divider(),
                
                // Mapping sorok
                ..._mappings.asMap().entries.map((entry) {
                  final index = entry.key;
                  final mapping = entry.value;
                  
                  return _buildMappingRow(context, index, mapping);
                }).toList(),
              ],
            ),
          ),
          
          // Gyors beállítások
          const Divider(),
          _buildQuickActions(context),
        ],
      ),
    );
  }

  Widget _buildMappingRow(BuildContext context, int index, ColumnMapping mapping) {
    final isRequired = [
      CSVColumnType.date,
      CSVColumnType.amount,
      CSVColumnType.description
    ].contains(mapping.appField);

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: isRequired ? Colors.blue.shade50 : null,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          // CSV oszlop neve
          Expanded(
            flex: 2,
            child: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                mapping.csvColumnName,
                style: const TextStyle(fontWeight: FontWeight.w500),
              ),
            ),
          ),
          
          const SizedBox(width: 16),
          
          // App mező dropdown
          Expanded(
            flex: 2,
            child: DropdownButtonFormField<CSVColumnType>(
              value: mapping.appField,
              decoration: InputDecoration(
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(4),
                ),
                filled: true,
                fillColor: isRequired ? Colors.blue.shade50 : null,
              ),
              items: CSVColumnType.values.map((type) => DropdownMenuItem(
                value: type,
                child: Row(
                  children: [
                    Icon(
                      _getFieldIcon(type),
                      size: 16,
                      color: _getFieldColor(type),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        CSVImportService.getColumnTypeDisplayName(type),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              )).toList(),
              onChanged: (newType) {
                if (newType != null) {
                  _updateMapping(index, newType);
                }
              },
            ),
          ),
          
          const SizedBox(width: 16),
          
          // Kötelező indikátor
          SizedBox(
            width: 80,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isRequired) ...[
                  Icon(
                    Icons.star,
                    color: Colors.orange.shade600,
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                ],
                Text(
                  isRequired ? 'csvi_widget_map.required_yes'.tr() : 'csvi_widget_map.required_no'.tr(),
                  style: TextStyle(
                    color: isRequired ? Colors.orange.shade700 : Colors.grey.shade600,
                    fontWeight: isRequired ? FontWeight.w500 : FontWeight.normal,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'csvi_widget_map.quick_actions_title'.tr(),
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _buildQuickActionChip(
                'csvi_widget_map.revolut_format'.tr(),
                Icons.account_balance,
                () => _applyRevolutMapping(),
              ),
              _buildQuickActionChip(
                'csvi_widget_map.skip_all'.tr(),
                Icons.clear_all,
                () => _setAllToIgnore(),
              ),
              _buildQuickActionChip(
                'csvi_widget_map.auto_mapping'.tr(),
                Icons.auto_fix_high,
                () => _applyAutoMapping(),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionChip(String label, IconData icon, VoidCallback onPressed) {
    return ActionChip(
      avatar: Icon(icon, size: 16),
      label: Text(label),
      onPressed: onPressed,
      backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
    );
  }

  void _applyRevolutMapping() {
    final revolutMappings = {
      'Description': CSVColumnType.description,
      'Amount': CSVColumnType.amount,
      'Currency': CSVColumnType.currency,
      'Type': CSVColumnType.type,
      'Started Date': CSVColumnType.date,
      'Completed Date': CSVColumnType.date,
    };

    setState(() {
      for (int i = 0; i < _mappings.length; i++) {
        final csvColumn = _mappings[i].csvColumnName;
        if (revolutMappings.containsKey(csvColumn)) {
          _mappings[i] = _mappings[i].copyWith(
            appField: revolutMappings[csvColumn]!,
          );
        } else {
          _mappings[i] = _mappings[i].copyWith(
            appField: CSVColumnType.ignore,
          );
        }
      }
      _validateMappings();
    });
    widget.onMappingChanged(_mappings);
  }

  void _setAllToIgnore() {
    setState(() {
      for (int i = 0; i < _mappings.length; i++) {
        _mappings[i] = _mappings[i].copyWith(appField: CSVColumnType.ignore);
      }
      _validateMappings();
    });
    widget.onMappingChanged(_mappings);
  }

  void _applyAutoMapping() {
    // Ez már meg van csinálva a backend által, visszaállítjuk az eredetit
    setState(() {
      _mappings = List.from(widget.mappings);
      _validateMappings();
    });
    widget.onMappingChanged(_mappings);
  }

  IconData _getFieldIcon(CSVColumnType type) {
    switch (type) {
      case CSVColumnType.date:
        return Icons.calendar_today;
      case CSVColumnType.amount:
        return Icons.attach_money;
      case CSVColumnType.description:
        return Icons.description;
      case CSVColumnType.type:
        return Icons.category;
      case CSVColumnType.currency:
        return Icons.monetization_on;
      case CSVColumnType.category:
        return Icons.label;
      case CSVColumnType.ignore:
        return Icons.block;
    }
  }

  Color _getFieldColor(CSVColumnType type) {
    switch (type) {
      case CSVColumnType.date:
        return Colors.blue;
      case CSVColumnType.amount:
        return Colors.green;
      case CSVColumnType.description:
        return Colors.orange;
      case CSVColumnType.type:
        return Colors.purple;
      case CSVColumnType.currency:
        return Colors.teal;
      case CSVColumnType.category:
        return Colors.indigo;
      case CSVColumnType.ignore:
        return Colors.grey;
    }
  }
}