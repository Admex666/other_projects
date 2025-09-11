// lib/screens/challenges/challenges_main_screen.dart
import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/models/challenge.dart';
import 'package:frontend/services/challenge_service.dart';
import 'package:frontend/screens/challenges/challenge_detail_screen.dart';
import 'package:frontend/screens/challenges/my_challenges_screen.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:provider/provider.dart';
import 'package:frontend/providers/subscription_provider.dart';
import 'package:frontend/widgets/subscription/usage_indicator.dart';
import 'package:frontend/widgets/subscription/tier_badge.dart';
import 'package:frontend/utils/subscription_utils.dart';
import 'package:frontend/models/subscription.dart';
import 'package:frontend/services/nestcash_analytics_service.dart';

class ChallengesMainScreen extends StatefulWidget {
  final String userId;
  final String? username;

  const ChallengesMainScreen({
    Key? key,
    required this.userId,
    this.username,
  }) : super(key: key);

  @override
  _ChallengesMainScreenState createState() => _ChallengesMainScreenState();
}

class _ChallengesMainScreenState extends State<ChallengesMainScreen>
  with SingleTickerProviderStateMixin {
  final ChallengeService _challengeService = ChallengeService();
  late TabController _tabController;

  String _currentUsername = 'User';
  final AuthService _authService = AuthService();
  List<Challenge> _allChallenges = [];
  List<Challenge> _recommendedChallenges = [];
  bool _isLoading = true;
  bool _isCheckingFeatureAccess = false;
  int _activeChallengesCount = 0;
  String _error = '';

  ChallengeType? _selectedType;
  ChallengeDifficulty? _selectedDifficulty;
  String _sortBy = 'newest';
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await NestCashAnalyticsService.trackScreenView('challenges_screen');
    });

    _tabController = TabController(length: 3, vsync: this);
    _loadUsername();
    Future.microtask(() {
      _loadChallenges();
    });
  }
  
  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadUsername() async {
    final username = widget.username ?? await _authService.getCurrentUsername();
    if (username != null && mounted) {
      setState(() {
        _currentUsername = username;
      });
    }
  }

   Future<void> _loadChallenges() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      final currentLang = context.locale.languageCode;

      final futures = await Future.wait([
        _challengeService.getChallenges(
          challengeType: _selectedType,
          difficulty: _selectedDifficulty,
          search: _searchController.text.isEmpty ? null : _searchController.text,
          sortBy: _sortBy,
          lang: currentLang,
        ),
        _challengeService.getRecommendedChallenges(lang: currentLang),
      ]);

      // Aktív kihívások számának meghatározása
      final allChallenges = futures[0];
      _activeChallengesCount = allChallenges.where((c) => c.isParticipating).length;

      setState(() {
        _allChallenges = futures[0];
        _recommendedChallenges = futures[1];
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<bool> _checkCanJoinChallenge() async {
    final subscriptionProvider = context.read<SubscriptionProvider>();
    
    try {
      setState(() => _isCheckingFeatureAccess = true);
      
      final canJoin = await subscriptionProvider.canCreateChallenge();
      
      if (!canJoin) {
        _showChallengeJoinLimitReached();
        return false;
      }
      
      return true;
    } finally {
      setState(() => _isCheckingFeatureAccess = false);
    }
  }

  void _showChallengeJoinLimitReached() {
    SubscriptionUtils.showUpgradeDialog(
      context,
      feature: 'further_challenges'.tr(),
      description: 'free_version_limit'.tr(),
      requiredTier: SubscriptionTier.plus,
    );
  }

  void _showFilterBottomSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.8,
        minChildSize: 0.4,
        builder: (context, scrollController) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
            ),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: const BoxDecoration(
                  color: Color(0xFF00D4A3),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.filter_list, color: Colors.white, size: 28),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        'filters'.tr(),
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close, color: Colors.white),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Típus szűrő
                      Text(
                        'type'.tr(),
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2D3748),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildFilterChip(
                            'all'.tr(),
                            _selectedType == null,
                            () {
                              setState(() => _selectedType = null);
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          ),
                          ...ChallengeType.values.map((type) => _buildFilterChip(
                            type.displayName,
                            _selectedType == type,
                            () {
                              setState(() => _selectedType = _selectedType == type ? null : type);
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          )),
                        ],
                      ),
                      const SizedBox(height: 24),
                      
                      // Nehézség szűrő
                      Text(
                        'difficulty'.tr(),
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2D3748),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildFilterChip(
                            'all'.tr(),
                            _selectedDifficulty == null,
                            () {
                              setState(() => _selectedDifficulty = null);
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          ),
                          ...ChallengeDifficulty.values.map((difficulty) => _buildFilterChip(
                            difficulty.displayName,
                            _selectedDifficulty == difficulty,
                            () {
                              setState(() => _selectedDifficulty = _selectedDifficulty == difficulty ? null : difficulty);
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          )),
                        ],
                      ),
                      const SizedBox(height: 24),
                      
                      // Rendezés
                      Text(
                        'sort'.tr(),
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2D3748),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildFilterChip(
                            'newest'.tr(),
                            _sortBy == 'newest',
                            () {
                              setState(() => _sortBy = 'newest');
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          ),
                          _buildFilterChip(
                            'popular'.tr(),
                            _sortBy == 'popular',
                            () {
                              setState(() => _sortBy = 'popular');
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          ),
                          _buildFilterChip(
                            'difficulty'.tr(),
                            _sortBy == 'difficulty',
                            () {
                              setState(() => _sortBy = 'difficulty');
                              Navigator.pop(context);
                              _loadChallenges();
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00D4A3) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF00D4A3) : Colors.grey[300]!,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.grey[700],
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _buildUsageIndicator() {
    return Consumer<SubscriptionProvider>(
      builder: (context, subscriptionProvider, child) {
        final currentTier = subscriptionProvider.currentTier;
        final challengesLimit = currentTier == SubscriptionTier.free ? 1 : null;
        
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: UsageIndicator(
            featureName: 'active_challenges'.tr(),
            current: _activeChallengesCount,
            limit: challengesLimit,
            onUpgradePressed: () => SubscriptionUtils.showUpgradeDialog(
              context,
              feature: 'unlimited_challenges'.tr(),
              requiredTier: SubscriptionTier.plus,
            ),
          ),
        );
      },
    );
  }  

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      decoration: BoxDecoration(
        color: Color(0xFF00D4A3),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Back arrow, cím és tier badge
          Row(
            children: [
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00D4A3).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.arrow_back_ios,
                    color: Colors.black87,
                    size: 20,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  'challenges'.tr(),
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ),
              // Tier Badge hozzáadása
              Consumer<SubscriptionProvider>(
                builder: (context, subscriptionProvider, child) {
                  return AppBarTierBadge(
                    tier: subscriptionProvider.currentTier,
                    onTap: () => SubscriptionUtils.showUpgradeDialog(
                      context,
                      feature: 'manage_subscriptions'.tr(),
                      requiredTier: SubscriptionTier.plus,
                    ),
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: 20),
          
          // Keresés és szűrők
          Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.circular(15),
                  ),
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'search_challenges'.tr(),
                      prefixIcon: Icon(Icons.search, color: Color(0xFF00D4A3)),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      hintStyle: TextStyle(color: Colors.grey),
                    ),
                    onSubmitted: (_) => _loadChallenges(),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              GestureDetector(
                onTap: _showFilterBottomSheet,
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00D4A3),
                    borderRadius: BorderRadius.circular(15),
                  ),
                  child: const Icon(
                    Icons.filter_list,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      body: SafeArea(
        child: Column(
          children: [
            // Header módosított verzió
            _buildHeader(),

            // Usage Indicator hozzáadása
            _buildUsageIndicator(),

            // Tab Bar
            Container(
              color: Colors.white,
              child: TabBar(
                controller: _tabController,
                tabs: [
                  Tab(text: 'discovery'.tr()),
                  Tab(text: 'recommended'.tr()),
                  Tab(text: 'my_challenges_tab'.tr()),
                ],
                labelColor: const Color(0xFF00D4A3),
                unselectedLabelColor: Colors.grey,
                indicatorColor: const Color(0xFF00D4A3),
                indicatorWeight: 3,
                labelStyle: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),

            // Tab Bar View
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildChallengesList(_allChallenges),
                  _buildChallengesList(_recommendedChallenges),
                  MyChallengesScreen(userId: widget.userId),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // _buildChallengeCard módosítása - jogosultság ellenőrzéssel
  Widget _buildChallengeCard(Challenge challenge) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () async {
            // Ha még nem vesz részt és elérte a limitet, ellenőrizzük
            if (!challenge.isParticipating) {
              final subscriptionProvider = context.read<SubscriptionProvider>();
              if (subscriptionProvider.currentTier == SubscriptionTier.free && 
                  _activeChallengesCount >= 1) {
                _showChallengeJoinLimitReached();
                return;
              }
            }
            
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ChallengeDetailScreen(
                  challengeId: challenge.id,
                  userId: widget.userId,
                ),
              ),
            ).then((_) => _loadChallenges());
          },
          borderRadius: BorderRadius.circular(15),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: _getTypeColor(challenge.challengeType),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        challenge.challengeType.displayName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: _getDifficultyColor(challenge.difficulty),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        challenge.difficulty.displayName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const Spacer(),
                    if (challenge.isParticipating)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.green,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          'participating'.tr(),
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      )
                    else
                      // Jogosultság figyelmeztető jelzés
                      Consumer<SubscriptionProvider>(
                        builder: (context, subscriptionProvider, child) {
                          final isAtLimit = subscriptionProvider.currentTier == SubscriptionTier.free && 
                                           _activeChallengesCount >= 1;
                          
                          if (isAtLimit) {
                            return Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              decoration: BoxDecoration(
                                color: Colors.grey,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.lock, size: 12, color: Colors.white),
                                  SizedBox(width: 4),
                                  Text(
                                    'limit_reached'.tr(),
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }
                          
                          return Icon(
                            Icons.arrow_forward_ios,
                            color: Colors.grey,
                            size: 16,
                          );
                        },
                      ),
                  ],
                ),
                
                // Rest of the existing card content remains the same
                const SizedBox(height: 16),

                Text(
                  challenge.title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF2D3748),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  challenge.shortDescription ?? challenge.description,
                  style: const TextStyle(
                    color: Colors.grey,
                    fontSize: 14,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 16),

                // Haladás (ha részt vesz)
                if (challenge.isParticipating && challenge.myProgress != null)
                  Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '${'progress'.tr()}: ${challenge.myProgress!.percentage.toStringAsFixed(1)}%',
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF2D3748),
                            ),
                          ),
                          Text(
                            '${_formatAmount(challenge.myProgress!.currentValue)} / ${_formatAmount(challenge.myProgress!.targetValue)} ${challenge.myProgress!.unit}',
                            style: const TextStyle(color: Colors.grey, fontSize: 12),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: challenge.myProgress!.percentage / 100,
                        backgroundColor: Colors.grey[200],
                        valueColor: AlwaysStoppedAnimation<Color>(
                          challenge.myProgress!.percentage >= 100 
                              ? Colors.green 
                              : const Color(0xFF00D4A3),
                        ),
                        minHeight: 6,
                      ),
                      const SizedBox(height: 16),
                    ],
                  ),

                // Statisztikák
                Row(
                  children: [
                    Expanded(
                      child: Row(
                        children: [
                          Icon(Icons.people, size: 16, color: Colors.grey[600]),
                          const SizedBox(width: 4),
                          Text(
                            '${challenge.participantCount} ${'participants'.tr()}',
                            style: TextStyle(color: Colors.grey[600], fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: Row(
                        children: [
                          Icon(Icons.timer, size: 16, color: Colors.grey[600]),
                          const SizedBox(width: 4),
                          Text(
                            '${challenge.durationDays} ${'days'.tr()}',
                            style: TextStyle(color: Colors.grey[600], fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    Row(
                      children: [
                        Icon(Icons.star, size: 16, color: Colors.grey[600]),
                        const SizedBox(width: 4),
                        Text(
                          '${challenge.rewards.points} ${'points'.tr()}',
                          style: TextStyle(color: Colors.grey[600], fontSize: 12),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildChallengesList(List<Challenge> challenges) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00D4A3)));
    }

    if (_error.isNotEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(_error, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadChallenges,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00D4A3),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text('retry'.tr()),
            ),
          ],
        ),
      );
    }

    if (challenges.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.emoji_events_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'no_challenges_available'.tr(),
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 8),
            Text(
              'try_different_filters'.tr(),
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadChallenges,
      color: const Color(0xFF00D4A3),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: challenges.length,
        itemBuilder: (context, index) {
          final challenge = challenges[index];
          return _buildChallengeCard(challenge);
        },
      ),
    );
  }

  Color _getTypeColor(ChallengeType type) {
    switch (type) {
      case ChallengeType.savings:
        return Colors.green;
      case ChallengeType.expenseReduction:
        return Colors.red;
      case ChallengeType.habitStreak:
        return Colors.purple;
      case ChallengeType.budgetControl:
        return Colors.blue;
      case ChallengeType.investment:
        return Colors.orange;
      case ChallengeType.incomeBoost:
        return Colors.teal;
    }
  }

  Color _getDifficultyColor(ChallengeDifficulty difficulty) {
    switch (difficulty) {
      case ChallengeDifficulty.easy:
        return Colors.green;
      case ChallengeDifficulty.medium:
        return Colors.orange;
      case ChallengeDifficulty.hard:
        return Colors.red;
      case ChallengeDifficulty.expert:
        return Colors.purple;
    }
  }

  String _formatAmount(double amount) {
    if (amount >= 1000000) {
      return '${(amount / 1000000).toStringAsFixed(1)}M';
    } else if (amount >= 1000) {
      return '${(amount / 1000).toStringAsFixed(0)}k';
    } else {
      return amount.toStringAsFixed(0);
    }
  }
}