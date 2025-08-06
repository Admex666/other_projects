// lib/widgets/subscription/subscription_widgets.dart
import 'package:flutter/material.dart';
import '../../models/subscription.dart';

/// Inline használati indikátor widget - használat/limit megjelenítésére
class InlineUsageIndicator extends StatelessWidget {
  final int current;
  final int limit;
  final Color color;
  final double fontSize;

  const InlineUsageIndicator({
    Key? key,
    required this.current,
    required this.limit,
    this.color = Colors.black,
    this.fontSize = 12,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isNearLimit = current / limit >= 0.8;
    final displayColor = isNearLimit ? Colors.red : color;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: displayColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: displayColor.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.info_outline,
            size: fontSize + 2,
            color: displayColor,
          ),
          const SizedBox(width: 4),
          Text(
            '$current/$limit',
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: FontWeight.w600,
              color: displayColor,
            ),
          ),
        ],
      ),
    );
  }
}

/// AppBar-ban megjelenő tier badge
class AppBarTierBadge extends StatelessWidget {
  final SubscriptionTier tier;
  final VoidCallback? onTap;

  const AppBarTierBadge({
    Key? key,
    required this.tier,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Free tier esetén nem jelenítünk meg semmit
    if (tier == SubscriptionTier.free) {
      return const SizedBox(width: 48);
    }

    final tierColor = _getTierColor(tier);
    final tierIcon = _getTierIcon(tier);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 12, top: 8, bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              tierColor,
              tierColor.withOpacity(0.8),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: tierColor.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              tierIcon,
              color: Colors.white,
              size: 16,
            ),
            const SizedBox(width: 4),
            Text(
              tier.displayName.toUpperCase(),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getTierColor(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Colors.grey;
      case SubscriptionTier.plus:
        return const Color(0xFF4CAF50); // Green
      case SubscriptionTier.pro:
        return const Color(0xFF9C27B0); // Purple
    }
  }

  IconData _getTierIcon(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Icons.person;
      case SubscriptionTier.plus:
        return Icons.star;
      case SubscriptionTier.pro:
        return Icons.diamond;
    }
  }
}

/// Kör alakú tier badge (alternatív design)
class CircularTierBadge extends StatelessWidget {
  final SubscriptionTier tier;
  final double size;
  final VoidCallback? onTap;

  const CircularTierBadge({
    Key? key,
    required this.tier,
    this.size = 32,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (tier == SubscriptionTier.free) {
      return SizedBox(width: size, height: size);
    }

    final tierColor = _getTierColor(tier);
    final tierIcon = _getTierIcon(tier);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              tierColor,
              tierColor.withOpacity(0.8),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: tierColor.withOpacity(0.3),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Icon(
          tierIcon,
          color: Colors.white,
          size: size * 0.5,
        ),
      ),
    );
  }

  Color _getTierColor(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Colors.grey;
      case SubscriptionTier.plus:
        return const Color(0xFF4CAF50);
      case SubscriptionTier.pro:
        return const Color(0xFF9C27B0);
    }
  }

  IconData _getTierIcon(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Icons.person;
      case SubscriptionTier.plus:
        return Icons.star;
      case SubscriptionTier.pro:
        return Icons.diamond;
    }
  }
}

/// Subscription status banner - lejárati figyelmeztetéshez
class SubscriptionStatusBanner extends StatelessWidget {
  final UserSubscription subscription;
  final VoidCallback? onUpgrade;

  const SubscriptionStatusBanner({
    Key? key,
    required this.subscription,
    this.onUpgrade,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Csak akkor jelenítünk meg bannert, ha figyelmeztetni kell
    if (!_shouldShowBanner()) {
      return const SizedBox.shrink();
    }

    final bannerColor = _getBannerColor();
    final message = _getBannerMessage();
    final icon = _getBannerIcon();

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bannerColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: bannerColor.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Icon(icon, color: bannerColor),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _getBannerTitle(),
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: bannerColor,
                  ),
                ),
                Text(
                  message,
                  style: TextStyle(
                    fontSize: 12,
                    color: bannerColor.withOpacity(0.8),
                  ),
                ),
              ],
            ),
          ),
          if (onUpgrade != null)
            TextButton(
              onPressed: onUpgrade,
              child: Text(
                'Frissítés',
                style: TextStyle(color: bannerColor),
              ),
            ),
        ],
      ),
    );
  }

  bool _shouldShowBanner() {
    // Lejárt előfizetés
    if (subscription.status == SubscriptionStatus.expired) return true;
    
    // 7 napon belül lejár
    if (subscription.daysUntilExpiry != null && 
        subscription.daysUntilExpiry! <= 7 && 
        subscription.daysUntilExpiry! > 0) {
      return true;
    }
    
    return false;
  }

  Color _getBannerColor() {
    if (subscription.status == SubscriptionStatus.expired) {
      return Colors.red;
    }
    return Colors.orange;
  }

  IconData _getBannerIcon() {
    if (subscription.status == SubscriptionStatus.expired) {
      return Icons.error;
    }
    return Icons.warning;
  }

  String _getBannerTitle() {
    if (subscription.status == SubscriptionStatus.expired) {
      return 'Előfizetés lejárt';
    }
    return 'Előfizetés hamarosan lejár';
  }

  String _getBannerMessage() {
    if (subscription.status == SubscriptionStatus.expired) {
      return 'Az előfizetésed lejárt. Frissítsd a folyamatos hozzáféréshez.';
    }
    
    if (subscription.daysUntilExpiry != null) {
      if (subscription.daysUntilExpiry == 1) {
        return 'Az előfizetésed holnap lejár.';
      }
      return 'Az előfizetésed ${subscription.daysUntilExpiry} nap múlva lejár.';
    }
    
    return 'Ellenőrizd az előfizetésed állapotát.';
  }
}