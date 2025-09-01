// lib/screens/pti/pti_main_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';
import 'package:frontend/screens/pti/pti_ranking_screen.dart';
import 'package:frontend/screens/pti/pti_settings_screen.dart';
import 'package:frontend/screens/pti/pti_comparison_screen.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/screens/pti/pti_component_ranking_screen.dart';
import 'package:easy_localization/easy_localization.dart';

class PTIMainScreen extends StatefulWidget {
  final String userId;

  const PTIMainScreen({
    Key? key,
    required this.userId,
  }) : super(key: key);

  @override
  _PTIMainScreenState createState() => _PTIMainScreenState();
}

class _PTIMainScreenState extends State<PTIMainScreen> {
  final PTIService _ptiService = PTIService();
  final AuthService _authService = AuthService(); // Hozzáadás
  PTIDashboardResponse? _dashboardData;
  PTIPeriodInfo? _periodInfo; // Új
  String? _username; // Hozzáadás
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    if (!mounted) return; // Ellenőrzés a metódus elején
    
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Username lekérése az AuthService-ből
      final username = await _authService.getCurrentUsername();
      if (username != null) {
        if (!mounted) return; // Ellenőrzés aszinkron művelet után
        setState(() {
          _username = username;
        });
        await _loadDashboard();
      } else {
        if (!mounted) return; // Ellenőrzés aszinkron művelet után
        setState(() {
          _error = 'pti.load_error'.tr();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return; // Ellenőrzés catch blokban
      setState(() {
        _error = 'pti.error'.tr(namedArgs: {'error': e.toString()});
        _isLoading = false;
      });
    }
  }

  Future<void> _loadDashboard() async {
    // A korábbi _isLoading és _error beállítás eltávolítható innen,
    // mivel a _loadUserData kezeli
    try {
      final dashboard = await _ptiService.getDashboard();
      if (dashboard != null) {
        if (!mounted) return; // Ellenőrzés aszinkron művelet után
        setState(() {
          _dashboardData = dashboard;
          _isLoading = false;
        });
      } else {
        if (!mounted) return; // Ellenőrzés aszinkron művelet után
        setState(() {
          _error = 'pti.load_pti_error'.tr();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return; // Ellenőrzés catch blokban
      setState(() {
        _error = 'pti.error'.tr(namedArgs: {'error': e.toString()});
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(
          'pti.title'.tr(),
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.settings, color: Colors.black),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => PTISettingsScreen(
                    userId: widget.userId,
                  ),
                ),
              ).then((_) => _loadDashboard());
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadUserData,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              _error!,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadDashboard,
              child: Text('pti.retry'.tr()),
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4A3),
              ),
            ),
          ],
        ),
      );
    }

    if (_dashboardData == null) {
      return Center(
        child: Text(
          'pti.no_data'.tr(),
          style: TextStyle(
            fontSize: 16,
            color: Colors.grey[600],
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // PTI Összefoglaló kártya
          _buildPTISummaryCard(),
          SizedBox(height: 16),
          
          // Komponensek részletezése
          _buildComponentsCard(),
          SizedBox(height: 16),
          
          // Rangsorok
          _buildRankingsCard(),
          SizedBox(height: 16),
          
          // Célok (ha vannak)
          if (_dashboardData!.weeklyGoalProgress != null || 
              _dashboardData!.monthlyGoalProgress != null)
            _buildGoalsCard(),
          
          if (_dashboardData!.weeklyGoalProgress != null || 
              _dashboardData!.monthlyGoalProgress != null)
            SizedBox(height: 16),
          
          // Fejlesztési javaslatok
          if (_dashboardData!.nextActions.isNotEmpty)
            _buildSuggestionsCard(),
          
          if (_dashboardData!.nextActions.isNotEmpty)
            SizedBox(height: 16),
          
          // Gyors műveletek
          _buildQuickActionsCard(),
        ],
      ),
    );
  }

  Widget _buildPTISummaryCard() {
    final pti = _dashboardData!.currentPti;
    
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF00D4A3), Color(0xFF00B894)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Color(0xFF00D4A3).withOpacity(0.3),
            blurRadius: 20,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'pti.current_score'.tr(),
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                'pti.updated'.tr(namedArgs: {'date': _formatDate(pti.calculatedAt)}),
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 12,
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          
          // PTI Score
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                '${pti.ptiScore.toStringAsFixed(1)}',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                ' / 100',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.8),
                  fontSize: 20,
                ),
              ),
              Spacer(),
              if (pti.rank != null)
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.emoji_events,
                        color: Colors.white,
                        size: 20,
                      ),
                      SizedBox(width: 6),
                      Text(
                        'pti.rank'.tr(namedArgs: {'rank': pti.rank.toString()}),
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          SizedBox(height: 20),
          
          // Progress bar
          Container(
            height: 8,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: pti.ptiScore / 100,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ),
          SizedBox(height: 12),
          
          // Score interpretation
          Text(
            _getScoreInterpretation(pti.ptiScore),
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 14,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildComponentsCard() {
    final components = _dashboardData!.currentPti.components;
    
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'pti.components'.tr(),
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              TextButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PTIComponentRankingScreen(
                        userId: widget.userId,
                        username: _username!,
                      ),
                    ),
                  );
                },
                icon: Icon(
                  Icons.leaderboard,
                  size: 16,
                  color: Color(0xFF00D4A3),
                ),
                label: Text(
                  'pti.all_rankings'.tr(),
                  style: TextStyle(
                    color: Color(0xFF00D4A3),
                    fontWeight: FontWeight.w600,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          
          // Info szöveg, hogy jelezzük a felhasználónak, hogy a komponensek kattinthatók
          Container(
            padding: EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Color(0xFF00D4A3).withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: Color(0xFF00D4A3).withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.info_outline,
                  color: Color(0xFF00D4A3),
                  size: 16,
                ),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'pti.tap_info'.tr(),
                    style: TextStyle(
                      fontSize: 12,
                      color: Color(0xFF00D4A3),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 20),
          
          _buildComponentItem(
            '📚 Tanulás',
            components.learningContribution,
            30,
            Colors.blue,
            'pti.component_descriptions.learning'.tr(),
            PTIComponent.learning,
          ),
          SizedBox(height: 16),
          
          _buildComponentItem(
            '💪 Szokások',
            components.habitContribution,
            30,
            Colors.green,
            'pti.component_descriptions.habits'.tr(),
            PTIComponent.habits,
          ),
          SizedBox(height: 16),
          
          _buildComponentItem(
            '🏆 Kitűzők',
            components.badgeContribution,
            20,
            Colors.orange,
            'pti.component_descriptions.badges'.tr(),
            PTIComponent.badges,
          ),
          SizedBox(height: 16),
          
          _buildComponentItem(
            '📊 Limitek',
            components.limitContribution,
            20,
            Colors.purple,
            'pti.component_descriptions.limits'.tr(),
            PTIComponent.limits,
          ),
        ],
      ),
    );
  }

  Widget _buildComponentItem(
    String title,
    double currentScore,
    int maxWeight,
    Color color,
    String description,
    PTIComponent component,
  ) {
    final percentage = (currentScore / maxWeight) * 100;
    
    return InkWell(
      onTap: () {
        // Navigálás az adott komponens ranglistájához
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => PTIComponentRankingScreen(
              userId: widget.userId,
              username: _username!,
              initialComponent: component, // Előre kiválasztott komponens
            ),
          ),
        );
      },
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(width: 8),
                    // Kis ranglista ikon jelzi, hogy kattintható
                    Icon(
                      Icons.leaderboard,
                      size: 16,
                      color: color,
                    ),
                  ],
                ),
                Text(
                  '${currentScore.toStringAsFixed(1)} / $maxWeight',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text(
              description,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
            SizedBox(height: 12),
            
            // Progress bar
            Container(
              height: 8,
              decoration: BoxDecoration(
                color: color.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: (percentage / 100).clamp(0.0, 1.0),
                child: Container(
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
            SizedBox(height: 8),
            
            // Kiegészítő információ row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${percentage.toStringAsFixed(1)}%',
                  style: TextStyle(
                    fontSize: 12,
                    color: color,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  'pti.see_ranking'.tr(),
                  style: TextStyle(
                    fontSize: 11,
                    color: color.withOpacity(0.8),
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRankingsCard() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'pti.rankings'.tr(),
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              TextButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PTIRankingScreen(
                        userId: widget.userId,
                        username: _username!,
                      ),
                    ),
                  );
                },
                child: Text(
                  'pti.view_all'.tr(),
                  style: TextStyle(
                    color: Color(0xFF00D4A3),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: _buildRankingPreview(
                  'pti.weekly'.tr(),
                  _dashboardData!.weeklyRanking?.rank,
                  _dashboardData!.currentPti.totalUsers,
                  Icons.calendar_view_week,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildRankingPreview(
                  'pti.monthly'.tr(),
                  _dashboardData!.monthlyRanking?.rank,
                  _dashboardData!.currentPti.totalUsers,
                  Icons.calendar_month,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildRankingPreview(
                  'pti.yearly'.tr(),
                  _dashboardData!.yearlyRanking?.rank,
                  _dashboardData!.currentPti.totalUsers,
                  Icons.calendar_today,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRankingPreview(
    String period,
    int? rank,
    int? totalUsers,
    IconData icon,
  ) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.grey[50]!, Colors.grey[100]!],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color: Color(0xFF00D4A3),
            size: 24,
          ),
          SizedBox(height: 8),
          Text(
            period,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.grey[700],
            ),
          ),
          SizedBox(height: 4),
          if (rank != null) ...[
            Text(
              '$rank.',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Color(0xFF00D4A3),
              ),
            ),
            Text(
              '/ ${totalUsers ?? 0}',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ] else
            Text(
              'N/A',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[500],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildGoalsCard() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'pti.goals'.tr(),
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          
          if (_dashboardData!.weeklyGoalProgress != null)
            _buildGoalProgress(
              'pti.weekly'.tr(),
              _dashboardData!.weeklyGoalProgress!,
              Icons.calendar_view_week,
              Colors.blue,
            ),
          
          if (_dashboardData!.weeklyGoalProgress != null && 
              _dashboardData!.monthlyGoalProgress != null)
            SizedBox(height: 16),
          
          if (_dashboardData!.monthlyGoalProgress != null)
            _buildGoalProgress(
              'pti.monthly'.tr(),
              _dashboardData!.monthlyGoalProgress!,
              Icons.calendar_month,
              Colors.green,
            ),
        ],
      ),
    );
  }

  Widget _buildGoalProgress(
    String title,
    double progressPercentage,
    IconData icon,
    Color color,
  ) {
    final isAchieved = progressPercentage >= 100;
    
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Spacer(),
              if (isAchieved)
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check, color: Colors.white, size: 12),
                      SizedBox(width: 4),
                      Text(
                        'pti.goal_achieved'.tr(),
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          SizedBox(height: 8),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'pti.goal_progress'.tr(namedArgs: {'progress': progressPercentage.toStringAsFixed(1)}),
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          
          LinearProgressIndicator(
            value: (progressPercentage / 100).clamp(0.0, 1.0),
            backgroundColor: color.withOpacity(0.2),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
        ],
      ),
    );
  }

  Widget _buildSuggestionsCard() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.lightbulb_outline,
                color: Colors.amber[600],
                size: 24,
              ),
              SizedBox(width: 8),
              Text(
                'pti.suggestions'.tr(),
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          
          ..._dashboardData!.nextActions.take(3).map((suggestion) {
            return Container(
              margin: EdgeInsets.only(bottom: 12),
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: Colors.amber[200]!,
                  width: 1,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.amber[700],
                    size: 16,
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      suggestion,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[800],
                      ),
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildQuickActionsCard() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'pti.quick_actions'.tr(),
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: _buildQuickActionButton(
                  'pti.quick_actions_titles.rankings'.tr(),
                  Icons.leaderboard,
                  Color(0xFF00D4A3),
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PTIRankingScreen(
                          userId: widget.userId,
                          username: _username!,
                        ),
                      ),
                    );
                  },
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildQuickActionButton(
                  'pti.quick_actions_titles.comparison'.tr(),
                  Icons.compare_arrows,
                  Colors.blue,
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PTIComparisonScreen(
                          userId: widget.userId,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          
          Row(
            children: [
              Expanded(
                child: _buildQuickActionButton(
                  'pti.quick_actions_titles.refresh'.tr(),
                  Icons.refresh,
                  Colors.orange,
                  () async {
                    await _ptiService.calculatePTI();
                    if (!mounted) return; // Ellenőrzés aszinkron művelet után
                    _loadDashboard();
                    if (!mounted) return; // Ellenőrzés ScaffoldMessenger előtt
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('pti.refresh_success'.tr()),
                        backgroundColor: Color(0xFF00D4A3),
                      ),
                    );
                  },
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildQuickActionButton(
                  'pti.quick_actions_titles.settings'.tr(),
                  Icons.settings,
                  Colors.grey[600]!,
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PTISettingsScreen(
                          userId: widget.userId,
                        ),
                      ),
                    ).then((_) => _loadDashboard());
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionButton(
    String title,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: color.withOpacity(0.3),
            width: 1,
          ),
        ),
        child: Column(
          children: [
            Icon(
              icon,
              color: color,
              size: 28,
            ),
            SizedBox(height: 8),
            Text(
              title,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: color,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);
    
    if (difference.inDays == 0) {
      return 'today'.tr();
    } else if (difference.inDays == 1) {
      return 'yesterday'.tr();
    } else if (difference.inDays < 7) {
      return 'time_days_ago'.tr(namedArgs: {'days': difference.inDays.toString()});
    } else {
      return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
    }
  }

  String _getScoreInterpretation(double score) {
    if (score >= 90) {
      return 'pti.score_interpretation.excellent'.tr();
    } else if (score >= 80) {
      return 'pti.score_interpretation.good'.tr();
    } else if (score >= 70) {
      return 'pti.score_interpretation.average'.tr();
    } else if (score >= 60) {
      return 'pti.score_interpretation.developable'.tr();
    } else {
      return 'pti.score_interpretation.significant_opportunity'.tr();
    }
  }

  Widget _buildPeriodInfoCard() {
    if (_periodInfo == null) return SizedBox.shrink();
    
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.schedule,
                color: Color(0xFF00D4A3),
                size: 20,
              ),
              SizedBox(width: 8),
              Text(
                'Aktuális ${_getPeriodDisplayName(_periodInfo!.period)} időszak',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Időszak vége:',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    _formatPeriodEnd(_periodInfo!.periodEnd),
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'Hátralévő napok:',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    '${_periodInfo!.daysRemaining} nap',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: _periodInfo!.daysRemaining <= 2 
                          ? Colors.red[600] 
                          : _periodInfo!.daysRemaining <= 7
                              ? Colors.orange[600]
                              : Colors.green[600],
                    ),
                  ),
                ],
              ),
            ],
          ),
          SizedBox(height: 12),
          
          // Progress bar
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Időszak haladása: ${_periodInfo!.progressPercentage.toStringAsFixed(1)}%',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
              SizedBox(height: 6),
              LinearProgressIndicator(
                value: _periodInfo!.progressPercentage / 100,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
                minHeight: 6,
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showHistoryBottomSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildHistoryBottomSheet(),
    );
  }

  Widget _buildHistoryBottomSheet() {
    return Container(
      height: MediaQuery.of(context).size.height * 0.8,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
      ),
      child: Column(
        children: [
          // Handle
          Container(
            margin: EdgeInsets.only(top: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey[300],
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          
          // Header
          Padding(
            padding: EdgeInsets.all(20),
            child: Row(
              children: [
                Icon(
                  Icons.history,
                  color: Color(0xFF00D4A3),
                  size: 24,
                ),
                SizedBox(width: 12),
                Text(
                  'pti.history.title'.tr(),
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Spacer(),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: Icon(Icons.close),
                ),
              ],
            ),
          ),
          
          // History content
          Expanded(
            child: _buildHistoryContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryContent() {
    return FutureBuilder<PTIHistoryResponse?>(
      future: _ptiService.getPTIHistory(period: PTIPeriod.weekly, limit: 20),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
            ),
          );
        }

        if (snapshot.hasError || !snapshot.hasData) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline,
                  size: 48,
                  color: Colors.grey[400],
                ),
                SizedBox(height: 16),
                Text(
                  'pti.history.load_error'.tr(),
                  style: TextStyle(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          );
        }

        final history = snapshot.data!;
        final allEntries = <PTIHistoryEntry>[];
        
        // Aktuális időszak hozzáadása
        if (history.currentPeriod != null) {
          allEntries.add(history.currentPeriod!);
        }
        
        // Történeti bejegyzések hozzáadása
        allEntries.addAll(history.entries);

        if (allEntries.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.history,
                  size: 48,
                  color: Colors.grey[400],
                ),
                SizedBox(height: 16),
                Text(
                  'pti.history.no_history'.tr(),
                  style: TextStyle(
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: EdgeInsets.symmetric(horizontal: 20),
          itemCount: allEntries.length,
          itemBuilder: (context, index) {
            final entry = allEntries[index];
            final isCurrentPeriod = index == 0 && history.currentPeriod != null;
            final previousEntry = index < allEntries.length - 1 ? allEntries[index + 1] : null;
            
            return _buildHistoryItem(entry, isCurrentPeriod, previousEntry);
          },
        );
      },
    );
  }

  Widget _buildHistoryItem(PTIHistoryEntry entry, bool isCurrentPeriod, PTIHistoryEntry? previousEntry) {
    // Változás számítása az előző időszakhoz képest
    double? change;
    bool? isImprovement;
    
    if (previousEntry != null) {
      change = entry.ptiScore - previousEntry.ptiScore;
      isImprovement = change > 0;
    }

    return Container(
      margin: EdgeInsets.only(bottom: 16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrentPeriod ? Color(0xFF00D4A3).withOpacity(0.1) : Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: isCurrentPeriod ? Border.all(
          color: Color(0xFF00D4A3).withOpacity(0.3),
          width: 2,
        ) : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (isCurrentPeriod) ...[
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Color(0xFF00D4A3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'pti.history.current'.tr(),
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    SizedBox(width: 8),
                  ],
                  Text(
                    _formatPeriodKey(entry.periodKey),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: isCurrentPeriod ? Color(0xFF00D4A3) : Colors.black,
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  Text(
                    '${entry.ptiScore.toStringAsFixed(1)}',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: isCurrentPeriod ? Color(0xFF00D4A3) : Colors.black,
                    ),
                  ),
                  if (change != null) ...[
                    SizedBox(width: 8),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: isImprovement! ? Colors.green : Colors.red,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isImprovement ? Icons.arrow_upward : Icons.arrow_downward,
                            color: Colors.white,
                            size: 12,
                          ),
                          SizedBox(width: 2),
                          Text(
                            '${change.abs().toStringAsFixed(1)}',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
          SizedBox(height: 8),
          
          // Időszak információ
          Text(
            '${_formatDateShort(entry.periodStart)} - ${_formatDateShort(entry.periodEnd)}',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
          
          if (entry.rank != null) ...[
            SizedBox(height: 4),
            Text(
              '${'pti.history.place'.tr(namedArgs: {'rank': entry.rank.toString()})} ${entry.totalUsers != null ? "pti.history.out_of".tr(namedArgs: {'total_users': entry.totalUsers.toString()}) : ""}',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ],
          SizedBox(height: 12),
          
          // Komponensek mini előnézet
          Row(
            children: [
              _buildMiniComponent('📚', entry.components.learningContribution, 30, Colors.blue),
              SizedBox(width: 8),
              _buildMiniComponent('💪', entry.components.habitContribution, 30, Colors.green),
              SizedBox(width: 8),
              _buildMiniComponent('🏆', entry.components.badgeContribution, 20, Colors.orange),
              SizedBox(width: 8),
              _buildMiniComponent('📊', entry.components.limitContribution, 20, Colors.purple),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMiniComponent(String emoji, double score, int maxScore, Color color) {
    final percentage = (score / maxScore) * 100;
    
    return Expanded(
      child: Column(
        children: [
          Text(
            emoji,
            style: TextStyle(fontSize: 16),
          ),
          SizedBox(height: 4),
          Container(
            height: 4,
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(2),
            ),
            child: FractionallySizedBox(
              alignment: Alignment.centerLeft,
              widthFactor: (percentage / 100).clamp(0.0, 1.0),
              child: Container(
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
          ),
          SizedBox(height: 2),
          Text(
            '${score.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  String _getPeriodDisplayName(PTIPeriod period) {
    switch (period) {
      case PTIPeriod.weekly:
        return 'heti';
      case PTIPeriod.monthly:
        return 'havi';
      case PTIPeriod.yearly:
        return 'éves';
    }
  }

  String _formatPeriodEnd(DateTime date) {
    final now = DateTime.now();
    final difference = date.difference(now).inDays;
    
    if (difference == 0) {
      return 'Ma ${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } else if (difference == 1) {
      return 'Holnap';
    } else {
      return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
    }
  }

  String _formatPeriodKey(String periodKey) {
    // 2025-W03 -> 2025. 3. hét
    // 2025-01 -> 2025. január
    // 2025 -> 2025. év
    
    if (periodKey.contains('-W')) {
      final parts = periodKey.split('-W');
      return 'pti.history.week'.tr(namedArgs: {'year': parts[0], 'week': int.parse(parts[1]).toString()});
    } else if (periodKey.contains('-')) {
      final parts = periodKey.split('-');
      final monthNames = [
        'január', 'február', 'március', 'április', 'május', 'június',
        'július', 'augusztus', 'szeptember', 'október', 'november', 'december'
      ];
      final monthIndex = int.parse(parts[1]) - 1;
      return 'pti.history.month'.tr(namedArgs: {'year': parts[0], 'month': monthNames[monthIndex]});
    } else {
      return '$periodKey. év';
    }
  }

  String _formatDateShort(DateTime date) {
    return '${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
  }
}