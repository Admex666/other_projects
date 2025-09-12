// lib/widgets/import_configuration_widget.dart

import 'package:flutter/material.dart';
import '../models/csv_import_models.dart';

class ImportConfigurationWidget extends StatefulWidget {
  final UserImportData userImportData;
  final List<ColumnMapping> columnMappings;
  final Function(ImportConfiguration) onConfigurationChanged;

  const ImportConfigurationWidget({
    Key? key,
    required this.userImportData,
    required this.columnMappings,
    required this.onConfigurationChanged,
  }) : super(key: key);

  @override
  State<ImportConfigurationWidget> createState() => _ImportConfigurationWidgetState();
}

class _ImportConfigurationWidgetState extends State<ImportConfigurationWidget> {
  String? _selectedMainAccount;
  String? _selectedSubAccount;
  String? _selectedDefaultCategory;
  bool _skipDuplicates = true;
  String _dateFormat = '%Y-%m-%d %H:%M:%S';

  @override
  void initState() {
    super.initState();
    // Alapértelmezett értékek beállítása
    if (widget.userImportData.mainAccounts.isNotEmpty) {
      _selectedMainAccount = widget.userImportData.mainAccounts.first;
      _updateSubAccountOptions();
    }
    if (widget.userImportData.categories.isNotEmpty) {
      _selectedDefaultCategory = widget.userImportData.categories.first;
    }
    _updateConfiguration();
  }

  void _updateSubAccountOptions() {
    if (_selectedMainAccount != null) {
      final subAccounts = widget.userImportData.subAccounts[_selectedMainAccount!] ?? [];
      if (subAccounts.isNotEmpty) {
        _selectedSubAccount = subAccounts.first;
      } else {
        _selectedSubAccount = null;
      }
    }
  }

