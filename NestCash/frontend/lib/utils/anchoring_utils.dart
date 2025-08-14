// lib/utils/anchoring_utils.dart
import 'dart:math';
import '../models/subscription.dart';

class AnchoringUtils {
  static final List<AnchoringComparison> _plusComparisons = [
    AnchoringComparison(
      title: 'Egy csomag cigaretta',
      description: 'Ennyi pénzért átlagosan egy csomag cigarettát kapsz. Ez pedig egy havi előfizetés.',
      icon: '🚬',
    ),
    AnchoringComparison(
      title: 'Egy Starbucks kávé',
      description: 'Kevesebb, mint egy prémium kávé ára naponta. Cserébe egy hónap teljes pénzügyi tudatosság.',
      icon: '☕',
    ),
    AnchoringComparison(
      title: 'Egy Big Mac menü',
      description: 'Annyiba kerül, mint egy gyorséttermi menü. De ez egy hónap alatt megtanít pénzt spórolni.',
      icon: '🍔',
    ),
    AnchoringComparison(
      title: 'Egy üdítő a moziban',
      description: 'Kevesebb, mint egy nagy üdítő a moziban. Viszont ez egész hónapban segít a pénzügyeidben.',
      icon: '🥤',
    ),
    AnchoringComparison(
      title: 'Egy újság és egy szendvics',
      description: 'Annyiba kerül, mint egy újság és egy szendvics. Cserébe pénzügyi tudatosság egy hónapig.',
      icon: '🥪',
    ),
  ];

  static final List<AnchoringComparison> _proComparisons = [
    AnchoringComparison(
      title: 'Két doboz cigaretta',
      description: 'Kevesebb, mint két csomag cigaretta. Cserébe egy hónap személyre szabott pénzügyi coaching.',
      icon: '🚬',
    ),
    AnchoringComparison(
      title: 'Egy éttermi pizza',
      description: 'Annyiba kerül, mint egy pizza egy jó étteremben. De ez egész hónapban fejleszti a pénzügyi szokásaidat.',
      icon: '🍕',
    ),
    AnchoringComparison(
      title: 'Két Starbucks kávé',
      description: 'Kevesebb, mint két prémium kávé árából egy havi személyre szabott pénzügyi elemzés.',
      icon: '☕',
    ),
    AnchoringComparison(
      title: 'Egy mozi jegy nassolnivalóval',
      description: 'Annyiba kerül, mint egy mozijegy popcornnal. Viszont ez egy havi exkluzív pénzügyi tanácsadás.',
      icon: '🍿',
    ),
    AnchoringComparison(
      title: 'Egy taxi utazás a belvárosban',
      description: 'Kevesebb, mint egy rövid taxi út. Cserébe egy hónap profi pénzügyi insights.',
      icon: '🚕',
    ),
    AnchoringComparison(
      title: 'Egy koktél egy jó bárban',
      description: 'Annyiba kerül, mint egy koktél egy menő helyen. De ez egész hónapban tanít befektetni.',
      icon: '🍸',
    ),
  ];

  /// Véletlenszerű anchoring összehasonlítás lekérése a tier alapján
  static AnchoringComparison getRandomComparison(SubscriptionTier tier) {
    final comparisons = tier == SubscriptionTier.plus ? _plusComparisons : _proComparisons;
    final random = Random();
    return comparisons[random.nextInt(comparisons.length)];
  }

  /// Napi költség számítása
  static String getDailyCost(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.plus:
        return '0,17 EUR';
      case SubscriptionTier.pro:
        return '0,42 EUR';
      case SubscriptionTier.free:
        return '0 EUR';
    }
  }

  /// Formázott napi költség leírással
  static String getDailyCostDescription(SubscriptionTier tier) {
    final dailyCost = getDailyCost(tier);
    return 'Mindössze $dailyCost naponta';
  }
}

class AnchoringComparison {
  final String title;
  final String description;
  final String icon;

  const AnchoringComparison({
    required this.title,
    required this.description,
    required this.icon,
  });
}