// lib/screens/profile/badges_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/badge_service.dart';
import 'package:frontend/models/badge_models.dart';
import 'package:frontend/services/sharing_service.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/utils/category_translate.dart';

class BadgesScreen extends StatefulWidget {
  final String userId;

  const BadgesScreen({
    Key? key, 
    required this.userId, 
  }) : super(key: key);

  @override
  _BadgesScreenState createState() => _BadgesScreenState();
}

class _BadgesScreenState extends State<BadgesScreen> with SingleTickerProviderStateMixin {
  final BadgeService _badgeService = BadgeService();
  late TabController _tabController;
  
  List<UserBadge> _myBadges = [];
  List<BadgeProgress> _progressList = [];
  BadgeStats? _badgeStats;
  bool _isLoading = true;
  String _error = '';
  BadgeCategory? _selectedCategory;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadBadgeData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadBadgeData() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      // Badge-ek lekérése
      final badgesResponse = await _badgeService.getUserBadges(
        category: _selectedCategory?.value
      );
      
      // Haladás lekérése
      final progressResponse = await _badgeService.getBadgeProgress();
      
      // Statisztikák lekérése
      final statsResponse = await _badgeService.getBadgeStats();

      if (badgesResponse != null) {
        _myBadges = (badgesResponse['badges'] as List<dynamic>)
            .map((badge) => UserBadge.fromJson(badge))
            .toList();
      }

      if (progressResponse != null) {
        _progressList = (progressResponse['progress_list'] as List<dynamic>)
            .map((progress) => BadgeProgress.fromJson(progress))
            .toList();
      }

