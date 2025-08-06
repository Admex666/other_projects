// lib/widgets/subscription/upgrade_dialog.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/subscription.dart';
import '../../providers/subscription_provider.dart';
import '../../utils/subscription_utils.dart';
import '../../screens/subscription/plans_screen.dart';

class UpgradeDialog extends StatelessWidget {
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
  Widget build(BuildContext context) {
    final tierColor = SubscriptionUtils.getTierColor(requiredTier);
    final tierIcon = SubscriptionUtils.getTierIcon(requiredTier);
    final tierName = SubscriptionUtils.formatTierName(requiredTier);
    final price = requiredTier.displayPrice;

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
              'Frissítés szükséges',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            
            const SizedBox(height: 8),
            
            // Feature name
            Text(
              featureName,
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
              description ?? 
              'A $featureName funkció használatához $tierName előfizetés szükséges.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
                height: 1.4,
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Tier info card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: tierColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: tierColor.withOpacity(0.3),
                ),
              ),
              child: Row(
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
                    child: const Text('Később'),
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
                            highlightTier: requiredTier,
                          ),
                        ),
                      );
                    },
                    icon: Icon(tierIcon, size: 18),
                    label: const Text(
                      'Frissítés',
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