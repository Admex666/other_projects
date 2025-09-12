// lib/widgets/import_result_widget.dart

import 'package:flutter/material.dart';
import '../models/csv_import_models.dart';

class ImportResultWidget extends StatelessWidget {
  final ImportResult result;
  final VoidCallback onNewImport;

  const ImportResultWidget({
    Key? key,
    required this.result,
    required this.onNewImport,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // Fő eredmény kártya
          _buildMainResultCard(context),
          
          const SizedBox(height: 16),
          
          // Részletes statisztikák
          _buildStatisticsCard(context),
          
          if (result.hasErrors) ...[
            const SizedBox(height: 16),
            _buildErrorsCard(context),
          ],
          
          const SizedBox(height: 24),
          
          // Akciók
          _buildActionButtons(context),
        ],
      ),
    );
  }

  Widget _buildMainResultCard(BuildContext context) {
    final bool isSuccess = result.successCount > 0 && result.errorCount == 0;
    final Color primaryColor = isSuccess ? Colors.green : 
                              result.hasErrors ? Colors.red : Colors.orange;
    
    return Card(
      elevation: 4,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              primaryColor,
              primaryColor,
            ],
          ),
        ),
        child: Column(
          children: [
            Icon(
              isSuccess ? Icons.check_circle : 
              result.hasErrors ? Icons.error : Icons.warning,
              size: 64,
              color: primaryColor,
            ),
            const SizedBox(height: 16),
            Text(
              _getMainResultTitle(),
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: primaryColor,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              _getMainResultSubtitle(),
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: primaryColor,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatisticsCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.analytics,
                  color: Theme.of(context).primaryColor,
                ),
                const SizedBox(width: 8),
                Text(
                  'Import statisztika',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Statisztikai sorok
            Row(
              children: [
                Expanded(
                  child: _buildStatItem(
                    context,
                    'Sikeres',
                    result.successCount,
                    Colors.green,
                    Icons.check_circle,
                  ),
                ),
                Expanded(
                  child: _buildStatItem(
                    context,
                    'Hiba',
                    result.errorCount,
                    Colors.red,
                    Icons.error,
                  ),
                ),
                Expanded(
                  child: _buildStatItem(
                    context,
                    'Duplikátum',
                    result.duplicateCount,
                    Colors.orange,
                    Icons.content_copy,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),
            
            // Összes feldolgozott
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Összes feldolgozott:',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text(
                  '${result.totalProcessed}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(
    BuildContext context,
    String label,
    int value,
    Color color,
    IconData icon,
  ) {
    return Column(
      children: [
        Icon(
          icon,
          color: color,
          size: 32,
        ),
        const SizedBox(height: 8),
        Text(
          '$value',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildErrorsCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.warning,
                  color: Colors.red.shade600,
                ),
                const SizedBox(width: 8),
                Text(
                  'Hibák részletei',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.red.shade700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            if (result.errors.isEmpty) 
              Text(
                'Nincsenek részletes hibaüzenetek.',
                style: TextStyle(color: Colors.grey[600]),
              )
            else
              ...result.errors.take(10).map((error) => _buildErrorItem(context, error)),
            
            if (result.errors.length > 10) ...[
              const SizedBox(height: 8),
              Text(
                '... és további ${result.errors.length - 10} hiba',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildErrorItem(BuildContext context, Map<String, dynamic> error) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.red.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (error.containsKey('row_index'))
            Text(
              'Sor ${error['row_index'] + 1}:',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          const SizedBox(height: 4),
          Text(
            error['error']?.toString() ?? 
            error['general_error']?.toString() ?? 
            'Ismeretlen hiba',
            style: const TextStyle(fontSize: 12),
          ),
          if (error.containsKey('row_data')) ...[
            const SizedBox(height: 4),
            Text(
              'Adat: ${error['row_data'].toString()}',
              style: TextStyle(
                fontSize: 10,
                color: Colors.grey[600],
                fontFamily: 'monospace',
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: onNewImport,
            icon: const Icon(Icons.upload_file),
            label: const Text('Új import indítása'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              backgroundColor: Theme.of(context).primaryColor,
              foregroundColor: Colors.white,
            ),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: TextButton.icon(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.close),
            label: const Text('Bezárás'),
          ),
        ),
      ],
    );
  }

  String _getMainResultTitle() {
    if (result.successCount > 0 && result.errorCount == 0) {
      return 'Import sikeres!';
    } else if (result.errorCount > 0 && result.successCount == 0) {
      return 'Import sikertelen';
    } else if (result.errorCount > 0) {
      return 'Import részben sikeres';
    } else {
      return 'Import befejezve';
    }
  }

  String _getMainResultSubtitle() {
    if (result.successCount > 0 && result.errorCount == 0) {
      return '${result.successCount} tranzakció sikeresen importálva';
    } else if (result.errorCount > 0 && result.successCount == 0) {
      return 'Egyetlen tranzakció sem lett importálva';
    } else if (result.errorCount > 0) {
      return '${result.successCount} sikeres, ${result.errorCount} hibás';
    } else {
      return '${result.totalProcessed} tranzakció feldolgozva';
    }
  }
}