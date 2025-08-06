// lib/utils/subscription_utils.dart
import 'package:flutter/material.dart';
import '../models/subscription.dart';
import '../widgets/subscription/upgrade_dialog.dart';

class SubscriptionUtils {
  
  /// Get color for subscription tier
  static Color getTierColor(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Colors.grey[600]!;
      case SubscriptionTier.plus:
        return const Color(0xFF00D4A3);
      case SubscriptionTier.pro:
        return const Color(0xFF6C63FF);
    }
  }

  /// Get icon for subscription tier
  static IconData getTierIcon(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Icons.person;
      case SubscriptionTier.plus:
        return Icons.star;
      case SubscriptionTier.pro:
        return Icons.diamond;
    }
  }

  /// Format tier name for display
  static String formatTierName(SubscriptionTier tier) {
    return tier.displayName;
  }

  /// Get gradient colors for tier
  static List<Color> getTierGradientColors(SubscriptionTier tier) {
    final baseColor = getTierColor(tier);
    return [
      baseColor,
      baseColor.withOpacity(0.8),
    ];
  }

  /// Show upgrade dialog
  static void showUpgradeDialog(
    BuildContext context, {
    required String feature,
    SubscriptionTier requiredTier = SubscriptionTier.plus,
    String? description,
  }) {
    showDialog(
      context: context,
      builder: (context) => UpgradeDialog(
        featureName: feature,
        requiredTier: requiredTier,
        description: description,
      ),
    );
  }

  /// Check if user can access feature based on tier
  static bool canAccessFeature(
    SubscriptionTier currentTier,
    SubscriptionTier requiredTier,
  ) {
    return currentTier.index >= requiredTier.index;
  }

  /// Get feature limitation message
  static String getFeatureLimitationMessage(
    String featureName,
    SubscriptionTier currentTier,
    SubscriptionTier requiredTier,
  ) {
    final tierName = formatTierName(requiredTier);
    return '$featureName funkcióhoz $tierName előfizetés szükséges';
  }

  /// Show tier upgrade bottom sheet
  static void showTierUpgradeBottomSheet(
    BuildContext context, {
    required String feature,
    SubscriptionTier requiredTier = SubscriptionTier.plus,
  }) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.95,
        minChildSize: 0.5,
        builder: (context, scrollController) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: _buildUpgradeContent(
            context,
            scrollController,
            feature,
            requiredTier,
          ),
        ),
      ),
    );
  }

  static Widget _buildUpgradeContent(
    BuildContext context,
    ScrollController scrollController,
    String feature,
    SubscriptionTier requiredTier,
  ) {
    final tierColor = getTierColor(requiredTier);
    final tierIcon = getTierIcon(requiredTier);
    final tierName = formatTierName(requiredTier);

    return SingleChildScrollView(
      controller: scrollController,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Handle bar
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            
            const SizedBox(height: 24),
            
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
            
            const SizedBox(height: 24),
            
            // Title
            Text(
              'Frissítés szükséges',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey[800],
              ),
            ),
            
            const SizedBox(height: 8),
            
            // Feature name
            Text(
              feature,
              style: TextStyle(
                fontSize: 18,
                color: tierColor,
                fontWeight: FontWeight.w600,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Description
            Text(
              'A $feature funkció használatához $tierName előfizetés szükséges.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
                height: 1.5,
              ),
            ),
            
            const SizedBox(height: 32),
            
            // Benefits list
            _buildBenefitsList(requiredTier),
            
            const SizedBox(height: 32),
            
            // Upgrade button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  // Navigate to plans screen
                  // This would be implemented based on your navigation structure
                },
                icon: Icon(tierIcon),
                label: Text(
                  'Frissítés $tierName-ra',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: tierColor,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Cancel button
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                'Később',
                style: TextStyle(
                  color: Colors.grey[600],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Widget _buildBenefitsList(SubscriptionTier tier) {
    final benefits = _getTierBenefits(tier);
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${formatTierName(tier)} előnyök:',
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 12),
        ...benefits.map((benefit) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            children: [
              Icon(
                Icons.check_circle,
                color: getTierColor(tier),
                size: 20,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  benefit,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[700],
                  ),
                ),
              ),
            ],
          ),
        )),
      ],
    );
  }

  static List<String> _getTierBenefits(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.plus:
        return [
          'Korlátlan kihívások',
          'Korlátlan szokások',
          'Teljes elemzések',
          'Teljes tudástár',
          'Import funkciók',
          'Tömeges szerkesztés',
          'Tier jelvény',
        ];
      case SubscriptionTier.pro:
        return [
          'Minden Plus funkció',
          'Személyre szabott elemzések',
          'Exkluzív leckék',
          'Exkluzív kihívások',
          'Csoportok',
          'Korlátlan partnerek',
          'Javaslatok',
        ];
      case SubscriptionTier.free:
        return [];
    }
  }

  /// Format price display
  static String formatPrice(double price, {String currency = 'EUR'}) {
    if (price == 0) return 'Ingyenes';
    // Handle the 12.5 case specifically
    if (price == 12.5) return '12,5 $currency/hó';
    return '${price.toStringAsFixed(price.truncateToDouble() == price ? 0 : 1)} $currency/hó';
  }

  /// Get usage color based on percentage
  static Color getUsageColor(double percentage) {
    if (percentage < 0.5) return Colors.green;
    if (percentage < 0.8) return Colors.orange;
    return Colors.red;
  }

  /// Show feature locked snackbar
  static void showFeatureLockedSnackbar(
    BuildContext context, {
    required String feature,
    SubscriptionTier requiredTier = SubscriptionTier.plus,
  }) {
    final tierName = formatTierName(requiredTier);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              Icons.lock,
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text('$feature - $tierName előfizetés szükséges'),
            ),
          ],
        ),
        backgroundColor: getTierColor(requiredTier),
        action: SnackBarAction(
          label: 'Frissítés',
          textColor: Colors.white,
          onPressed: () {
            showUpgradeDialog(
              context,
              feature: feature,
              requiredTier: requiredTier,
            );
          },
        ),
        duration: const Duration(seconds: 4),
      ),
    );
  }
}