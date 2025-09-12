// lib/screens/csv_import_screen.dart

import 'package:flutter/material.dart';
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
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final base64Data = await CSVImportService.pickAndConvertCSVFile();
      
      if (base64Data != null) {
        final preview = await CSVImportService.getCSVPreview(base64Data);
        
        setState(() {
          _base64FileData = base64Data;
          _csvPreview = preview;
          _columnMappings = List.from(preview.detectedMappings);
          _isLoading = false;
        });
        
        _nextStep();
      } else {
        setState(() {
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _nextStep() {
    if (_currentStep < 3) {
      setState(() {
        _currentStep++;
      });
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  void _previousStep() {
    if (_currentStep > 0) {
      setState(() {
        _currentStep--;
      });
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  void _onMappingChanged(List<ColumnMapping> mappings) {
    setState(() {
      _columnMappings = mappings;
    });
  }

  void _onConfigurationChanged(ImportConfiguration configuration) {
    setState(() {
      _importConfiguration = configuration;
    });
  }

  Future<void> _executeImport() async {
    if (_base64FileData == null || _importConfiguration == null) {
      setState(() {
        _error = 'Hiányos adatok az import végrehajtásához';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final result = await CSVImportService.executeImport(
        base64Data: _base64FileData!,
        configuration: _importConfiguration!,
      );
      
      setState(() {
        _importResult = result;
        _isLoading = false;
      });
      
      _nextStep();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
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
    _pageController.animateToPage(
      0,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CSV Import'),
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
    return PageView(
      controller: _pageController,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        _buildFileSelectionStep(),
        _buildMappingStep(),
        _buildConfigurationStep(),
        _buildResultStep(),
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
            'CSV fájl kiválasztása',
            style: Theme.of(context).textTheme.headlineSmall,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            'Válassz ki egy CSV fájlt a tranzakciók importálásához.\nMaximum fájlméret: 5MB',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: _pickCSVFile,
            icon: const Icon(Icons.file_upload),
            label: const Text('Fájl kiválasztása'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMappingStep() {
    if (_csvPreview == null) {
      return const Center(child: Text('Nincs CSV adat'));
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'Oszlop hozzárendelés',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
        ),
        Expanded(
          child: CSVPreviewWidget(
            preview: _csvPreview!,
          ),
        ),
        Container(
          padding: const EdgeInsets.all(16),
          child: CSVMappingWidget(
            mappings: _columnMappings,
            onMappingChanged: _onMappingChanged,
          ),
        ),
      ],
    );
  }

  Widget _buildConfigurationStep() {
    if (_userImportData == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return ImportConfigurationWidget(
      userImportData: _userImportData!,
      columnMappings: _columnMappings,
      onConfigurationChanged: _onConfigurationChanged,
    );
  }

  Widget _buildResultStep() {
    if (_importResult == null) {
      return const Center(child: Text('Nincs import eredmény'));
    }

    return ImportResultWidget(
      result: _importResult!,
      onNewImport: _resetImport,
    );
  }

  Widget _buildNavigationButtons() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          if (_currentStep > 0 && _currentStep < 3)
            TextButton(
              onPressed: _previousStep,
              child: const Text('Vissza'),
            )
          else
            const SizedBox(),
          
          if (_currentStep < 2)
            ElevatedButton(
              onPressed: _canProceedToNextStep() ? _nextStep : null,
              child: const Text('Tovább'),
            )
          else if (_currentStep == 2)
            ElevatedButton(
              onPressed: _canExecuteImport() ? _executeImport : null,
              child: const Text('Import indítása'),
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