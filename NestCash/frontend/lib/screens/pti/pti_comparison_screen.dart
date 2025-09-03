// lib/screens/pti/pti_comparison_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';
import 'package:easy_localization/easy_localization.dart';

class PTIComparisonScreen extends StatefulWidget {
  final String userId;

  const PTIComparisonScreen({
    Key? key,
    required this.userId,
  }) : super(key: key);

  @override
  _PTIComparisonScreenState createState() => _PTIComparisonScreenState();
}

class _PTIComparisonScreenState extends State<PTIComparisonScreen>
    with TickerProviderStateMixin {
  final PTIService _ptiService = PTIService();
  
  late TabController _tabController;
  PTIPeriod _selectedPeriod = PTIPeriod.weekly;
  
  PTIComparisonResponse? _comparisonData;
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadComparison();
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) {
      final newPeriod = PTIPeriod.values[_tabController.index];
      if (newPeriod != _selectedPeriod) { // Csak ha tényleg változott
        setState(() {
          _selectedPeriod = newPeriod;
        });
        _loadComparison();
      }
    }
  }

  Future<void> _loadComparison() async {
    print('DEBUG: _loadComparison started for period: ${_selectedPeriod.value}');
    
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      print('DEBUG: Calling API...');
      final comparison = await _ptiService.getComparison(period: _selectedPeriod);
      print('DEBUG: API call completed, result: ${comparison != null}');

      if (comparison != null) {
        print('DEBUG: Comparison data - PTI: ${comparison.currentPeriod.ptiScore}');
        print('DEBUG: Has previous period: ${comparison.previousPeriod != null}');
        print('DEBUG: PTI Change: ${comparison.ptiChange}');
        
        if (!mounted) return;
        setState(() {
          _comparisonData = comparison;
          _isLoading = false;
        });
      } else {
        if (!mounted) return; // Hozzáadás
        setState(() {
          _error = 'comparison_not_loaded'.tr();
          _isLoading = false;
        });
      }
    } catch (e) {
      print('DEBUG: Exception in _loadComparison: $e');
      if (!mounted) return; // Hozzáadás
      setState(() {
        _error = 'error_occurred'.tr(namedArgs: {'error': e.toString()});
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
          'pti_comparison_title'.tr(),
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.black),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.black,
          unselectedLabelColor: Colors.black54,
          indicatorColor: Colors.black,
          tabs: [
            Tab(text: 'weekly'.tr()),
            Tab(text: 'monthly'.tr()),
            Tab(text: 'yearly'.tr()),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildComparisonContent(),
          _buildComparisonContent(),
          _buildComparisonContent(),
        ],
      ),
    );
  }

  Widget _buildComparisonContent() {
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
              onPressed: _loadComparison,
              child: Text('retry'.tr()),
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4A3),
              ),
            ),
          ],
        ),
      );
    }

    if (_comparisonData == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.compare_arrows,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'no_comparison_data'.tr(),
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadComparison,
      child: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // PTI változás összefoglaló
            _buildChangeSummaryCard(),
            SizedBox(height: 16),
            
            // Aktuális vs előző időszak
            _buildPeriodsComparisonCard(),
            SizedBox(height: 16),
            
            // Komponensek összehasonlítása
            _buildComponentsComparisonCard(),
            SizedBox(height: 16),
            
            // Javulások és csökkenések
            if (_comparisonData!.improvements.isNotEmpty || 
                _comparisonData!.declines.isNotEmpty)
              _buildChangesCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildChangeSummaryCard() {
    final current = _comparisonData!.currentPeriod;
    //final previous = _comparisonData!.previousPeriod;
    final ptiChange = _comparisonData!.ptiChange;
    final rankChange = _comparisonData!.rankChange;

    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: ptiChange != null && ptiChange >= 0
              ? [Color(0xFF00D4A3), Color(0xFF00B894)]
              : [Colors.redAccent, Colors.red[700]!],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: (ptiChange != null && ptiChange >= 0 
                ? Color(0xFF00D4A3) 
                : Colors.redAccent).withOpacity(0.3),
            blurRadius: 20,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'pti_change_summary_title'.tr(namedArgs: {'period': _selectedPeriod.displayName}),
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
          SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                '${current.ptiScore.toStringAsFixed(1)}',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (ptiChange != null) ...[
                SizedBox(width: 12),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        ptiChange >= 0 ? Icons.trending_up : Icons.trending_down,
                        color: Colors.white,
                        size: 16,
                      ),
                      SizedBox(width: 4),
                      Text(
                        '${ptiChange >= 0 ? '+' : ''}${ptiChange.toStringAsFixed(1)}',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
          SizedBox(height: 12),
          Row(
            children: [
              if (current.rank != null) ...[
                Icon(
                  Icons.emoji_events,
                  color: Colors.white,
                  size: 16,
                ),
                SizedBox(width: 4),
                Text(
                  'rank'.tr(namedArgs: {'rank': current.rank.toString()}),
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 14,
                  ),
                ),
                if (rankChange != null) ...[
                  SizedBox(width: 8),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '${rankChange > 0 ? '+' : ''}$rankChange',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPeriodsComparisonCard() {
    final current = _comparisonData!.currentPeriod;
    final previous = _comparisonData!.previousPeriod;

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
            'period_comparison_title'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildPeriodColumn(
                  'current_period'.tr(),
                  current.ptiScore,
                  current.rank,
                  current.totalUsers,
                  Color(0xFF00D4A3),
                ),
              ),
              Container(
                width: 1,
                height: 80,
                color: Colors.grey[300],
                margin: EdgeInsets.symmetric(horizontal: 16),
              ),
              Expanded(
                child: previous != null
                    ? _buildPeriodColumn(
                        'previous_period'.tr(),
                        previous.ptiScore,
                        previous.rank,
                        previous.totalUsers,
                        Colors.grey[600]!,
                      )
                    : Column(
                        children: [
                          Icon(
                            Icons.help_outline,
                            color: Colors.grey[400],
                            size: 32,
                          ),
                          SizedBox(height: 8),
                          Text(
                            'no_data_available'.tr(),
                            style: TextStyle(
                              color: Colors.grey[500],
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPeriodColumn(
    String title,
    double ptiScore,
    int? rank,
    int? totalUsers,
    Color color,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 8),
        Text(
          '${ptiScore.toStringAsFixed(1)}',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          'pti_point'.tr(),
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        if (rank != null) ...[
          SizedBox(height: 4),
          Text(
            'rank_of_total'.tr(namedArgs: {'rank': rank.toString(), 'total': (totalUsers ?? 0).toString()}),
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildComponentsComparisonCard() {
    final current = _comparisonData!.currentPeriod.components;
    final previous = _comparisonData!.previousPeriod?.components;

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
            'component_change_title'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          _buildComponentComparisonItem(
            'learning_emoji'.tr(),
            current.learningPoints,
            previous?.learningPoints,
            Colors.blue,
          ),
          SizedBox(height: 12),
          _buildComponentComparisonItem(
            'habits_emoji'.tr(),
            current.habitScore,
            previous?.habitScore,
            Colors.green,
          ),
          SizedBox(height: 12),
          _buildComponentComparisonItem(
            'badges_emoji'.tr(),
            current.badgeScore,
            previous?.badgeScore,
            Colors.orange,
          ),
          SizedBox(height: 12),
          _buildComponentComparisonItem(
            'limits_emoji'.tr(),
            current.limitScore,
            previous?.limitScore,
            Colors.purple,
          ),
        ],
      ),
    );
  }

  Widget _buildComponentComparisonItem(
  String title,
  double currentValue,
  double? previousValue,
  Color color,
) {
  final change = previousValue != null ? currentValue - previousValue : null;
  
  return Container(
    padding: EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: color.withOpacity(0.1),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              SizedBox(height: 4),
              Row(
                children: [
                  Text(
                    '${currentValue.toStringAsFixed(1)}',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: color,
                    ),
                  ),
                  if (change != null) ...[
                    SizedBox(width: 8),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: change >= 0 
                            ? Colors.green.withOpacity(0.2)
                            : Colors.red.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            change >= 0 ? Icons.arrow_upward : Icons.arrow_downward,
                            size: 12,
                            color: change >= 0 ? Colors.green : Colors.red,
                          ),
                          SizedBox(width: 2),
                          Text(
                            '${change.abs().toStringAsFixed(1)}',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: change >= 0 ? Colors.green : Colors.red,
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
        ),
        SizedBox(width: 16),
        // JAVÍTOTT LinearProgressIndicator
        Expanded(
          flex: 0,
          child: Container(
            width: 100, // Fix szélesség
            child: Column(
              children: [
                LinearProgressIndicator(
                  value: _calculateSafeProgressValue(currentValue),
                  backgroundColor: color.withOpacity(0.2),
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                  minHeight: 6,
                ),
                SizedBox(height: 4),
                Text(
                  '${_calculatePercentage(currentValue)}%',
                  style: TextStyle(
                    fontSize: 10,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}

// Segédmetódusok hozzáadása a class-hoz:
double _calculateSafeProgressValue(double value) {
  // A komponensek maximális értékei (models alapján):
  // learning: 30, habits: 30, badges: 20, limits: 20
  
  // Biztonságos érték számítás:
  if (value.isNaN || value.isInfinite) return 0.0;
  
  // Feltételezzük, hogy a maximum érték 30 (vagy dinamikusan számítható)
  double maxValue = 30.0; // Ez lehet hogy változó a komponens alapján
  double progress = (value / maxValue).clamp(0.0, 1.0);
  
  return progress;
}

double _calculatePercentage(double value) {
  double maxValue = 30.0; // Ugyanaz mint fent
  return ((value / maxValue) * 100).clamp(0.0, 100.0);
}

  Widget _buildChangesCard() {
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
            'detailed_changes_title'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          
          if (_comparisonData!.improvements.isNotEmpty) ...[
            Row(
              children: [
                Icon(
                  Icons.trending_up,
                  color: Colors.green,
                  size: 20,
                ),
                SizedBox(width: 8),
                Text(
                  'improvements'.tr(),
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            ..._comparisonData!.improvements.map((improvement) {
              return Padding(
                padding: EdgeInsets.only(bottom: 4, left: 28),
                child: Text(
                  improvement,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[700],
                  ),
                ),
              );
            }).toList(),
            SizedBox(height: 16),
          ],
          
          // Csökkenések
          if (_comparisonData!.declines.isNotEmpty) ...[
            Row(
              children: [
                Icon(
                  Icons.trending_down,
                  color: Colors.red,
                  size: 20,
                ),
                SizedBox(width: 8),
                Text(
                  'declines'.tr(),
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.red,
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            ..._comparisonData!.declines.map((decline) {
              return Padding(
                padding: EdgeInsets.only(bottom: 4, left: 28),
                child: Text(
                  decline,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[700],
                  ),
                ),
              );
            }).toList(),
          ],
        ],
      ),
    );
  }
}