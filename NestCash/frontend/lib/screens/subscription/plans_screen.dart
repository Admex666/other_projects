// lib/screens/subscription/plans_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:easy_localization/easy_localization.dart';
import '../../models/subscription.dart';
import '../../providers/subscription_provider.dart';
import '../../widgets/subscription/tier_badge.dart';
import '../../utils/subscription_utils.dart';
import '../../utils/anchoring_utils.dart';
import 'upgrade_success_screen.dart';

class PlansScreen extends StatefulWidget {
  final SubscriptionTier currentTier;
  final SubscriptionTier? highlightTier;

  const PlansScreen({
    super.key,
    required this.currentTier,
    this.highlightTier,
  });

  @override
  State<PlansScreen> createState() => _PlansScreenState();
}

class _PlansScreenState extends State<PlansScreen> {
  bool _isUpgrading = false;

  @override
  void initState() {
    super.initState();
    // Load available plans
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SubscriptionProvider>().loadAvailablePlans();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'plans_screen.app_bar_title'.tr(),
          style: const TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: const Color(0xFF00D4A3),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Consumer<SubscriptionProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.availablePlans == null) {
            return const Center(
              child: CircularProgressIndicator(
                color: Color(0xFF00D4A3),
              ),
            );
          }

          // Use predefined plans if backend plans are not available
          final plans = provider.availablePlans ?? _getDefaultPlans();

          return SingleChildScrollView(
            child: Column(
              children: [
                // Header
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: const BoxDecoration(
                    color: Color(0xFF00D4A3),
                    borderRadius: BorderRadius.only(
                      bottomLeft: Radius.circular(30),
                      bottomRight: Radius.circular(30),
                    ),
                  ),
                  child: Column(
                    children: [
                      Text(
                        'plans_screen.header_title'.tr(),
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'plans_screen.current_tier'.tr(namedArgs: {'tier_name': widget.currentTier.displayName}),
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.black87,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const SizedBox(height: 24),
                
                // Plans
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Column(
                    children: plans.map((plan) => _buildPlanCard(plan, provider)).toList(),
                  ),
                ),
                
                const SizedBox(height: 32),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildPlanCard(SubscriptionPlan plan, SubscriptionProvider provider) {
    final isCurrentTier = plan.tier == widget.currentTier;
    final isHighlighted = plan.tier == widget.highlightTier;
    final tierColor = SubscriptionUtils.getTierColor(plan.tier);
    final canUpgrade = plan.tier.index > widget.currentTier.index;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isHighlighted 
              ? tierColor 
              : isCurrentTier 
                  ? Colors.green 
                  : Colors.grey.withOpacity(0.3),
          width: isHighlighted || isCurrentTier ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: (isHighlighted ? tierColor : Colors.black).withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          // Plan header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: isHighlighted 
                  ? tierColor.withOpacity(0.1) 
                  : isCurrentTier 
                      ? Colors.green.withOpacity(0.1) 
                      : Colors.grey.withOpacity(0.05),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Tier badge and current indicator
                Row(
                  children: [
                    TierBadge(tier: plan.tier, isCompact: true),
                    const Spacer(),
                    if (isCurrentTier)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.green,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'plans_screen.current_badge'.tr(),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    if (isHighlighted && !isCurrentTier)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: tierColor,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'plans_screen.recommended_badge'.tr(),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
                
                const SizedBox(height: 8),
                
                // Price
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      plan.tier.displayPrice,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: tierColor,
                      ),
                    ),
                    if (plan.tier != SubscriptionTier.free)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          AnchoringUtils.getDailyCostDescription(plan.tier),
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[600],
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
          
          // Features list
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ..._buildFeatureList(plan),
                
                const SizedBox(height: 20),
                
                // Action button
                SizedBox(
                  width: double.infinity,
                  child: _buildActionButton(plan, provider, canUpgrade, isCurrentTier),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildFeatureList(SubscriptionPlan plan) {
    final features = _getPlanFeatures(plan.tier);
    
    return features.map((feature) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            Icons.check_circle,
            color: SubscriptionUtils.getTierColor(plan.tier),
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              feature.tr(),
              style: const TextStyle(
                fontSize: 14,
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
    )).toList();
  }

  Widget _buildActionButton(
    SubscriptionPlan plan, 
    SubscriptionProvider provider, 
    bool canUpgrade, 
    bool isCurrentTier,
  ) {
    if (isCurrentTier) {
      return Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: Colors.grey[200],
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          'plans_screen.current_plan_button'.tr(),
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.grey,
          ),
        ),
      );
    }

    if (!canUpgrade) {
      return Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: Colors.grey[200],
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          'plans_screen.lower_tier_button'.tr(),
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            color: Colors.grey,
          ),
        ),
      );
    }

    return ElevatedButton(
      onPressed: _isUpgrading ? null : () => _handleUpgrade(plan, provider),
      style: ElevatedButton.styleFrom(
        backgroundColor: SubscriptionUtils.getTierColor(plan.tier),
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: _isUpgrading 
          ? const SizedBox(
              height: 20,
              width: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : Text(
              plan.tier == SubscriptionTier.free ? 'plans_screen.free_button'.tr() : 'plans_screen.upgrade_button'.tr(),
              style: const TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
    );
  }

  void _handleUpgrade(SubscriptionPlan plan, SubscriptionProvider provider) async {
    if (plan.tier == SubscriptionTier.free) {
      // Free plan selection - just go back
      Navigator.pop(context);
      return;
    }

    setState(() => _isUpgrading = true);

    try {
      // Show payment confirmation dialog
      final confirmed = await _showPaymentDialog(plan);
      
      if (confirmed == true) {
        // In a real app, you'd integrate with payment provider here
        // For now, we'll simulate successful payment
        final success = await provider.upgradeSubscription(
          plan.tier,
          paymentProvider: 'stripe', // or whatever payment provider you use
          externalSubscriptionId: 'sub_${DateTime.now().millisecondsSinceEpoch}',
        );

        if (success) {
          if (mounted) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (context) => UpgradeSuccessScreen(newTier: plan.tier),
              ),
            );
          }
        } else {
          _showErrorSnackbar('plans_screen.upgrade_failed_snackbar'.tr());
        }
      }
    } catch (e) {
      _showErrorSnackbar('plans_screen.error_snackbar'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      if (mounted) {
        setState(() => _isUpgrading = false);
      }
    }
  }

  Future<bool?> _showPaymentDialog(SubscriptionPlan plan) async {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('plans_screen.dialog_title'.tr()),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('plans_screen.dialog_upgrade_text'.tr(namedArgs: {'tier_name': plan.tier.displayName})),
            const SizedBox(height: 8),
            Text(
              'plans_screen.dialog_price_text'.tr(namedArgs: {'price': plan.tier.displayPrice}),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text(
              'plans_screen.dialog_info_text'.tr(),
              style: const TextStyle(
                fontSize: 12,
                color: Colors.grey,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('plans_screen.dialog_cancel_button'.tr()),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('plans_screen.dialog_confirm_button'.tr()),
          ),
        ],
      ),
    );
  }

  void _showErrorSnackbar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  List<String> _getPlanFeatures(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return [
          'plans_screen.free_feature_1',
          'plans_screen.free_feature_2',
          'plans_screen.free_feature_3',
          'plans_screen.free_feature_4',
          'plans_screen.free_feature_5',
          'plans_screen.free_feature_6',
          'plans_screen.free_feature_7',
          'plans_screen.free_feature_8',
          'plans_screen.free_feature_9',
          'plans_screen.free_feature_10',
          'plans_screen.free_feature_11',
        ];
      case SubscriptionTier.plus:
        return [
          'plans_screen.plus_feature_1',
          'plans_screen.plus_feature_2',
          'plans_screen.plus_feature_3',
          'plans_screen.plus_feature_4',
          'plans_screen.plus_feature_5',
          'plans_screen.plus_feature_6',
          'plans_screen.plus_feature_7',
          'plans_screen.plus_feature_8',
          'plans_screen.plus_feature_9',
        ];
      case SubscriptionTier.pro:
        return [
          'plans_screen.pro_feature_1',
          'plans_screen.pro_feature_2',
          'plans_screen.pro_feature_3',
          'plans_screen.pro_feature_4',
          'plans_screen.pro_feature_5',
          'plans_screen.pro_feature_6',
          'plans_screen.pro_feature_7',
        ];
    }
  }

