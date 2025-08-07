import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/subscription.dart';
import '../../providers/subscription_provider.dart';
import '../../widgets/subscription/tier_badge.dart';
import '../../widgets/subscription/usage_indicator.dart';
import 'plans_screen.dart';

class SubscriptionScreen extends StatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  State<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends State<SubscriptionScreen> {
  
  @override
  void initState() {
    super.initState();
    print('SubscriptionScreen initState: Loading subscription info...');
    
    // Load subscription info when screen opens
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        print('SubscriptionScreen: About to load subscription with forceRefresh');
        context.read<SubscriptionProvider>().loadSubscriptionInfo(forceRefresh: true);
      }
    });
  }

  // Manual refresh metódus
  Future<void> _refreshSubscription() async {
    if (!mounted) return;
    
    try {
      final provider = context.read<SubscriptionProvider>();
      await provider.loadSubscriptionInfo(forceRefresh: true);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Előfizetési adatok frissítve'),
            backgroundColor: Color(0xFF00D4A3),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      print('Error during manual refresh: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Frissítési hiba: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Előfizetésem',
          style: TextStyle(
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
          if (provider.isLoading) {
            return const Center(
              child: CircularProgressIndicator(
                color: Color(0xFF00D4A3),
              ),
            );
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.error_outline,
                    size: 64,
                    color: Colors.grey[400],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Hiba történt',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[700],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    provider.error!,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      provider.loadSubscriptionInfo(forceRefresh: true);
                    },
                    child: const Text('Újrapróbálkozás'),
                  ),
                ],
              ),
            );
          }

          final subscription = provider.subscriptionInfo;
          if (subscription == null) return const SizedBox();

          return RefreshIndicator(
            color: const Color(0xFF00D4A3),
            onRefresh: () async {
              print('SubscriptionScreen: Manual refresh triggered');
              await provider.loadSubscriptionInfo(forceRefresh: true);
            },
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: Column(
                children: [
                  // Current subscription status
                  _buildCurrentStatusCard(context, subscription, provider),
                  
                  const SizedBox(height: 16),
                  
                  // Usage statistics
                  _buildUsageSection(context, provider),
                  
                  const SizedBox(height: 16),
                  
                  // Action buttons
                  _buildActionSection(context, subscription, provider),
                  
                  const SizedBox(height: 32),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildCurrentStatusCard(BuildContext context, UserSubscription subscription, SubscriptionProvider provider) {
    print('SubscriptionScreen: Building status card for tier: ${subscription.tier}');
    print('SubscriptionScreen: Subscription status: ${subscription.status}');
    
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: _getTierGradientColors(subscription.tier),
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: _getTierColor(subscription.tier).withOpacity(0.3),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Tier badge
          TierBadge(tier: subscription.tier, showPrice: true),
          
          const SizedBox(height: 16),
          
          // Status text
          Text(
            subscription.statusDisplayText,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          
          const SizedBox(height: 8),
          
          // Expiry info
          if (subscription.expiryDisplayText != null)
            Text(
              subscription.expiryDisplayText!,
              style: TextStyle(
                color: Colors.white.withOpacity(0.8),
                fontSize: 14,
              ),
            ),
          
          // Subscription date
          if (subscription.tier != SubscriptionTier.free) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'Előfizetve: ${_formatDate(subscription.subscribedAt)}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildUsageSection(BuildContext context, SubscriptionProvider provider) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Használati statisztikák',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),
          
          // Challenges usage
          UsageIndicator(
            featureName: 'Aktív kihívások',
            current: provider.getCurrentChallengesCount(),
            limit: provider.getChallengesLimit() == -1 ? null : provider.getChallengesLimit(),
            showUpgradeButton: !provider.canCreateUnlimitedChallenges,
          ),
          
          const SizedBox(height: 12),
          
          // Habits usage
          FutureBuilder<int>(
            future: provider.getCurrentHabitsCount(),
            builder: (context, snapshot) {
              final habitsCount = snapshot.data ?? provider.cachedHabitsCount;
              
              return UsageIndicator(
                featureName: 'Szokások',
                current: habitsCount,
                limit: provider.getHabitsLimit() == -1 ? null : provider.getHabitsLimit(),
                showUpgradeButton: !provider.canCreateUnlimitedHabits,
              );
            },
          ),
          
          const SizedBox(height: 12),
          
          // Partners usage
          UsageIndicator(
            featureName: 'Partner kapcsolatok',
            current: provider.getCurrentPartnersCount(),
            limit: provider.getPartnersLimit() == -1 ? null : provider.getPartnersLimit(),
            showUpgradeButton: provider.currentTier == SubscriptionTier.free,
          ),
        ],
      ),
    );
  }

  Widget _buildActionSection(BuildContext context, UserSubscription subscription, SubscriptionProvider provider) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // Upgrade button
          if (subscription.tier != SubscriptionTier.pro)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PlansScreen(
                        currentTier: subscription.tier,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.upgrade),
                label: Text(
                  subscription.tier == SubscriptionTier.free 
                    ? 'Előfizetés indítása'
                    : 'Frissítés Pro-ra',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6C63FF),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          
          const SizedBox(height: 12),
          
          // Cancel subscription (if subscribed)
          if (subscription.tier != SubscriptionTier.free && subscription.isActive)
            TextButton(
              onPressed: () => _showCancelDialog(context, provider),
              child: Text(
                'Előfizetés lemondása',
                style: TextStyle(
                  color: Colors.grey[600],
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
        ],
      ),
    );
  }

  void _showCancelDialog(BuildContext context, SubscriptionProvider provider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Előfizetés lemondása'),
        content: const Text(
          'Biztosan le szeretnéd mondani az előfizetésed? '
          'A lemondás után a Free verzióra térünk vissza.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Mégse'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              final success = await provider.cancelSubscription();
              if (success) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Előfizetés sikeresen lemondva'),
                    backgroundColor: Color(0xFF00D4A3),
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            child: const Text('Lemondás'),
          ),
        ],
      ),
    );
  }

  Color _getTierColor(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.free:
        return Colors.grey[600]!;
      case SubscriptionTier.plus:
        return const Color(0xFF00D4A3);
      case SubscriptionTier.pro:
        return const Color(0xFF6C63FF);
    }
  }

  List<Color> _getTierGradientColors(SubscriptionTier tier) {
    final baseColor = _getTierColor(tier);
    return [baseColor, baseColor.withOpacity(0.8)];
  }

  String _formatDate(DateTime date) {
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
  }
}