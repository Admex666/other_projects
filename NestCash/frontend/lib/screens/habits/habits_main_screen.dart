// lib/screens/habits/habits_main_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/models/habit.dart';
import 'package:frontend/services/habit_service.dart';
import 'package:frontend/screens/habits/add_habit_screen.dart';
import 'package:frontend/screens/habits/habit_detail_screen.dart';
import 'package:provider/provider.dart';
import 'package:frontend/providers/subscription_provider.dart';
import 'package:frontend/widgets/subscription/usage_indicator.dart';
import 'package:frontend/utils/subscription_utils.dart';
import 'package:frontend/models/subscription.dart';
import 'package:easy_localization/easy_localization.dart';

class HabitsMainScreen extends StatefulWidget {
  final String userId;
  final String username;

  const HabitsMainScreen({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _HabitsMainScreenState createState() => _HabitsMainScreenState();
}

class _HabitsMainScreenState extends State<HabitsMainScreen> {
  final HabitService _habitService = HabitService();
  
  List<Habit> _habits = [];
  UserHabitOverview? _overview;
  bool _isLoading = true;
  bool _isCheckingFeatureAccess = false;
  String _errorMessage = '';
  
  HabitCategory? _selectedCategory;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final habits = await _habitService.getHabits(
        activeOnly: true,
        category: _selectedCategory,
      );

      UserHabitOverview? overview;
      try {
        overview = await _habitService.getUserHabitOverview();
      } catch (e) {
        print('Overview loading failed: $e');
        overview = UserHabitOverview(
          totalHabits: habits.length,
          activeHabits: habits.where((h) => h.isActive).length,
          archivedHabits: habits.where((h) => !h.isActive).length,
          completedToday: habits.where((h) => h.isCompletedToday ?? false).length,
          currentAverageStreak: habits.isNotEmpty 
              ? habits.map((h) => h.streakCount).reduce((a, b) => a + b) / habits.length 
              : 0.0,
          bestOverallStreak: habits.isNotEmpty 
              ? habits.map((h) => h.bestStreak).reduce((a, b) => a > b ? a : b) 
              : 0,
          categoriesBreakdown: _calculateCategoryBreakdown(habits),
        );
      }

      setState(() {
        _habits = habits;
        _overview = overview;
        _isLoading = false;
      });
      
      // *** MÓDOSÍTVA: Async módon frissítjük a provider-t ***
      final subscriptionProvider = context.read<SubscriptionProvider>();
      
      // Ne várjunk rá, hogy ne blokkolja a UI-t, de frissítsük a cache-t
      subscriptionProvider.getCurrentHabitsCount().then((_) {
        // Opcionálisan értesíthetjük a provider-t ha szükséges
      }).catchError((e) {
        debugPrint('habits.error_updating_count'.tr(namedArgs: {'error': e.toString()}));
      });
      
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  // Új metódus - jogosultság ellenőrzés
  Future<bool> _checkCanCreateHabit() async {
    final subscriptionProvider = context.read<SubscriptionProvider>();
    
    try {
      setState(() => _isCheckingFeatureAccess = true);
      
      // Most már az adatbázisból kéri le a tényleges számot
      final canCreate = await subscriptionProvider.canCreateHabit();
      
      if (!canCreate) {
        _showHabitLimitReached();
        return false;
      }
      
      return true;
    } catch (e) {
      debugPrint('habits.error_checking_permission'.tr(namedArgs: {'error': e.toString()}));
      
      // Fallback: cached érték alapján
      if (subscriptionProvider.currentTier == SubscriptionTier.free && 
          subscriptionProvider.cachedHabitsCount >= 5) {
        _showHabitLimitReached();
        return false;
      }
      return true;
    } finally {
      setState(() => _isCheckingFeatureAccess = false);
    }
  }

  void _showHabitLimitReached() {
    SubscriptionUtils.showUpgradeDialog(
      context,
      feature: 'habits.habit_limit_reached_title'.tr(),
      description: 'habits.habit_limit_reached_desc'.tr(),
      requiredTier: SubscriptionTier.plus,
    );
  }

  Future<void> _onAddHabitPressed() async {
    if (_isCheckingFeatureAccess) return;
    
    final canCreate = await _checkCanCreateHabit();
    if (!canCreate) return;
    
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AddHabitScreen(userId: widget.userId),
      ),
    );
    
    if (result == true) {
      _loadData();
      // Cache frissítése a provider-ben
      final subscriptionProvider = context.read<SubscriptionProvider>();
      subscriptionProvider.getCurrentHabitsCount();
    }
  }

