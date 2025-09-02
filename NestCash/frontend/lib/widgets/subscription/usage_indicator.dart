import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../../models/subscription.dart';

class UsageIndicator extends StatelessWidget {
  final String featureName;
  final int current;
  final int? limit; // null = unlimited
  final VoidCallback? onUpgradePressed;
  final bool showUpgradeButton;
  final Color? color;

  const UsageIndicator({
    super.key,
    required this.featureName,
    required this.current,
    this.limit,
    this.onUpgradePressed,
    this.showUpgradeButton = true,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isUnlimited = limit == null;
    final isAtLimit = !isUnlimited && current >= limit!;
    final percentage = isUnlimited ? 0.0 : (current / limit!).clamp(0.0, 1.0);
    
    final indicatorColor = color ?? _getColorByPercentage(percentage);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isAtLimit ? Colors.red.withOpacity(0.3) : Colors.grey.withOpacity(0.2),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  featureName,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
              ),
              
              // Usage count
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: indicatorColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isUnlimited ? '$current' : '$current/${limit!}',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: indicatorColor,
                  ),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          
          // Progress bar
          if (!isUnlimited) ...[
            Container(
              height: 6,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(3),
              ),
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: percentage,
                child: Container(
                  decoration: BoxDecoration(
                    color: indicatorColor,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
          ],
          
          // Status text
          Row(
            children: [
              Icon(
                isUnlimited 
                  ? Icons.all_inclusive
                  : isAtLimit 
                    ? Icons.warning_amber
                    : Icons.check_circle_outline,
                size: 16,
                color: isUnlimited 
                  ? Colors.blue
                  : isAtLimit 
                    ? Colors.red
                    : Colors.green,
              ),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  isUnlimited 
                    ? 'unlimited_usage'.tr()
                    : isAtLimit 
                      ? 'reached_your_limit'.tr()
                      : '_isleft'.tr(namedArgs: {'count': (limit! - current).toString()}),
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ),
            ],
          ),
          
          // Upgrade button for limited users at limit
          if (isAtLimit && showUpgradeButton) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onUpgradePressed,
                icon: const Icon(Icons.upgrade, size: 16),
                label: Text(
                  'upgrade_for_unlimited'.tr(),
                  style: TextStyle(fontSize: 12),
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: indicatorColor,
                  side: BorderSide(color: indicatorColor),
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Color _getColorByPercentage(double percentage) {
    if (percentage < 0.5) return Colors.green;
    if (percentage < 0.8) return Colors.orange;
    return Colors.red;
  }
}

// Simplified version for inline use
class InlineUsageIndicator extends StatelessWidget {
  final int current;
  final int? limit;
  final Color? color;

  const InlineUsageIndicator({
    super.key,
    required this.current,
    this.limit,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isUnlimited = limit == null;
    final isAtLimit = !isUnlimited && current >= limit!;
    final indicatorColor = color ?? (isAtLimit ? Colors.red : Colors.green);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: indicatorColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: indicatorColor.withOpacity(0.3),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isUnlimited ? Icons.all_inclusive : Icons.numbers,
            size: 14,
            color: indicatorColor,
          ),
          const SizedBox(width: 4),
          Text(
            isUnlimited ? 'unlimited'.tr() : '$current/${limit!}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: indicatorColor,
            ),
          ),
        ],
      ),
    );
  }
}