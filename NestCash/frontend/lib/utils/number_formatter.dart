// lib/utils/number_formatter.dart

import 'package:intl/intl.dart';

class NumberFormatter {
  static final NumberFormat _formatter = NumberFormat('#,##0', 'hu_HU');
  
  /// Számot formáz # ##0 formátumba (pl: 1 234 567)
  static String format(double number) {
    return _formatter.format(number.round());
  }
  
  /// Pénzösszeget formáz Ft-tal (pl: 1 234 567 Ft)
  static String formatCurrency(double amount) {
    return '${format(amount)} Ft';
  }
  
  /// Százalékot formáz (pl: 15,5%)
  static String formatPercentage(double percentage) {
    return '${percentage.toStringAsFixed(1)}%';
  }
}