  Map<String, int> _calculateCategoryBreakdown(List<Habit> habits) {
    final Map<String, int> breakdown = {};
    for (final habit in habits) {
      final category = habit.category.value;
      breakdown[category] = (breakdown[category] ?? 0) + 1;
    }
    return breakdown;
  }

  Future<void> _toggleHabitCompletion(Habit habit) async {
    try {
      final isCompleted = habit.isCompletedToday ?? false;
      
      await _habitService.logHabitCompletion(
        habit.id,
        completed: !isCompleted,
        value: habit.trackingType == TrackingType.numeric && !isCompleted ? 1.0 : null,
      );

      await _loadData();

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            !isCompleted 
                ? 'habits.habit_completed'.tr(namedArgs: {'habitTitle': habit.title})
                : 'habits.habit_uncompleted'.tr(namedArgs: {'habitTitle': habit.title}),
          ),
          backgroundColor: Color(0xFF00D4AA),
          duration: const Duration(seconds: 2),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('habits.error_toggle_completion'.tr(namedArgs: {'error': e.toString()})),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildOverviewCard() {
    if (_overview == null) return const SizedBox.shrink();

    final completionRate = _overview!.activeHabits > 0 
        ? (_overview!.completedToday / _overview!.activeHabits) * 100 
        : 0.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'habits.today_performance'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 16),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'habits.completed_habits'.tr(),
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
              Text(
                '${_overview!.completedToday}/${_overview!.activeHabits}',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF00D4AA),
                ),
              ),
            ],
          ),
          
          const SizedBox(height: 12),
          
          LinearProgressIndicator(
            value: completionRate / 100,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(
              completionRate >= 100 
                  ? Colors.green 
                  : completionRate >= 50 
                      ? Colors.orange 
                      : Colors.red,
            ),
            minHeight: 6,
          ),
          
          const SizedBox(height: 8),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${completionRate.toStringAsFixed(1)}% ' + 'completed'.tr(),
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
              Row(
                children: [
                  _buildStatItem('habits.average_streak'.tr(), 
                    _overview!.currentAverageStreak.toStringAsFixed(1),
                    Colors.blue),
                  SizedBox(width: 16),
                  _buildStatItem('habits.best_streak'.tr(), 
                    _overview!.bestOverallStreak.toString(),
                    Colors.orange),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildCategoryFilter() {
    return Container(
      height: 50,
      margin: EdgeInsets.only(bottom: 16),
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.symmetric(horizontal: 24),
        children: [
          _buildCategoryChip('habits.all'.tr(), null),
          SizedBox(width: 8),
          ...HabitCategory.values.map(
            (category) => Padding(
              padding: EdgeInsets.only(right: 8),
              child: _buildCategoryChip(category.value.tr(), category),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryChip(String label, HabitCategory? category) {
    final isSelected = _selectedCategory == category;
    
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() {
          _selectedCategory = selected ? category : null;
        });
        _loadData();
      },
      backgroundColor: Colors.white,
      selectedColor: Color(0xFF00D4AA).withOpacity(0.2),
      checkmarkColor: Color(0xFF00D4AA),
      labelStyle: TextStyle(
        color: isSelected ? Color(0xFF00D4AA) : Colors.grey[700],
        fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: isSelected ? Color(0xFF00D4AA) : Colors.grey[300]!,
        ),
      ),
    );
  }

  Widget _buildHabitCard(Habit habit) {
    final isCompleted = habit.isCompletedToday ?? false;
    final streakColor = habit.streakCount > 0 ? Color(0xFF00D4AA) : Colors.grey;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => HabitDetailScreen(
                habitId: habit.id,
                userId: widget.userId,
              ),
            ),
          );
          
          if (result == true) {
            _loadData();
          }
        },
        borderRadius: BorderRadius.circular(15),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              // Completion button
              GestureDetector(
                onTap: () => _toggleHabitCompletion(habit),
                child: Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isCompleted 
                        ? Color(0xFF00D4AA) 
                        : Colors.grey[200],
                    border: Border.all(
                      color: isCompleted 
                          ? Color(0xFF00D4AA) 
                          : Colors.grey[400]!,
                      width: 2,
                    ),
                  ),
                  child: Icon(
                    isCompleted ? Icons.check : Icons.circle_outlined,
                    color: isCompleted ? Colors.white : Colors.grey[400],
                    size: 24,
                  ),
                ),
              ),
              
              const SizedBox(width: 16),
              
              // Habit info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      habit.title,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: isCompleted ? Colors.grey[600] : Colors.black87,
                        decoration: isCompleted 
                            ? TextDecoration.lineThrough 
                            : null,
                      ),
                    ),
                    if (habit.description != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        habit.description!,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getCategoryColor(habit.category).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            habit.category.value.tr(),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: _getCategoryColor(habit.category),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.blue.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            habit.frequency.displayName,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: Colors.blue[700],
                            ),
                          ),
                        ),
                        if (habit.hasGoal && habit.usagePercentage != null) ...[
                          const SizedBox(width: 8),
                          _buildProgressChip(habit),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              
              // Streak info
              Column(
                children: [
                  Icon(
                    Icons.local_fire_department,
                    color: streakColor,
                    size: 24,
                  ),
                  Text(
                    habit.streakCount.toString(),
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: streakColor,
                    ),
                  ),
                  Text(
                    'habits.days'.tr(),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[500],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressChip(Habit habit) {
    final percentage = habit.usagePercentage ?? 0.0;
    final color = percentage >= 100 
        ? Colors.green 
        : percentage >= 50 
            ? Colors.orange 
            : Colors.red;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '${percentage.toInt()}%',
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: color,
        ),
      ),
    );
  }

  Widget _buildUsageIndicator() {
    return Consumer<SubscriptionProvider>(
      builder: (context, subscriptionProvider, child) {
        final currentTier = subscriptionProvider.currentTier;
        final habitsLimit = currentTier == SubscriptionTier.free ? 5 : null;
        
        return FutureBuilder<int>(
          // Adatbázisból kérjük le minden alkalommal
          future: subscriptionProvider.getCurrentHabitsCount(),
          builder: (context, snapshot) {
            // Loading közben a cached értéket mutatjuk
            final habitsCount = snapshot.data ?? subscriptionProvider.cachedHabitsCount;
            
            return UsageIndicator(
              featureName: 'habits.title'.tr(),
              current: habitsCount,
              limit: habitsLimit,
              onUpgradePressed: () => SubscriptionUtils.showUpgradeDialog(
                context,
                feature: 'habits.unlimited_tracking'.tr(),
                requiredTier: SubscriptionTier.plus,
              ),
            );
          },
        );
      },
    );
  }

  Color _getCategoryColor(HabitCategory category) {
    switch (category) {
      case HabitCategory.financial:
        return Colors.green;
      case HabitCategory.savings:
        return Colors.blue;
      case HabitCategory.investment:
        return Colors.purple;
      case HabitCategory.other:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: Icon(
                      Icons.arrow_back,
                      color: Colors.black87,
                      size: 24,
                    ),
                  ),
                  Expanded(
                    child: Text(
                      'habits.title'.tr(),
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  IconButton(
                    onPressed: _loadData,
                    icon: Icon(
                      Icons.refresh,
                      color: Colors.black87,
                      size: 24,
                    ),
                  ),
                ],
              ),
            ),
            
            // Content Container
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: _isLoading
                    ? Center(
                        child: CircularProgressIndicator(
                          color: Color(0xFF00D4AA),
                        ),
                      )
                    : _errorMessage.isNotEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(24),
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
                                    'habits.error_occurred'.tr(),
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    _errorMessage,
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      color: Colors.grey[500],
                                    ),
                                  ),
                                  const SizedBox(height: 24),
                                  Container(
                                    width: double.infinity,
                                    height: 48,
                                    child: ElevatedButton(
                                      onPressed: _loadData,
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Color(0xFF00D4AA),
                                        foregroundColor: Colors.white,
                                        elevation: 0,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                      ),
                                      child: Text(
                                        'habits.retry'.tr(),
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          )
                        : SingleChildScrollView(
                            child: Column(
                              children: [
                                SizedBox(height: 10),
                                
                                // Usage Indicator hozzáadása
                                _buildUsageIndicator(),
                                SizedBox(height: 16),
                                
                                // Add button módosítása - betöltés állapot és jogosultság ellenőrzés
                                Container(
                                  width: double.infinity,
                                  height: 48,
                                  child: Consumer<SubscriptionProvider>(
                                    builder: (context, subscriptionProvider, child) {
                                      return FutureBuilder<int>(
                                        future: subscriptionProvider.getCurrentHabitsCount(),
                                        builder: (context, snapshot) {
                                          final habitsCount = snapshot.data ?? _habits.length;
                                          final isAtLimit = subscriptionProvider.currentTier == SubscriptionTier.free && 
                                                          habitsCount >= 5;
                                          
                                          return ElevatedButton.icon(
                                            onPressed: _isCheckingFeatureAccess ? null : _onAddHabitPressed,
                                            icon: _isCheckingFeatureAccess 
                                                ? SizedBox(
                                                    width: 16,
                                                    height: 16,
                                                    child: CircularProgressIndicator(strokeWidth: 2),
                                                  )
                                                : Icon(
                                                    isAtLimit ? Icons.lock : Icons.add,
                                                    color: Colors.white,
                                                  ),
                                            label: Text(
                                              isAtLimit ? 'habits.upgrade_needed'.tr() : 'habits.new_habit'.tr(),
                                              style: TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.w600,
                                                color: Colors.white,
                                              ),
                                            ),
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: isAtLimit ? Colors.grey : Colors.orange,
                                              elevation: 0,
                                              shape: RoundedRectangleBorder(
                                                borderRadius: BorderRadius.circular(12),
                                              ),
                                            ),
                                          );
                                        },
                                      );
                                    },
                                  ),
                                ),

                                SizedBox(height: 24),

                                _buildOverviewCard(),
                                
                                _buildCategoryFilter(),

                                // Empty state módosítása jogosultság-tudatos üzenettel
                                if (_habits.isEmpty)
                                  Consumer<SubscriptionProvider>(
                                    builder: (context, subscriptionProvider, child) {
                                      return FutureBuilder<int>(
                                        future: subscriptionProvider.getCurrentHabitsCount(),
                                        builder: (context, snapshot) {
                                          final isAtLimit = subscriptionProvider.currentTier == SubscriptionTier.free;
                                          
                                          return Container(
                                            padding: const EdgeInsets.all(40),
                                            child: Column(
                                              children: [
                                                Icon(
                                                  Icons.psychology_outlined,
                                                  size: 64,
                                                  color: Colors.grey[400],
                                                ),
                                                const SizedBox(height: 16),
                                                Text(
                                                  'habits.no_habits_yet'.tr(),
                                                  style: TextStyle(
                                                    fontSize: 18,
                                                    fontWeight: FontWeight.w600,
                                                    color: Colors.grey[600],
                                                  ),
                                                ),
                                                const SizedBox(height: 8),
                                                Text(
                                                  isAtLimit 
                                                      ? 'habits.free_version_info'.tr()
                                                      : 'habits.first_habit_info'.tr(),
                                                  style: TextStyle(
                                                    color: Colors.grey[500],
                                                  ),
                                                  textAlign: TextAlign.center,
                                                ),
                                                if (isAtLimit) ...[
                                                  const SizedBox(height: 16),
                                                  TextButton.icon(
                                                    onPressed: () => SubscriptionUtils.showUpgradeDialog(
                                                      context,
                                                      feature: 'habits.unlimited_tracking'.tr(),
                                                      requiredTier: SubscriptionTier.plus,
                                                    ),
                                                    icon: Icon(Icons.upgrade),
                                                    label: Text('habits.unlimited_tracking'.tr()),
                                                  ),
                                                ],
                                              ],
                                            ),
                                          );
                                        },
                                      );
                                    },
                                  )
                                else
                                  ...(_habits.map((habit) => _buildHabitCard(habit)).toList()),

                                SizedBox(height: 100), // Extra space for FAB
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                floatingActionButton: Consumer<SubscriptionProvider>(
                  builder: (context, subscriptionProvider, child) {
                    return FutureBuilder<int>(
                      future: subscriptionProvider.getCurrentHabitsCount(),
                      builder: (context, snapshot) {
                        final habitsCount = snapshot.data ?? _habits.length;
                        final isAtLimit = subscriptionProvider.currentTier == SubscriptionTier.free && 
                                        habitsCount >= 5;
                        
                        return FloatingActionButton(
                          onPressed: _isCheckingFeatureAccess ? null : _onAddHabitPressed,
                          backgroundColor: isAtLimit ? Colors.grey : Colors.orange,
                          child: _isCheckingFeatureAccess
                              ? SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation(Colors.white),
                                  ),
                                )
                              : Icon(
                                  isAtLimit ? Icons.lock : Icons.add,
                                  color: Colors.white,
                                ),
                        );
                      },
                    );
                  },
                ),
    );
  }
}