  List<SubscriptionPlan> _getDefaultPlans() {
    return [
      SubscriptionPlan(
        tier: SubscriptionTier.free,
        name: 'Free',
        price: 0.0,
        durationDays: 0,
        features: {
          'transaction_management': 'basic_manual',
          'analysis_insights': 'basic_category_only',
          'knowledge_base': '1_lesson_per_day_with_ads',
          'challenges': '1_active',
          'habit_streak': 'max_5_habits',
          'accountability_partner': 'max_1',
        },
      ),
      SubscriptionPlan(
        tier: SubscriptionTier.plus,
        name: 'Plus',
        price: 5.0,
        durationDays: 30,
        features: {
          'transaction_management': 'import_bulk_edit',
          'analysis_insights': 'full_module',
          'knowledge_base': 'full_unlimited',
          'challenges': 'unlimited',
          'habit_streak': 'unlimited',
          'accountability_partner': 'unlimited',
        },
      ),
      SubscriptionPlan(
        tier: SubscriptionTier.pro,
        name: 'Pro',
        price: 12.5,
        durationDays: 30,
        features: {
          'transaction_management': 'import_bulk_edit',
          'analysis_insights': 'personalized',
          'knowledge_base': 'exclusive_content_learning_paths',
          'challenges': 'unlimited_with_exclusive',
          'habit_streak': 'unlimited',
          'accountability_partner': 'unlimited_with_groups',
        },
      ),
    ];
  }
}