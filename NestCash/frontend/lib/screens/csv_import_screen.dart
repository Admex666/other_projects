// lib/screens/csv_import_screen.dart

import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../models/csv_import_models.dart';
import '../services/csv_import_service.dart';
import '../widgets/csv_mapping_widget.dart';
import '../widgets/csv_preview_widget.dart';
import '../widgets/import_configuration_widget.dart';
import '../widgets/import_result_widget.dart';

class CSVImportScreen extends StatefulWidget {
  const CSVImportScreen({Key? key}) : super(key: key);

  @override
  State<CSVImportScreen> createState() => _CSVImportScreenState();
}

class _CSVImportScreenState extends State<CSVImportScreen> {
  final PageController _pageController = PageController();
  
  // Import állapot
  int _currentStep = 0;
  bool _isLoading = false;
  String? _error;
  
  // Import adatok
  String? _base64FileData;
  CSVPreviewResponse? _csvPreview;
  UserImportData? _userImportData;
  List<ColumnMapping> _columnMappings = [];
  ImportConfiguration? _importConfiguration;
  ImportResult? _importResult;

  @override
  void initState() {
    super.initState();
    _loadUserImportData();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _loadUserImportData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final userData = await CSVImportService.getUserImportData();
      setState(() {
        _userImportData = userData;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _pickCSVFile() async {
    print('DEBUG SCREEN: _pickCSVFile started');
    
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      print('DEBUG SCREEN: About to call pickAndConvertCSVFile');
      final base64Data = await CSVImportService.pickAndConvertCSVFile();
      print('DEBUG SCREEN: pickAndConvertCSVFile completed');
      
      if (base64Data != null && mounted) {
        print('DEBUG SCREEN: Got base64 data, length: ${base64Data.length}');
        
        setState(() {
          _base64FileData = base64Data;
          _isLoading = false;
        });
        
        print('DEBUG SCREEN: State updated successfully');
        
        // Most teszteljük a preview hívást
        print('DEBUG SCREEN: About to call getCSVPreview');
        
        try {
          final preview = await CSVImportService.getCSVPreview(base64Data);
          print('DEBUG SCREEN: getCSVPreview completed, rows: ${preview.sampleRows.length}');
          
          setState(() {
            _csvPreview = preview;
            _columnMappings = List.from(preview.detectedMappings);
          });
          
          print('DEBUG SCREEN: Preview state updated, calling _nextStep');
          _nextStep();
          
        } catch (previewError) {
          print('DEBUG SCREEN: Preview error: $previewError');
          setState(() {
            _error = 'csvi_screen.preview_error'.tr(namedArgs: {'error': previewError.toString()});
          });
        }
        
      } else if (mounted) {
        print('DEBUG SCREEN: No data received or widget unmounted');
        setState(() {
          _isLoading = false;
        });
      }
    } catch (e, stackTrace) {
      print('DEBUG SCREEN: Error occurred: $e');
      print('DEBUG SCREEN: Stack trace: $stackTrace');
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _nextStep() {
    print('DEBUG NAVIGATION: _nextStep called, current step: $_currentStep');
    
    if (_currentStep < 3) {
      final newStep = _currentStep + 1;
      print('DEBUG NAVIGATION: Updating current step to $newStep');
      setState(() {
        _currentStep = newStep;
      });
      
      print('DEBUG NAVIGATION: State updated, current step now: $_currentStep');
      
      // Abszolút pozícióra ugrás a nextPage helyett
      WidgetsBinding.instance.addPostFrameCallback((_) {
        print('DEBUG NAVIGATION: PostFrameCallback called');
        print('DEBUG NAVIGATION: PageController hasClients: ${_pageController.hasClients}');
        
        if (_pageController.hasClients) {
          print('DEBUG NAVIGATION: About to animateToPage: $_currentStep');
          try {
            _pageController.animateToPage(
              _currentStep,  // Abszolút pozíció
              duration: const Duration(milliseconds: 300),
              curve: Curves.easeInOut,
            );
            print('DEBUG NAVIGATION: animateToPage call completed');
          } catch (e) {
            print('DEBUG NAVIGATION: Error in animateToPage: $e');
          }
        } else {
          print('DEBUG NAVIGATION: PageController does not have clients');
        }
      });
    } else {
      print('DEBUG NAVIGATION: Already at max step ($_currentStep)');
    }
  }

  void _previousStep() {
    if (_currentStep > 0) {
      final newStep = _currentStep - 1;
      setState(() {
        _currentStep = newStep;
      });
      
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_pageController.hasClients) {
          _pageController.animateToPage(
            _currentStep,  // Abszolút pozíció
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          );
        }
      });
    }
  }

  void _onMappingChanged(List<ColumnMapping> mappings) {
    setState(() {
      _columnMappings = mappings;
    });
  }

  void _onConfigurationChanged(ImportConfiguration configuration) {
    print('DEBUG SCREEN: Configuration changed');
    print('DEBUG SCREEN: Main account: ${configuration.mainAccount}');
    print('DEBUG SCREEN: Sub account: ${configuration.subAccountName}');
    
    // Késleltetett setState a build ciklus után
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        setState(() {
          _importConfiguration = configuration;
        });
        print('DEBUG SCREEN: Configuration state updated');
      }
    });
  }

  Future<void> _executeImport() async {
    print('DEBUG SCREEN: _executeImport started');
    print('DEBUG SCREEN: _base64FileData is null: ${_base64FileData == null}');
    print('DEBUG SCREEN: _importConfiguration is null: ${_importConfiguration == null}');
    
    if (_base64FileData == null || _importConfiguration == null) {
      setState(() {
        _error = 'csvi_screen.missing_data_error'.tr();
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      print('DEBUG SCREEN: About to call executeImport');
      
      final result = await CSVImportService.executeImport(
        base64Data: _base64FileData!,
        configuration: _importConfiguration!,
      );
      
      print('DEBUG SCREEN: executeImport completed');
      print('DEBUG SCREEN: Success count: ${result.successCount}');
      print('DEBUG SCREEN: Error count: ${result.errorCount}');
      
      if (mounted) {
        setState(() {
          _importResult = result;
          _isLoading = false;
        });
        
        print('DEBUG SCREEN: Import result saved, about to go to results page');
        // Most már hívhatjuk a _nextStep()-et, mert van eredmény
        _nextStep();
      }
    } catch (e) {
      print('DEBUG SCREEN: executeImport error: $e');
      if (mounted) {
        setState(() {
          _error = 'csvi_screen.execute_import_error'.tr(namedArgs: {'error': e.toString()});
          _isLoading = false;
        });
      }
    }
  }

  void _resetImport() {
    setState(() {
      _currentStep = 0;
      _base64FileData = null;
      _csvPreview = null;
      _columnMappings.clear();
      _importConfiguration = null;
      _importResult = null;
      _error = null;
    });
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_pageController.hasClients) {
        _pageController.animateToPage(  // animateToPage helyett nextPage
          0,  // Első oldalra
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('csvi_screen.title'.tr()),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Column(
        children: [
          // Progress indicator
          _buildProgressIndicator(),
          
          // Error display
          if (_error != null) _buildErrorBanner(),
          
          // Main content
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _buildStepContent(),
          ),
          
          // Navigation buttons
          _buildNavigationButtons(),
        ],
      ),
    );
  }

  Widget _buildProgressIndicator() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          for (int i = 0; i < 4; i++) ...[
            CircleAvatar(
              radius: 16,
              backgroundColor: i <= _currentStep 
                  ? Theme.of(context).primaryColor
                  : Colors.grey.shade300,
              child: Text(
                '${i + 1}',
                style: TextStyle(
                  color: i <= _currentStep ? Colors.white : Colors.grey.shade600,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            if (i < 3) Expanded(
              child: Container(
                height: 2,
                color: i < _currentStep 
                    ? Theme.of(context).primaryColor
                    : Colors.grey.shade300,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildErrorBanner() {
    return Container(
      width: double.infinity,
      color: Colors.red.shade100,
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Icon(Icons.error, color: Colors.red.shade700),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _error!,
              style: TextStyle(color: Colors.red.shade700),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close),
            color: Colors.red.shade700,
            onPressed: () => setState(() => _error = null),
          ),
        ],
      ),
    );
  }

  Widget _buildStepContent() {
    print('DEBUG WIDGET: _buildStepContent called, current step: $_currentStep');
    print('DEBUG WIDGET: PageView should show index: $_currentStep');
    
    return PageView(
      controller: _pageController,
      physics: const NeverScrollableScrollPhysics(),
      onPageChanged: (index) {
        print('DEBUG WIDGET: PageView onPageChanged to index: $index (expected: $_currentStep)');
      },
      children: [
        _buildFileSelectionStep(),    // index 0
        _buildMappingStep(),          // index 1  
        _buildConfigurationStep(),    // index 2
        _buildResultStep(),           // index 3
      ],
    );
  }

  Widget _buildFileSelectionStep() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.file_upload,
            size: 80,
            color: Theme.of(context).primaryColor,
          ),
          const SizedBox(height: 24),
          Text(
            'csvi_screen.select_file_title'.tr(),
            style: Theme.of(context).textTheme.headlineSmall,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            'csvi_screen.select_file_description'.tr(),
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: _pickCSVFile,
            icon: const Icon(Icons.file_upload),
            label: Text('csvi_screen.select_file_button'.tr()),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  List<String> _getValidationErrors() {
    return CSVImportService.validateRequiredMappings(_columnMappings);
  }

  Widget _buildMappingStep() {
    print('DEBUG WIDGET: _buildMappingStep called (enhanced safe version)');
    
    if (_csvPreview == null) {
      return Center(child: Text('csvi_screen.no_csv_data'.tr()));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'csvi_screen.preview_mapping_title'.tr(),
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 16),
          
          // Fájl információ
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('csvi_screen.file_info'.tr(), style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text('csvi_screen.columns_count'.tr(namedArgs: {'count': _csvPreview!.headers.length.toString()})),
                  Text('csvi_screen.rows_count'.tr(namedArgs: {'count': _csvPreview!.totalRows.toString()})),
                  const SizedBox(height: 12),
                  Text('csvi_screen.first_row_sample'.tr(), style: Theme.of(context).textTheme.titleSmall),
                  if (_csvPreview!.sampleRows.isNotEmpty)
                    ..._csvPreview!.headers.take(5).map((header) { // Max 5 oszlop
                      final value = _csvPreview!.sampleRows.first.data[header]?.toString() ?? '';
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Text('• $header: ${value.length > 30 ? value.substring(0, 30) + '...' : value}'),
                      );
                    }).toList(),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Oszlop hozzárendelések
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'csvi_screen.column_mappings'.tr(),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 16),
                  
                  // Mapping lista dropdown-okkal
                  ..._columnMappings.asMap().entries.map((entry) {
                    final index = entry.key;
                    final mapping = entry.value;
                    
                    return Container(
                      margin: const EdgeInsets.symmetric(vertical: 8),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'csvi_screen.csv_column'.tr(namedArgs: {'column_name': mapping.csvColumnName}),
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<CSVColumnType>(
                            value: mapping.appField,
                            decoration: InputDecoration(
                              labelText: 'csvi_screen.mapping_label'.tr(),
                              border: const OutlineInputBorder(),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            ),
                            items: CSVColumnType.values.map((type) => DropdownMenuItem(
                              value: type,
                              child: Text(CSVImportService.getColumnTypeDisplayName(type)),
                            )).toList(),
                            onChanged: (newType) {
                              if (newType != null) {
                                setState(() {
                                  _columnMappings[index] = mapping.copyWith(appField: newType);
                                });
                                _onMappingChanged(_columnMappings);
                              }
                            },
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Validációs hibák megjelenítése
          if (_getValidationErrors().isNotEmpty)
            Card(
              color: Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.error, color: Colors.red.shade700),
                        const SizedBox(width: 8),
                        Text(
                          'csvi_screen.errors_title'.tr(),
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.red.shade700,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ..._getValidationErrors().map((error) => Text(
                      '• $error',
                      style: TextStyle(color: Colors.red.shade700),
                    )),
                  ],
                ),
              ),
            ),
          
          const SizedBox(height: 24),
          
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _getValidationErrors().isEmpty ? () {
                print('DEBUG: Manual next step with valid mappings');
                _nextStep();
              } : null,
              child: Text('csvi_screen.next_to_config_button'.tr()),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConfigurationStep() {
    print('DEBUG WIDGET: _buildConfigurationStep called');
    print('DEBUG WIDGET: _userImportData is null: ${_userImportData == null}');
    
    if (_userImportData == null) {
      print('DEBUG WIDGET: Returning CircularProgressIndicator for configuration');
      return const Center(child: CircularProgressIndicator());
    }

    print('DEBUG WIDGET: About to create ImportConfigurationWidget');
    
    try {
      return ImportConfigurationWidget(
        userImportData: _userImportData!,
        columnMappings: _columnMappings,
        onConfigurationChanged: _onConfigurationChanged,
      );
    } catch (e) {
      print('DEBUG WIDGET: Error creating ImportConfigurationWidget: $e');
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error, color: Colors.red),
            SizedBox(height: 8),
            Text('csvi_screen.config_load_error'.tr(namedArgs: {'error': e.toString()})),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => setState(() {}),
              child: Text('csvi_screen.retry_button'.tr()),
            ),
          ],
        ),
      );
    }
  }

  Widget _buildResultStep() {
    print('DEBUG WIDGET: _buildResultStep called');
    print('DEBUG WIDGET: _importResult is null: ${_importResult == null}');
    
    if (_importResult == null) {
      print('DEBUG WIDGET: No import result, showing placeholder');
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text('csvi_screen.loading_result'.tr()),
          ],
        ),
      );
    }

    print('DEBUG WIDGET: Import result available, creating result widget');
    return ImportResultWidget(
      result: _importResult!,
      onNewImport: () {
        _resetImport();
      },
    );
  }

  Widget _buildNavigationButtons() {
    print('DEBUG NAV: Building navigation buttons, current step: $_currentStep');
    print('DEBUG NAV: _canProceedToNextStep: ${_canProceedToNextStep()}');
    print('DEBUG NAV: _canExecuteImport: ${_canExecuteImport()}');
    
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          if (_currentStep > 0 && _currentStep < 3)
            TextButton(
              onPressed: _previousStep,
              child: Text('csvi_screen.back_button'.tr()),
            )
          else
            const SizedBox(),
          
          if (_currentStep < 2)
            ElevatedButton(
              onPressed: _canProceedToNextStep() ? _nextStep : null,
              child: Text('csvi_screen.next_button'.tr()),
            )
          else if (_currentStep == 2)
            ElevatedButton(
              onPressed: _canExecuteImport() ? () {
                print('DEBUG NAV: Execute import button pressed');
                _executeImport();
              } : null,
              child: Text('csvi_screen.start_import_button'.tr()),
            )
          else
            const SizedBox(),
        ],
      ),
    );
  }

  bool _canProceedToNextStep() {
    switch (_currentStep) {
      case 0:
        return _csvPreview != null;
      case 1:
        final errors = CSVImportService.validateRequiredMappings(_columnMappings);
        return errors.isEmpty;
      default:
        return false;
    }
  }

  bool _canExecuteImport() {
    return _importConfiguration != null && 
           _base64FileData != null &&
           CSVImportService.validateRequiredMappings(_columnMappings).isEmpty;
  }
}