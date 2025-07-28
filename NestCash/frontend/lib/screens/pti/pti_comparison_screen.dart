// lib/screens/pti/pti_comparison_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';

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
      setState(() {
        _selectedPeriod = PTIPeriod.values[_tabController.index];
      });
      _loadComparison();
    }
  }

  Future<void> _loadComparison() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final comparison = await _ptiService.getComparison(period: _selectedPeriod);

      if (comparison != null) {
        setState(() {
          _comparisonData = comparison;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nem sikerült betölteni az összehasonlítást';
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
          'PTI Összehasonlítás',
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
            Tab(text: 'Heti'),
            Tab(text: 'Havi'),
            Tab(text: 'Éves'),
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
              child: Text('Újrapróbálás'),
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
              'Nincs összehasonlítási adat',
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
            '${_selectedPeriod.displayName} PTI Változás',
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
                  '${current.rank}. helyezés',
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
            'Időszakok összehasonlítása',
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
                  'Aktuális időszak',
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
                        'Előző időszak',
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
                            'Nincs adat',
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
          'PTI pont',
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
        if (rank != null) ...[
          SizedBox(height: 4),
          Text(
            '${rank}. / ${totalUsers ?? 0}',
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
            'Komponensek változása',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          _buildComponentComparisonItem(
            '📚 Tanulás',
            current.learningPoints,
            previous?.learningPoints,
            Colors.blue,
          ),
          SizedBox(height: 12),
          _buildComponentComparisonItem(
            '💪 Szokások',
            current.habitScore,
            previous?.habitScore,
            Colors.green,
          ),
          SizedBox(height: 12),
          _buildComponentComparisonItem(
            '🏆 Kitűzők',
            current.badgeScore,
            previous?.badgeScore,
            Colors.orange,
          ),
          SizedBox(height: 12),
          _buildComponentComparisonItem(
            '📊 Limitek',
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
          LinearProgressIndicator(
            value: currentValue / 100,
            backgroundColor: color.withOpacity(0.2),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
        ],
      ),
    );
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
            'Változások részletesen',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 16),
          
          // Javulások
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
                  'Javulások',
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
                  'Csökkenések',
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