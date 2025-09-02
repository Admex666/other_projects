// lib/widgets/subscription/upgrade_dialog.dart
import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:provider/provider.dart';
import '../../models/subscription.dart';
import '../../providers/subscription_provider.dart';
import '../../utils/subscription_utils.dart';
import '../../screens/subscription/plans_screen.dart';
import '../../utils/anchoring_utils.dart';

class UpgradeDialog extends StatefulWidget {
  final String featureName;
  final SubscriptionTier requiredTier;
  final String? description;

  const UpgradeDialog({
    super.key,
    required this.featureName,
    this.requiredTier = SubscriptionTier.plus,
    this.description,
  });

  @override
  State<UpgradeDialog> createState() => _UpgradeDialogState();
}

class _UpgradeDialogState extends State<UpgradeDialog> {
  late final AnchoringComparison anchoringComparison;

  @override
  void initState() {
    super.initState();
    // Véletlenszerű anchoring összehasonlítás kiválasztása
    anchoringComparison = AnchoringUtils.getRandomComparison(widget.requiredTier);
  }

  @override
  Widget build(BuildContext context) {
    final tierColor = SubscriptionUtils.getTierColor(widget.requiredTier);
    final tierIcon = SubscriptionUtils.getTierIcon(widget.requiredTier);
    final tierName = SubscriptionUtils.formatTierName(widget.requiredTier);
    final price = widget.requiredTier.displayPrice;
    final dailyCost = AnchoringUtils.getDailyCost(widget.requiredTier);

    return Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: LinearGradient(
            colors: [
              Colors.white,
              tierColor.withOpacity(0.05),
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Close button
            Align(
              alignment: Alignment.topRight,
              child: IconButton(
                onPressed: () => Navigator.pop(context),
                icon: Icon(
                  Icons.close,
                  color: Colors.grey[600],
                ),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ),
            
            // Icon
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: tierColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                tierIcon,
                size: 48,
                color: tierColor,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Title
            Text(
              'habits.upgrade_needed'.tr(),
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            
            const SizedBox(height: 8),
            
            // Feature name
            Text(
              widget.featureName,
              style: TextStyle(
                fontSize: 18,
                color: tierColor,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            
            const SizedBox(height: 16),
            
            // Description
            Text(
              widget.description ?? 
              'to_use_function_tier_needed'.tr(namedArgs: {'feature': widget.featureName.toString(), 'tier': tierName}),
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
                height: 1.4,
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Tier info card with pricing
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: tierColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: tierColor.withOpacity(0.3),
                ),
              ),
              child: Column(
                children: [
                  // Tier header
                  Row(
                    children: [
                      Icon(tierIcon, color: tierColor, size: 24),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              tierName,
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: tierColor,
                              ),
                            ),
                            Text(
                              price,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 12),
                  
                  // Daily cost
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.7),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.calendar_today,
                          size: 16,
                          color: Colors.grey[600],
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'costs_only'.tr(namedArgs: {'cost': dailyCost.toString()}),
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[700],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Anchoring comparison card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.orange.withOpacity(0.3),
                ),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      Text(
                        anchoringComparison.icon,
                        style: const TextStyle(fontSize: 24),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          anchoringComparison.title,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    anchoringComparison.description,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                      height: 1.3,
                    ),
                    textAlign: TextAlign.left,
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Action buttons
            Row(
              children: [
                // Cancel button
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.grey[600],
                      side: BorderSide(color: Colors.grey[300]!),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: Text('later'.tr()),
                  ),
                ),
                
                const SizedBox(width: 12),
                
                // Upgrade button
                Expanded(
                  flex: 2,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => PlansScreen(
                            currentTier: context.read<SubscriptionProvider>().currentTier,
                            highlightTier: widget.requiredTier,
                          ),
                        ),
                      );
                    },
                    icon: Icon(tierIcon, size: 18),
                    label: Text(
                      'plans_screen.upgrade_button'.tr(),
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: tierColor,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}