      if (statsResponse != null) {
        _badgeStats = BadgeStats.fromJson(statsResponse);
      }

    } catch (e) {
      setState(() {
        _error = 'error_occured'.tr(namedArgs: {'error': e.toString()});
      });
    }

    setState(() => _isLoading = false);
  }

  void _showFilterBottomSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        maxChildSize: 0.7,
        minChildSize: 0.3,
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
                        style: const TextStyle(
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
                      // Kategória szűrő
                      Text(
                        'category'.tr(),
                        style: const TextStyle(
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
                            _selectedCategory == null,
                            () {
                              setState(() => _selectedCategory = null);
                              Navigator.pop(context);
                              _loadBadgeData();
                            },
                          ),
                          ...BadgeCategory.values.map((category) => _buildFilterChip(
                            CategoryTranslate.getLocalizedBadgeCategory(category.displayName).tr(),
                            _selectedCategory == category,
                            () {
                              setState(() => _selectedCategory = _selectedCategory == category ? null : category);
                              Navigator.pop(context);
                              _loadBadgeData();
                            },
                          )),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      body: SafeArea(
        child: Column(
          children: [
            // Header - ChallengesMainScreen stílusában
            Container(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
              decoration: BoxDecoration(
                color: const Color(0xFF00D4A3),
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
                  // Back arrow és cím
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
                          'badges'.tr(),
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
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
                              hintText: 'search_badges_hint'.tr(),
                              prefixIcon: const Icon(Icons.search, color: Color(0xFF00D4A3)),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                              hintStyle: const TextStyle(color: Colors.grey),
                            ),
                            onSubmitted: (_) => _loadBadgeData(),
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
            ),

            // Tab Bar
            Container(
              color: Colors.white,
              child: TabBar(
                controller: _tabController,
                tabs: [
                  Tab(text: 'my_badges_tab'.tr()),
                  Tab(text: 'progress_tab'.tr()),
                  Tab(text: 'stats_tab'.tr()),
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
                  _buildMyBadgesTab(),
                  _buildProgressTab(),
                  _buildStatsTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMyBadgesTab() {
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
              onPressed: _loadBadgeData,
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

    if (_myBadges.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.emoji_events_outlined, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              'no_badges_title'.tr(),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              'no_badges_subtitle'.tr(),
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadBadgeData,
      color: const Color(0xFF00D4A3),
      child: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.8,
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
        ),
        itemCount: _myBadges.length,
        itemBuilder: (context, index) {
          return _buildBadgeCard(_myBadges[index]);
        },
      ),
    );
  }

  Widget _buildProgressTab() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00D4A3)));
    }

    if (_progressList.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.trending_up_outlined, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              'no_progress_title'.tr(),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              'no_progress_subtitle'.tr(),
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadBadgeData,
      color: const Color(0xFF00D4A3),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _progressList.length,
        itemBuilder: (context, index) {
          return _buildProgressCard(_progressList[index]);
        },
      ),
    );
  }

  Widget _buildStatsTab() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00D4A3)));
    }

    if (_badgeStats == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.bar_chart_outlined, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              'no_stats_title'.tr(),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadBadgeData,
      color: const Color(0xFF00D4A3),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Összesítő kártyák
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    'total_badges'.tr(),
                    _badgeStats!.totalBadges.toString(),
                    Icons.emoji_events,
                    Colors.orange,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildStatCard(
                    'total_points'.tr(),
                    _badgeStats!.totalPoints.toString(),
                    Icons.stars,
                    Colors.blue,
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 24),
            
            // Kategória szerint
            Text(
              'badges_by_category'.tr(),
              style: const TextStyle(
                fontSize: 18, 
                fontWeight: FontWeight.bold,
                color: Color(0xFF2D3748),
              ),
            ),
            const SizedBox(height: 16),
            ..._badgeStats!.badgesByCategory.entries.map((entry) {
              final category = BadgeCategory.values.firstWhere(
                (cat) => cat.value == entry.key,
                orElse: () => BadgeCategory.transaction,
              );
              return _buildCategoryStatItem(CategoryTranslate.getLocalizedBadgeCategory(category.displayName).tr(), entry.value);
            }),
            
            const SizedBox(height: 24),
            
            // Ritkaság szerint
            Text(
              'badges_by_rarity'.tr(),
              style: const TextStyle(
                fontSize: 18, 
                fontWeight: FontWeight.bold,
                color: Color(0xFF2D3748),
              ),
            ),
            const SizedBox(height: 16),
            ..._badgeStats!.badgesByRarity.entries.map((entry) {
              final rarity = BadgeRarity.values.firstWhere(
                (rar) => rar.value == entry.key,
                orElse: () => BadgeRarity.common,
              );
              return _buildRarityStatItem(rarity, entry.value);
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildBadgeCard(UserBadge badge) {
    return Container(
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
          onTap: () => _showBadgeDetails(badge),
          borderRadius: BorderRadius.circular(15),
          child: Stack(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Badge ikon
                    Text(
                      badge.badgeIcon ?? '🏆',
                      style: const TextStyle(fontSize: 36),
                    ),
                    const SizedBox(height: 12),
                    
                    // Badge név
                    Text(
                      badge.badgeName ?? badge.badgeCode,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Color(0xFF2D3748),
                      ),
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 8),
                    
                    // Ritkaság
                    if (badge.badgeRarity != null)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: _getRarityColor(badge.badgeRarity!),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          badge.badgeRarity!.displayName.tr(),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    
                    const SizedBox(height: 8),
                    
                    // Szint és pontok
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        if (badge.level > 1)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0xFF00D4A3),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              'level_abbr'.tr(namedArgs: {'level': badge.level.toString()}),
                              style: const TextStyle(
                                fontSize: 10, 
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        if (badge.badgePoints != null)
                          Row(
                            children: [
                              const Icon(Icons.star, size: 12, color: Colors.orange),
                              const SizedBox(width: 2),
                              Text(
                                '${badge.badgePoints}',
                                style: const TextStyle(
                                  fontSize: 14, 
                                  color: Colors.orange,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              
              // Kedvenc ikon
              if (badge.isFavorite)
                const Positioned(
                  top: 8,
                  right: 8,
                  child: Icon(Icons.favorite, color: Colors.red, size: 16),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressCard(BadgeProgress progress) {
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
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  progress.badgeIcon ?? '🏆',
                  style: const TextStyle(fontSize: 28),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        progress.badgeName ?? progress.badgeCode,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                          color: Color(0xFF2D3748),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        progress.badgeDescription ?? '',
                        style: const TextStyle(
                          color: Colors.grey, 
                          fontSize: 14,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00D4A3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${progress.progressPercentage.toInt()}%',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            LinearProgressIndicator(
              value: progress.progressPercentage / 100,
              backgroundColor: Colors.grey[200],
              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
              minHeight: 6,
            ),
            const SizedBox(height: 8),
            Text(
              '${progress.currentValue.toInt()} / ${progress.targetValue.toInt()}',
              style: const TextStyle(
                fontSize: 12, 
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
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
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Icon(icon, color: color, size: 36),
            const SizedBox(height: 12),
            Text(
              value,
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              title,
              style: const TextStyle(
                color: Colors.grey,
                fontSize: 14,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryStatItem(String category, int count) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.05),
            blurRadius: 5,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              category,
              style: const TextStyle(
                fontSize: 16,
                color: Color(0xFF2D3748),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF00D4A3),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                count.toString(),
                style: const TextStyle(
                  color: Colors.white, 
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRarityStatItem(BadgeRarity rarity, int count) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.05),
            blurRadius: 5,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Text(rarity.colorEmoji),
                const SizedBox(width: 12),
                Text(
                  CategoryTranslate.getLocalizedBadgeRarity(rarity.displayName).tr(),
                  style: const TextStyle(
                    fontSize: 16,
                    color: Color(0xFF2D3748),
                  ),
                ),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getRarityColor(rarity),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                count.toString(),
                style: const TextStyle(
                  color: Colors.white, 
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getRarityColor(BadgeRarity rarity) {
    switch (rarity) {
      case BadgeRarity.common:
        return Colors.grey;
      case BadgeRarity.uncommon:
        return Colors.green;
      case BadgeRarity.rare:
        return Colors.blue;
      case BadgeRarity.epic:
        return Colors.purple;
      case BadgeRarity.legendary:
        return Colors.orange;
    }
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Text(
            label,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: Color(0xFF2D3748),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(color: Colors.grey),
            ),
          ),
        ],
      ),
    );
  }

  void _showBadgeDetails(UserBadge badge) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        title: Row(
          children: [
            Text(badge.badgeIcon ?? '🏆', style: const TextStyle(fontSize: 28)),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                badge.badgeName ?? badge.badgeCode,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2D3748),
                ),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (badge.badgeDescription != null)
              Text(
                badge.badgeDescription!,
                style: const TextStyle(fontSize: 16),
              ),
            const SizedBox(height: 16),
            _buildDetailRow(
              'earned_at_label'.tr(), 
              '${badge.earnedAt.year}/${badge.earnedAt.month.toString().padLeft(2, '0')}/${badge.earnedAt.day.toString().padLeft(2, '0')}'
            ),
            if (badge.level > 1)
              _buildDetailRow('level_label'.tr(), badge.level.toString()),
            if (badge.badgePoints != null)
              _buildDetailRow('points_label'.tr(), badge.badgePoints.toString()),
            if (badge.badgeRarity != null)
              _buildDetailRow('rarity_label'.tr(), badge.badgeRarity!.displayName.tr()),
            
            // Megosztás gomb hozzáadása
            const SizedBox(height: 16),
            Center(
              child: ShareAchievementButton(
                achievementType: 'badge',
                achievementId: badge.id,
                achievementName: badge.badgeName ?? badge.badgeCode,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () async {
              final success = await _badgeService.updateBadge(
                badge.id,
                isFavorite: !badge.isFavorite,
              );
              if (success) {
                Navigator.of(context).pop();
                _loadBadgeData();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(badge.isFavorite 
                        ? 'removed_from_favorites'.tr()
                        : 'added_to_favorites'.tr()),
                    backgroundColor: const Color(0xFF00D4A3),
                  ),
                );
              }
            },
            child: Text(
              badge.isFavorite ? 'remove_from_favorites'.tr() : 'add_to_favorites'.tr(),
              style: const TextStyle(color: Color(0xFF00D4A3)),
            ),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text(
              'close'.tr(),
              style: const TextStyle(color: Color(0xFF00D4A3)),
            ),
          ),
        ],
      ),
    );
  }
}