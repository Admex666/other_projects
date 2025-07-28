// lib/screens/pti/pti_main_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';
import 'package:frontend/screens/pti/pti_ranking_screen.dart';
import 'package:frontend/screens/pti/pti_settings_screen.dart';
import 'package:frontend/screens/pti/pti_comparison_screen.dart';

class PTIMainScreen extends StatefulWidget {
  final String userId;
  final String username;

  const PTIMainScreen({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _PTIMainScreenState createState() => _PTIMainScreenState();
}

class _PTIMainScreenState extends State<PTIMainScreen> {
  final PTIService _ptiService = PTIService();
  PTIDashboardResponse? _dashboardData;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final dashboard = await _ptiService.getDashboard();
      if (dashboard != null) {
        setState(() {
          _dashboardData = dashboard;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nem sikerült betölteni a PTI adatokat';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Hiba történt: $e';
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
          'PTI - Pénzügyi Tudatosság Index',
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
        onRefresh: _loadDashboard,
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
              child: Text('Újrapróbálás'),
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
          'Nincs PTI adat',
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
                'Jelenlegi PTI Pontszám',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                'Frissítve: ${_formatDate(pti.calculatedAt)}',
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
                        '${pti.rank}. helyezés',
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
          Text(
            'PTI Komponensek',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 20),
          
          _buildComponentItem(
            '📚 Tanulás',
            components.learningContribution,
            30,
            Colors.blue,
            'Pénzügyi ismeretek és képzések',
          ),
          SizedBox(height: 16),
          
          _buildComponentItem(
            '💪 Szokások',
            components.habitContribution,
            30,
            Colors.green,
            'Napi pénzügyi szokások követése',
          ),
          SizedBox(height: 16),
          
          _buildComponentItem(
            '🏆 Kitűzők',
            components.badgeContribution,
            20,
            Colors.orange,
            'Elért eredmények és mérföldkövek',
          ),
          SizedBox(height: 16),
          
          _buildComponentItem(
            '📊 Limitek',
            components.limitContribution,
            20,
            Colors.purple,
            'Költségvetési korlátok betartása',
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
  ) {
    final percentage = (currentScore / maxWeight) * 100;
    
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
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
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
          SizedBox(height: 4),
          Text(
            '${percentage.toStringAsFixed(1)}%',
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
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
                'Ranglisták',
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
                        username: widget.username,
                      ),
                    ),
                  );
                },
                child: Text(
                  'Összes megtekintése',
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
                  'Heti',
                  _dashboardData!.weeklyRanking?.rank,
                  _dashboardData!.currentPti.totalUsers,
                  Icons.calendar_view_week,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildRankingPreview(
                  'Havi',
                  _dashboardData!.monthlyRanking?.rank,
                  _dashboardData!.currentPti.totalUsers,
                  Icons.calendar_month,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildRankingPreview(
                  'Éves',
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
            'PTI Célok',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          
          if (_dashboardData!.weeklyGoalProgress != null)
            _buildGoalProgress(
              'Heti cél',
              _dashboardData!.weeklyGoalProgress!,
              Icons.calendar_view_week,
              Colors.blue,
            ),
          
          if (_dashboardData!.weeklyGoalProgress != null && 
              _dashboardData!.monthlyGoalProgress != null)
            SizedBox(height: 16),
          
          if (_dashboardData!.monthlyGoalProgress != null)
            _buildGoalProgress(
              'Havi cél',
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
                        'Elérve',
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
                '${progressPercentage.toStringAsFixed(1)}% teljesítve',
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
                'Fejlesztési javaslatok',
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
            'Gyors műveletek',
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
                  'Ranglisták',
                  Icons.leaderboard,
                  Color(0xFF00D4A3),
                  () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PTIRankingScreen(
                          userId: widget.userId,
                          username: widget.username,
                        ),
                      ),
                    );
                  },
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildQuickActionButton(
                  'Összehasonlítás',
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
                  'PTI frissítése',
                  Icons.refresh,
                  Colors.orange,
                  () async {
                    await _ptiService.calculatePTI();
                    _loadDashboard();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('PTI újraszámítás elindítva'),
                        backgroundColor: Color(0xFF00D4A3),
                      ),
                    );
                  },
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildQuickActionButton(
                  'Beállítások',
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
      return 'Ma';
    } else if (difference.inDays == 1) {
      return 'Tegnap';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} napja';
    } else {
      return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
    }
  }

  String _getScoreInterpretation(double score) {
    if (score >= 90) {
      return 'Kiváló pénzügyi tudatosság! 🌟';
    } else if (score >= 80) {
      return 'Jó pénzügyi tudatosság! 👍';
    } else if (score >= 70) {
      return 'Átlagos pénzügyi tudatosság 📈';
    } else if (score >= 60) {
      return 'Fejleszthető pénzügyi tudatosság 💪';
    } else {
      return 'Jelentős fejlesztési lehetőség 🎯';
    }
  }
}