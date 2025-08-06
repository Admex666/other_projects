import 'package:flutter/material.dart';
import '../../models/subscription.dart';
import '../../utils/subscription_utils.dart';

class FeatureLockedWidget extends StatelessWidget {
  final String featureName;
  final String? description;
  final SubscriptionTier requiredTier;
  final VoidCallback? onUpgradePressed;
  final double? height;
  final bool showUpgradeButton;

  const FeatureLockedWidget({
    super.key,
    required this.featureName,
    this.description,
    this.requiredTier = SubscriptionTier.plus,
    this.onUpgradePressed,
    this.height,
    this.showUpgradeButton = true,
  });

  @override
  Widget build(BuildContext context) {
    final tierColor = SubscriptionUtils.getTierColor(requiredTier);
    final tierName = SubscriptionUtils.formatTierName(requiredTier);
    final tierIcon = SubscriptionUtils.getTierIcon(requiredTier);

    return Container(
      height: height,
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Stack(
        children: [
          // Background pattern
          Positioned.fill(
            child: CustomPaint(
              painter: _LockedPatternPainter(),
            ),
          ),
          
          // Content
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Lock icon
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: tierColor.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.lock,
                    size: 48,
                    color: tierColor,
                  ),
                ),
                
                const SizedBox(height: 16),
                
                // Feature name
                Text(
                  featureName,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                  textAlign: TextAlign.center,
                ),
                
                const SizedBox(height: 8),
                
                // Description
                if (description != null)
                  Text(
                    description!,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                      height: 1.4,
                    ),
                    textAlign: TextAlign.center,
                  ),
                
                const SizedBox(height: 16),
                
                // Required tier badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: tierColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: tierColor.withOpacity(0.3)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(tierIcon, size: 18, color: tierColor),
                      const SizedBox(width: 6),
                      Text(
                        '$tierName szükséges',
                        style: TextStyle(
                          color: tierColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                
                if (showUpgradeButton) ...[
                  const SizedBox(height: 20),
                  
                  // Upgrade button
                  ElevatedButton.icon(
                    onPressed: onUpgradePressed ?? () {
                      SubscriptionUtils.showUpgradeDialog(
                        context,
                        feature: featureName,
                        requiredTier: requiredTier,
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
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LockedPatternPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey.withOpacity(0.1)
      ..strokeWidth = 1;

    const spacing = 20.0;
    
    // Draw diagonal lines pattern
    for (double i = -size.height; i < size.width + size.height; i += spacing) {
      canvas.drawLine(
        Offset(i, 0),
        Offset(i + size.height, size.height),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}