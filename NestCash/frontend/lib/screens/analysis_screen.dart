// lib/screens/analysis_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/services/analysis_service.dart';
import 'package:frontend/models/analysis.dart';
import 'package:frontend/utils/number_formatter.dart';

class AnalysisScreen extends StatefulWidget {
  final String userId;

  const AnalysisScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen>
    with SingleTickerProviderStateMixin {
  final AnalysisService _analysisService = AnalysisService();
  late TabController _tabController;
  
  FinancialAnalysis? _comprehensiveAnalysis;
  BasicStats? _basicStats;
  RiskAnalysis? _riskAnalysis;
  CategoryAnalysis? _categoryAnalysis;
  
  bool _isLoading = false;
  String _selectedPeriod = '6'; // hónapok száma

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadBasicStats();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadBasicStats() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final basicStats = await _analysisService.getBasicStats(monthsBack: monthsBack);
      setState(() {
        _basicStats = basicStats;
      });
    } catch (e) {
      _showError('Hiba az alapstatisztikák betöltésekor: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadComprehensiveAnalysis() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final analysis = await _analysisService.getComprehensiveAnalysis(monthsBack: monthsBack);
      setState(() {
        _comprehensiveAnalysis = analysis;
      });
    } catch (e) {
      _showError('Hiba az átfogó elemzés betöltésekor: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadRiskAnalysis() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final riskAnalysis = await _analysisService.getRiskAnalysis(monthsBack: monthsBack);
      setState(() {
        _riskAnalysis = riskAnalysis;
      });
    } catch (e) {
      _showError('Hiba a kockázatelemzés betöltésekor: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadCategoryAnalysis() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final categoryAnalysis = await _analysisService.getCategoryAnalysis(monthsBack: monthsBack);
      setState(() {
        _categoryAnalysis = categoryAnalysis;
      });
    } catch (e) {
      _showError('Hiba a kategóriaelemzés betöltésekor: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _onPeriodChanged(String? newValue) {
    if (newValue != null) {
      setState(() {
        _selectedPeriod = newValue;
      });
      // Újratöltjük az aktuális tab adatait
      switch (_tabController.index) {
        case 0:
          _loadBasicStats();
          break;
        case 1:
          _loadRiskAnalysis();
          break;
        case 2:
          _loadCategoryAnalysis();
          break;
        case 3:
          _loadComprehensiveAnalysis();
          break;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF00D4A3),
                Color(0xFFE8F6F3),
              ],
              stops: [0.0, 0.4],
            ),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back, color: Colors.black87),
                      onPressed: () => Navigator.pop(context),
                    ),
                    Expanded(
                      child: Text(
                        'Pénzügyi Elemzések',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    // Időszak választó
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.9),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: DropdownButton<String>(
                        value: _selectedPeriod,
                        underline: SizedBox(),
                        items: [
                          DropdownMenuItem(value: '3', child: Text('3 hónap')),
                          DropdownMenuItem(value: '6', child: Text('6 hónap')),
                          DropdownMenuItem(value: '12', child: Text('1 év')),
                          DropdownMenuItem(value: '24', child: Text('2 év')),
                        ],
                        onChanged: _onPeriodChanged,
                        style: TextStyle(
                          color: Colors.black87,
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Tab Bar
              Container(
                margin: EdgeInsets.symmetric(horizontal: 20),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(25),
                ),
                child: TabBar(
                  controller: _tabController,
                  indicator: BoxDecoration(
                    color: Color(0xFF00D4A3),
                    borderRadius: BorderRadius.circular(25),
                  ),
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.black54,
                  labelStyle: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                  unselectedLabelStyle: TextStyle(fontSize: 12),
                  tabs: [
                    Tab(text: 'Alapok'),
                    Tab(text: 'Kockázat'),
                    Tab(text: 'Kategóriák'),
                    Tab(text: 'Átfogó'),
                  ],
                  onTap: (index) {
                    switch (index) {
                      case 0:
                        if (_basicStats == null) _loadBasicStats();
                        break;
                      case 1:
                        if (_riskAnalysis == null) _loadRiskAnalysis();
                        break;
                      case 2:
                        if (_categoryAnalysis == null) _loadCategoryAnalysis();
                        break;
                      case 3:
                        if (_comprehensiveAnalysis == null) _loadComprehensiveAnalysis();
                        break;
                    }
                  },
                ),
              ),

              SizedBox(height: 20),

              // Content
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildBasicStatsTab(),
                      _buildRiskAnalysisTab(),
                      _buildCategoryAnalysisTab(),
                      _buildComprehensiveAnalysisTab(),
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

  Widget _buildBasicStatsTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
      );
    }

    if (_basicStats == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.analytics_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Nincs elérhető adat', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildStatCard(
            'Összes bevétel',
            NumberFormatter.formatCurrency(_basicStats!.totalIncome),
            Icons.trending_up,
            Colors.green,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Összes kiadás',
            NumberFormatter.formatCurrency(_basicStats!.totalExpense),
            Icons.trending_down,
            Colors.red,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Nettó egyenleg',
            NumberFormatter.formatCurrency(_basicStats!.netBalance),
            Icons.account_balance,
            _basicStats!.netBalance >= 0 ? Colors.green : Colors.red,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Havi átlag kiadás',
            NumberFormatter.formatCurrency(_basicStats!.monthlyAvgExpense),
            Icons.calendar_month,
            Colors.blue,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Legaktívabb nap',
            _basicStats!.mostActiveDay,
            Icons.event,
            Colors.purple,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Tranzakciók száma',
            '${_basicStats!.transactionCount}',
            Icons.receipt,
            Colors.orange,
          ),
        ],
      ),
    );
  }

  Widget _buildRiskAnalysisTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
      );
    }

    if (_riskAnalysis == null) {
      return Center(
        child: ElevatedButton(
          onPressed: _loadRiskAnalysis,
          child: Text('Kockázatelemzés betöltése'),
          style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF00D4A3)),
        ),
      );
    }

    Color riskColor = _riskAnalysis!.riskLevel == 'alacsony' 
        ? Colors.green 
        : _riskAnalysis!.riskLevel == 'közepes' 
            ? Colors.orange 
            : Colors.red;

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildRiskCard(
            'Kockázati szint',
            _riskAnalysis!.riskLevel.toUpperCase(),
            riskColor,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Kiadás/Bevétel arány',
            '${(_riskAnalysis!.expenseIncomeRatio * 100).toStringAsFixed(1)}%',
            Icons.percent,
            _riskAnalysis!.expenseIncomeRatio > 0.8 ? Colors.red : Colors.green,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Megtakarítási ráta',
            '${(_riskAnalysis!.savingsRate * 100).toStringAsFixed(1)}%',
            Icons.savings,
            _riskAnalysis!.savingsRate > 0.2 ? Colors.green : Colors.orange,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Vészhelyzeti alap',
            '${_riskAnalysis!.emergencyFundMonths.toStringAsFixed(1)} hónap',
            Icons.security,
            _riskAnalysis!.emergencyFundMonths >= 6 ? Colors.green : Colors.orange,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'Adósság/Bevétel arány',
            '${(_riskAnalysis!.debtIncomeRatio * 100).toStringAsFixed(1)}%',
            Icons.warning,
            _riskAnalysis!.debtIncomeRatio > 0.3 ? Colors.red : Colors.green,
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryAnalysisTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
      );
    }

    if (_categoryAnalysis == null) {
      return Center(
        child: ElevatedButton(
          onPressed: _loadCategoryAnalysis,
          child: Text('Kategóriaelemzés betöltése'),
          style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF00D4A3)),
        ),
      );
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Top kiadási kategóriák',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),
          
          ..._categoryAnalysis!.topExpenseCategories.map((category) => 
            Container(
              margin: EdgeInsets.only(bottom: 12),
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 4,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Center(
                      child: Text(
                        '${category['rank']}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.red,
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          category['category'],
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          '${category['transaction_count']} tranzakció',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    NumberFormatter.formatCurrency(category['amount']),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: Colors.red,
                    ),
                  ),
                ],
              ),
            ),
          ).toList(),

          if (_categoryAnalysis!.missingBasicCategories.isNotEmpty) ...[
            SizedBox(height: 24),
            Text(
              'Hiányzó alapkategóriák',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            SizedBox(height: 16),
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.orange.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.warning, color: Colors.orange),
                      SizedBox(width: 8),
                      Text(
                        'Javasolt kategóriák',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: Colors.orange[800],
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    _categoryAnalysis!.missingBasicCategories.join(', '),
                    style: TextStyle(color: Colors.orange[700]),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildComprehensiveAnalysisTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
      );
    }

    if (_comprehensiveAnalysis == null) {
      return Center(
        child: ElevatedButton(
          onPressed: _loadComprehensiveAnalysis,
          child: Text('Átfogó elemzés betöltése'),
          style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF00D4A3)),
        ),
      );
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Cashflow trend
          Text(
            'Pénzforgalmi trend',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    Icon(
                      _comprehensiveAnalysis!.cashflowAnalysis.overallTrend == 'növekvő'
                          ? Icons.trending_up
                          : _comprehensiveAnalysis!.cashflowAnalysis.overallTrend == 'csökkenő'
                              ? Icons.trending_down
                              : Icons.trending_flat,
                      color: _comprehensiveAnalysis!.cashflowAnalysis.overallTrend == 'növekvő'
                          ? Colors.green
                          : _comprehensiveAnalysis!.cashflowAnalysis.overallTrend == 'csökkenő'
                              ? Colors.red
                              : Colors.blue,
                    ),
                    SizedBox(width: 8),
                    Text(
                      'Trend: ${_comprehensiveAnalysis!.cashflowAnalysis.overallTrend}',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 12),
                if (_comprehensiveAnalysis!.cashflowAnalysis.monthlyTrends.isNotEmpty)
                  ...(_comprehensiveAnalysis!.cashflowAnalysis.monthlyTrends.take(3).map((trend) =>
                    Padding(
                      padding: EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(trend.period),
                          Text(
                            NumberFormatter.formatCurrency(trend.net),
                            style: TextStyle(
                              color: trend.net >= 0 ? Colors.green : Colors.red,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ).toList()),
              ],
            ),
          ),

          SizedBox(height: 24),

          // Ajánlások
          Text(
            'Személyre szabott ajánlások',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),

          if (_comprehensiveAnalysis!.recommendations.savingsSuggestions.isNotEmpty)
            _buildRecommendationCard(
              'Megtakarítási javaslatok',
              _comprehensiveAnalysis!.recommendations.savingsSuggestions,
              Icons.savings,
              Colors.green,
            ),

          if (_comprehensiveAnalysis!.recommendations.costOptimizationTips.isNotEmpty)
            _buildRecommendationCard(
              'Költségoptimalizálás',
              _comprehensiveAnalysis!.recommendations.costOptimizationTips,
              Icons.done,
              Colors.blue,
            ),

          if (_comprehensiveAnalysis!.recommendations.emergencyFundAdvice.isNotEmpty)
            _buildRecommendationCard(
              'Vészhelyzeti alap',
              _comprehensiveAnalysis!.recommendations.emergencyFundAdvice,
              Icons.security,
              Colors.orange,
            ),

          if (_comprehensiveAnalysis!.recommendations.debtManagementAdvice.isNotEmpty)
            _buildRecommendationCard(
              'Adósságkezelés',
              _comprehensiveAnalysis!.recommendations.debtManagementAdvice,
              Icons.warning,
              Colors.red,
            ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[600],
                    fontWeight: FontWeight.w500,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRiskCard(String title, String value, Color color) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(
            Icons.shield,
            color: color,
            size: 48,
          ),
          SizedBox(height: 12),
          Text(
            title,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
              fontWeight: FontWeight.w500,
            ),
          ),
          SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendationCard(String title, List<String> recommendations, IconData icon, Color color) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 24),
              SizedBox(width: 12),
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          ...recommendations.map((rec) => Padding(
            padding: EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: EdgeInsets.only(top: 6),
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    rec,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[700],
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          )).toList(),
        ],
      ),
    );
  }
}