  void _updateConfiguration() {
    if (_selectedMainAccount != null && _selectedSubAccount != null) {
      final configuration = ImportConfiguration(
        mainAccount: _selectedMainAccount!,
        subAccountName: _selectedSubAccount!,
        defaultCategory: _selectedDefaultCategory,
        columnMappings: widget.columnMappings,
        skipDuplicates: _skipDuplicates,
        dateFormat: _dateFormat,
      );
      widget.onConfigurationChanged(configuration);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Import beállítások',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            'Állítsd be az import paramétereit',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 24),

          // Főszámla kiválasztás
          _buildAccountSection(),
          
          const SizedBox(height: 24),
          
          // Kategória beállítások
          _buildCategorySection(),
          
          const SizedBox(height: 24),
          
          // Import opciók
          _buildOptionsSection(),
          
          const SizedBox(height: 24),
          
          // Összefoglaló
          _buildSummarySection(),
        ],
      ),
    );
  }

  Widget _buildAccountSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.account_balance,
                  color: Theme.of(context).primaryColor,
                ),
                const SizedBox(width: 8),
                Text(
                  'Számla beállítások',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Főszámla
            DropdownButtonFormField<String>(
              value: _selectedMainAccount,
              decoration: const InputDecoration(
                labelText: 'Főszámla',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.account_balance_wallet),
              ),
              items: widget.userImportData.mainAccounts.map((account) {
                return DropdownMenuItem(
                  value: account,
                  child: Text(_getMainAccountDisplayName(account)),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  _selectedMainAccount = value;
                  _updateSubAccountOptions();
                  _updateConfiguration();
                });
              },
            ),
            
            const SizedBox(height: 16),

            // Alszámla
            DropdownButtonFormField<String>(
              value: _selectedSubAccount,
              decoration: const InputDecoration(
                labelText: 'Alszámla',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.account_tree),
              ),
              items: _selectedMainAccount != null
                  ? (widget.userImportData.subAccounts[_selectedMainAccount!] ?? [])
                      .map((subAccount) => DropdownMenuItem(
                            value: subAccount,
                            child: Text(subAccount),
                          ))
                      .toList()
                  : [],
              onChanged: (value) {
                setState(() {
                  _selectedSubAccount = value;
                  _updateConfiguration();
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategorySection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.category,
                  color: Theme.of(context).primaryColor,
                ),
                const SizedBox(width: 8),
                Text(
                  'Kategória beállítások',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Ha a CSV-ben nincs kategória oszlop, ez lesz az alapértelmezett',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),

            DropdownButtonFormField<String>(
              value: _selectedDefaultCategory,
              decoration: const InputDecoration(
                labelText: 'Alapértelmezett kategória',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.label),
              ),
              items: [
                const DropdownMenuItem(
                  value: null,
                  child: Text('Nincs alapértelmezett'),
                ),
                ...widget.userImportData.categories.map((category) {
                  return DropdownMenuItem(
                    value: category,
                    child: Text(category),
                  );
                }),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedDefaultCategory = value;
                  _updateConfiguration();
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionsSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.settings,
                  color: Theme.of(context).primaryColor,
                ),
                const SizedBox(width: 8),
                Text(
                  'Import opciók',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Duplikátumok kihagyása
            SwitchListTile(
              title: const Text('Duplikátumok kihagyása'),
              subtitle: const Text('A már létező tranzakciók nem lesznek újra importálva'),
              value: _skipDuplicates,
              onChanged: (value) {
                setState(() {
                  _skipDuplicates = value;
                  _updateConfiguration();
                });
              },
            ),

            const Divider(),

            // Dátum formátum
            DropdownButtonFormField<String>(
              value: _dateFormat,
              decoration: const InputDecoration(
                labelText: 'Dátum formátum',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.date_range),
              ),
              items: const [
                DropdownMenuItem(
                  value: '%Y-%m-%d %H:%M:%S',
                  child: Text('YYYY-MM-DD HH:MM:SS'),
                ),
                DropdownMenuItem(
                  value: '%Y-%m-%d',
                  child: Text('YYYY-MM-DD'),
                ),
                DropdownMenuItem(
                  value: '%d/%m/%Y %H:%M:%S',
                  child: Text('DD/MM/YYYY HH:MM:SS'),
                ),
                DropdownMenuItem(
                  value: '%d/%m/%Y',
                  child: Text('DD/MM/YYYY'),
                ),
                DropdownMenuItem(
                  value: '%m/%d/%Y',
                  child: Text('MM/DD/YYYY'),
                ),
              ],
              onChanged: (value) {
                setState(() {
                  _dateFormat = value ?? '%Y-%m-%d %H:%M:%S';
                  _updateConfiguration();
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummarySection() {
    if (_selectedMainAccount == null || _selectedSubAccount == null) {
      return const SizedBox();
    }

    final mappedFields = widget.columnMappings
        .where((m) => m.appField != CSVColumnType.ignore)
        .length;

    return Card(
      color: Colors.blue.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.info,
                  color: Colors.blue.shade700,
                ),
                const SizedBox(width: 8),
                Text(
                  'Összefoglaló',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.blue.shade700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            
            _buildSummaryRow('Cél számla', '${_getMainAccountDisplayName(_selectedMainAccount!)} → $_selectedSubAccount'),
            _buildSummaryRow('Alapértelmezett kategória', _selectedDefaultCategory ?? 'Nincs beállítva'),
            _buildSummaryRow('Hozzárendelt mezők', '$mappedFields/${widget.columnMappings.length}'),
            _buildSummaryRow('Duplikátumok kezelése', _skipDuplicates ? 'Kihagyás' : 'Importálás'),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 13,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  String _getMainAccountDisplayName(String account) {
    switch (account) {
      case 'likvid':
        return 'Likvid eszközök';
      case 'befektetes':
        return 'Befektetések';
      case 'megtakaritas':
        return 'Megtakarítások';
      default:
        return account;
    }
  }
}