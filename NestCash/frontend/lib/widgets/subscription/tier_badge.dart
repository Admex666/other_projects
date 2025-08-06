// lib/widgets/subscription/tier_badge.dart
import 'package:flutter/material.dart';
import '../../models/subscription.dart';
import '../../utils/subscription_utils.dart';

class TierBadge extends StatelessWidget {
  final SubscriptionTier tier;
  final bool showPrice;
  final double? size;
  final bool isCompact;

  const TierBadge({
    super.key,
    required this.tier,
    this.showPrice = false,
    this.size,
    this.isCompact = false,
  });

  @override
  Widget build(BuildContext context) {
    final tierColor = SubscriptionUtils.getTierColor(tier);
    final tierIcon = SubscriptionUtils.getTierIcon(tier);
    final tierName = tier.displayName;
    final effectiveSize = size ?? (isCompact ? 32.0 : 48.0);
    
    if (isCompact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: tierColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: tierColor.withOpacity(0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              tierIcon,
              size: 14,
              color: tierColor,
            ),
            const SizedBox(width: 4),
            Text(
              tierName,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: tierColor,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: EdgeInsets.all(effectiveSize * 0.25),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: SubscriptionUtils.getTierGradientColors(tier),
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(effectiveSize * 0.25),
        boxShadow: [
          BoxShadow(
            color: tierColor.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Icon
          Container(
            padding: EdgeInsets.all(effectiveSize * 0.2),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              tierIcon,
              size: effectiveSize * 0.4,
              color: Colors.white,
            ),
          ),
          
          SizedBox(height: effectiveSize * 0.1),
          
          // Tier name
          Text(
            tierName,
            style: TextStyle(
              fontSize: effectiveSize * 0.25,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          
          // Price
          if (showPrice) ...[
            SizedBox(height: effectiveSize * 0.05),
            Text(
              tier.displayPrice,
              style: TextStyle(
                fontSize: effectiveSize * 0.18,
                color: Colors.white.withOpacity(0.9),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class AppBarTierBadge extends StatelessWidget {
  final SubscriptionTier tier;
  final VoidCallback? onTap;

  const AppBarTierBadge({
    super.key,
    required this.tier,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    if (tier == SubscriptionTier.free) {
      return const SizedBox.shrink();
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        child: TierBadge(
          tier: tier,
          isCompact: true,
        ),
      ),
    );
  }
}

class ProfileTierBadge extends StatelessWidget {
  final SubscriptionTier tier;
  final bool isActive;
  final DateTime? expiresAt;

  const ProfileTierBadge({
    super.key,
    required this.tier,
    this.isActive = true,
    this.expiresAt,
  });

  @override
  Widget build(BuildContext context) {
    final tierColor = SubscriptionUtils.getTierColor(tier);
    final tierIcon = SubscriptionUtils.getTierIcon(tier);
    final tierName = tier.displayName;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: SubscriptionUtils.getTierGradientColors(tier),
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: tierColor.withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          // Icon
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              tierIcon,
              size: 24,
              color: Colors.white,
            ),
          ),
          
          const SizedBox(width: 16),
          
          // Info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tierName,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  isActive ? 'Aktív előfizetés' : 'Inaktív',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.white.withOpacity(0.9),
                  ),
                ),
                if (expiresAt != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    _getExpiryText(),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.white.withOpacity(0.8),
                    ),
                  ),
                ],
              ],
            ),
          ),
          
          // Status indicator
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: isActive ? Colors.green : Colors.red,
              shape: BoxShape.circle,
              border: Border.all(
                color: Colors.white,
                width: 2,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getExpiryText() {
    if (expiresAt == null) return '';
    
    final now = DateTime.now();
    final difference = expiresAt!.difference(now);
    
    if (difference.isNegative) {
      return 'Lejárt';
    } else if (difference.inDays > 30) {
      final months = (difference.inDays / 30).floor();
      return 'Lejár $months hónap múlva';
    } else if (difference.inDays > 0) {
      return 'Lejár ${difference.inDays} nap múlva';
    } else {
      return 'Ma lejár';
    }
  }
}