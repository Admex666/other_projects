// lib/screens/analysis_screen.dart

import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/services/analysis_service.dart';
import 'package:frontend/models/analysis.dart';
import 'package:frontend/utils/number_formatter.dart';
import '/main.dart';
import 'package:provider/provider.dart';
import '../providers/subscription_provider.dart';
import '../widgets/subscription/feature_locked_widget.dart';
import '../models/subscription.dart';
import '../utils/subscription_utils.dart';
import '../../widgets/subscription/subscription_widgets.dart';
import '../utils/category_translate.dart';
import 'package:frontend/services/nestcash_analytics_service.dart';

class AnalysisScreen extends StatefulWidget {
  final String userId;
  final bool fromTutorial;

  const AnalysisScreen({
    Key? key,
    required this.userId,
    this.fromTutorial = false,
    }) : super(key: key);

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

  // ÚJ ML VÁLTOZÓK:
  ForecastResponse? _forecastData;
  AnomalyResponse? _anomalyData;
  MLBudgetResponse? _mlBudgetData;
  WhatIfResponse? _whatIfData;
  Map<String, dynamic>? _advancedInsights;

  bool _isLoading = false;
  String _selectedPeriod = '6'; // hónapok száma

  bool _hasBasicAnalyticsAccess = true;
  bool _hasAdvancedAnalyticsAccess = false;
  bool _isCheckingAccess = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 6, vsync: this);
    _checkAnalyticsAccess();
  }

  Future<void> _checkAnalyticsAccess() async {
    setState(() => _isCheckingAccess = true);

    try {
      final subscriptionProvider = Provider.of<SubscriptionProvider>(context, listen: false);

      // Várjuk meg, hogy a provider inicializálódjon
      if (!subscriptionProvider.isInitialized) {
        await subscriptionProvider.loadSubscriptionInfo(forceRefresh: true);
      }

      // Alapvető elemzésekhez mindig van hozzáférés
      _hasBasicAnalyticsAccess = true;

      print('Current subscription tier: ${subscriptionProvider.currentTier}');
      print('Is active: ${subscriptionProvider.isActive}');
      print('Is Plus or higher: ${subscriptionProvider.isPlusOrHigher}');

      // Egyszerű tier-alapú ellenőrzés először
      if (subscriptionProvider.isPlusOrHigher) {
        setState(() {
          _hasAdvancedAnalyticsAccess = true;
        });
        print('Access granted based on tier');
      } else {
        // Részletes feature check ha kétséges
        try {
          final advancedAccessCheck = await subscriptionProvider.checkFeature(
            'analysis_insights',
            context: {'analysisType': 'advanced'},
          );

          setState(() {
            _hasAdvancedAnalyticsAccess = advancedAccessCheck.hasAccess;
          });

          print('Feature check result: ${advancedAccessCheck.hasAccess}');
          await NestCashAnalyticsService.trackScreenView('analysis_screen');
        } catch (e) {
          print('Feature check failed, falling back to tier: $e');
          setState(() {
            _hasAdvancedAnalyticsAccess = subscriptionProvider.isPlusOrHigher;
          });
        }
      }

      _loadBasicStats();
    } catch (e) {
      print('Error checking analytics access: $e');
      setState(() {
        _hasBasicAnalyticsAccess = true;
        _hasAdvancedAnalyticsAccess = false;
      });
      _loadBasicStats();
    } finally {
      setState(() => _isCheckingAccess = false);
    }
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
      _showError('basic_stats_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadComprehensiveAnalysis() async {
    if (!_hasAdvancedAnalyticsAccess) {
      _showUpgradeForFeature('comprehensive_analysis'.tr(), SubscriptionTier.plus);
      return;
    }

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
      _showError('comprehensive_analysis_error'.tr(namedArgs: {'error': e.toString()}));
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
      _showError('risk_analysis_error'.tr(namedArgs: {'error': e.toString()}));
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
      _showError('category_analysis_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadForecastData() async {
    if (!_hasAdvancedAnalyticsAccess) {
      _showUpgradeForFeature('ai_forecast'.tr(), SubscriptionTier.pro);
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final forecast = await _analysisService.getSpendingForecast(
        forecastType: 'monthly',
        periodsAhead: 6,
        monthsHistory: monthsBack,
      );
      setState(() {
        _forecastData = forecast;
      });
    } catch (e) {
      _showError('forecast_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadAnomalyData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final anomaly = await _analysisService.getAnomalyDetection(
        monthsBack: monthsBack,
        sensitivity: 0.1,
      );
      setState(() {
        _anomalyData = anomaly;
      });
    } catch (e) {
      _showError('anomaly_detection_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadMLBudgetData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);
      final mlBudget = await _analysisService.getMLBudgetRecommendations(
        monthsBack: monthsBack,
      );
      setState(() {
        _mlBudgetData = mlBudget;
      });
    } catch (e) {
      _showError('ml_budget_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadAdvancedInsights() async {
    if (!_hasAdvancedAnalyticsAccess) {
    _showUpgradeForFeature('advanced_ai_insights'.tr(), SubscriptionTier.pro);
    return;
  }

    setState(() {
      _isLoading = true;
    });

    try {
      final monthsBack = int.parse(_selectedPeriod);

      // Próbáljuk meg az anomália detektálást külön betölteni
      try {
        await _loadAnomalyData();
      } catch (e) {
        print('anomaly_load_error'.tr(namedArgs: {'error': e.toString()}));
      }

      // Próbáljuk meg az ML költségvetést külön betölteni
      try {
        await _loadMLBudgetData();
      } catch (e) {
        print('ml_budget_load_error'.tr(namedArgs: {'error': e.toString()}));
      }

      // Alap insights betöltése
      try {
        final insights = await _analysisService.getAdvancedInsights(
          monthsBack: monthsBack,
        );
        setState(() {
          _advancedInsights = insights;
        });
      } catch (e) {
        print('basic_insights_error'.tr(namedArgs: {'error': e.toString()}));
        // Ha minden más nem működik, adj vissza egy üres Map-et
        setState(() {
          _advancedInsights = {
            'status': 'partial_load',
            'message': 'partial_load_message'.tr(),
            'loaded_at': DateTime.now().toIso8601String(),
          };
        });
      }

    } catch (e) {
      print('detailed_error'.tr(namedArgs: {'error': e.toString()}));
      _showError('advanced_insights_error'.tr(namedArgs: {'error': e.toString()}));
      // Üres insights beállítása, hogy ne crasheljen
      setState(() {
        _advancedInsights = {
          'error': true,
          'message': 'advanced_insights_unavailable'.tr(),
          'error_details': e.toString(),
        };
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showUpgradeForFeature(String featureName, SubscriptionTier requiredTier) {
    SubscriptionUtils.showUpgradeDialog(
      context,
      feature: featureName,
      requiredTier: requiredTier,
    );
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
        case 4: // ÚJ
          _loadForecastData();
          break;
        case 5: // ÚJ
          _loadAdvancedInsights();
          break;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Color(0xFF00D4A3),
        foregroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back),
          onPressed: () {
            if (widget.fromTutorial) {
              Navigator.pop(context);
            } else {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => MainScreen(
                    userId: widget.userId,
                  ),
                ),
              );
            }
          },
        ),
        title: Center(
          child: Text(
            'analysis'.tr(),
            style: TextStyle(
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        actions: [
          // TIER BADGE HOZZÁADÁSA
          Consumer<SubscriptionProvider>(
            builder: (context, provider, child) {
              return AppBarTierBadge(
                tier: provider.currentTier,
                onTap: () {
                  // Navigálás a subscription képernyőre
                  Navigator.pushNamed(context, '/subscription');
                },
              );
            },
          ),
          IconButton(
            icon: Icon(Icons.notifications_outlined),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('notifications_soon'.tr())),
              );
            },
          ),
        ],
      ),
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
                  labelStyle: TextStyle(fontSize: 13, fontWeight: FontWeight.w600), // 10-ről 13-ra
                  unselectedLabelStyle: TextStyle(fontSize: 12), // 10-ről 12-re
                  labelPadding: EdgeInsets.symmetric(horizontal: 12), // padding hozzáadása
                  isScrollable: true,
                  tabs: [
                    Tab(text: 'basics'.tr()),
                    Tab(text: 'risk'.tr()),
                    Tab(text: 'category'.tr()),
                    Tab(text: 'comprehensive'.tr()),
                    Tab(text: 'forecast'.tr()),
                    Tab(text: 'insights'.tr()),
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
                      case 4: // ÚJ
                        if (_forecastData == null) _loadForecastData();
                        break;
                      case 5: // ÚJ
                        if (_advancedInsights == null) _loadAdvancedInsights();
                        break;
                    }
                  },
                ),
              ),

              SizedBox(height: 16),

              // Időszak választó
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    SizedBox(width: 36),
                    Text(
                      'analysis_period'.tr(),
                      style: TextStyle(
                        color: Colors.black87,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
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
                          DropdownMenuItem(value: '3', child: Text('3 ' + 'months'.tr())),
                          DropdownMenuItem(value: '6', child: Text('6 ' + 'months'.tr())),
                          DropdownMenuItem(value: '12', child: Text('1 ' + 'year'.tr())),
                          DropdownMenuItem(value: '24', child: Text('2 ' + 'years'.tr())),
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
                      // ÁTFOGÓ ELEMZÉS LOCKED WIDGET
                      _hasAdvancedAnalyticsAccess
                          ? _buildComprehensiveAnalysisTab()
                          : FeatureLockedWidget(
                              featureName: 'comprehensive_financial_analysis'.tr(),
                              description: 'comprehensive_analysis_desc'.tr(),
                              requiredTier: SubscriptionTier.plus,
                            ),
                      // ELŐREJELZÉS LOCKED WIDGET
                      _hasAdvancedAnalyticsAccess
                          ? _buildForecastTab()
                          : FeatureLockedWidget(
                              featureName: 'ai_forecast'.tr(),
                              description: 'ai_forecast_desc'.tr(),
                              requiredTier: SubscriptionTier.pro,
                            ),
                      // FEJLETT BETEKINTÉSEK LOCKED WIDGET
                      _hasAdvancedAnalyticsAccess
                          ? _buildAdvancedInsightsTab()
                          : FeatureLockedWidget(
                              featureName: 'advanced_ai_insights'.tr(),
                              description: 'advanced_ai_insights_desc'.tr(),
                              requiredTier: SubscriptionTier.pro,
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
            Text('no_data_available'.tr(), style: TextStyle(color: Colors.grey)),
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
            'total_income'.tr(),
            NumberFormatter.formatCurrency(_basicStats!.totalIncome),
            Icons.trending_up,
            Colors.green,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'total_expense'.tr(),
            NumberFormatter.formatCurrency(_basicStats!.totalExpense),
            Icons.trending_down,
            Colors.red,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'net_balance'.tr(),
            NumberFormatter.formatCurrency(_basicStats!.netBalance),
            Icons.account_balance,
            _basicStats!.netBalance >= 0 ? Colors.green : Colors.red,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'monthly_avg_expense'.tr(),
            NumberFormatter.formatCurrency(_basicStats!.monthlyAvgExpense),
            Icons.calendar_month,
            Colors.blue,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'most_active_day'.tr(),
            _basicStats!.mostActiveDay,
            Icons.event,
            Colors.purple,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'transaction_count'.tr(),
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
          child: Text('load_risk_analysis'.tr()),
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
            'risk_level'.tr(),
            _riskAnalysis!.riskLevel.tr().toUpperCase(),
            riskColor,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'expense_income_ratio'.tr(),
            '${(_riskAnalysis!.expenseIncomeRatio * 100).toStringAsFixed(1)}%',
            Icons.percent,
            _riskAnalysis!.expenseIncomeRatio > 0.8 ? Colors.red : Colors.green,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'savings_rate'.tr(),
            '${(_riskAnalysis!.savingsRate * 100).toStringAsFixed(1)}%',
            Icons.savings,
            _riskAnalysis!.savingsRate > 0.2 ? Colors.green : Colors.orange,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'emergency_fund'.tr(),
            '${_riskAnalysis!.emergencyFundMonths.toStringAsFixed(1)} ' + 'months'.tr(),
            Icons.security,
            _riskAnalysis!.emergencyFundMonths >= 6 ? Colors.green : Colors.orange,
          ),
          SizedBox(height: 12),
          _buildStatCard(
            'debt_income_ratio'.tr(),
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
          child: Text('load_category_analysis'.tr()),
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
            'top_expense_categories'.tr(),
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
                          CategoryTranslate.getLocalizedCategory(category['category']).tr(),
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          '${category['transaction_count']} ' + 'transaction_count_singular'.tr(),
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
              'missing_basic_categories'.tr(),
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
                        'suggested_categories'.tr(),
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: Colors.orange[800],
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    _categoryAnalysis!.missingBasicCategories
                        .map((category) => CategoryTranslate.getLocalizedCategory(category).tr())
                        .join(', '),
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
          child: Text('load_comprehensive_analysis'.tr()),
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
            'cashflow_trend'.tr(),
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
                      'trend'.tr(namedArgs: {'trend': _comprehensiveAnalysis!.cashflowAnalysis.overallTrend.tr()}),
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
            'personalized_recommendations'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),

          if (_comprehensiveAnalysis!.recommendations.savingsSuggestions.isNotEmpty)
            _buildRecommendationCard(
              'savings_suggestions'.tr(),
              _comprehensiveAnalysis!.recommendations.savingsSuggestions,
              Icons.savings,
              Colors.green,
            ),

          if (_comprehensiveAnalysis!.recommendations.costOptimizationTips.isNotEmpty)
            _buildRecommendationCard(
              'cost_optimization'.tr(),
              _comprehensiveAnalysis!.recommendations.costOptimizationTips,
              Icons.done,
              Colors.blue,
            ),

          if (_comprehensiveAnalysis!.recommendations.emergencyFundAdvice.isNotEmpty)
            _buildRecommendationCard(
              'emergency_fund_title'.tr(),
              _comprehensiveAnalysis!.recommendations.emergencyFundAdvice,
              Icons.security,
              Colors.orange,
            ),

          if (_comprehensiveAnalysis!.recommendations.debtManagementAdvice.isNotEmpty)
            _buildRecommendationCard(
              'debt_management'.tr(),
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

  Widget _buildForecastTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
      );
    }

    if (_forecastData == null) {
      return Center(
        child: ElevatedButton(
          onPressed: _loadForecastData,
          child: Text('load_forecast'.tr()),
          style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF00D4A3)),
        ),
      );
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Modell pontosság
          _buildStatCard(
            'model_accuracy'.tr(),
            '${_forecastData!.modelAccuracy > 1 ? (_forecastData!.modelAccuracy).toStringAsFixed(1) : (_forecastData!.modelAccuracy * 100).toStringAsFixed(1)}%',
            Icons.verified,
            (_forecastData!.modelAccuracy > 1 ? _forecastData!.modelAccuracy : _forecastData!.modelAccuracy * 100) > 80 ? Colors.green : Colors.orange,
          ),
          SizedBox(height: 12),

          // Trend
          _buildStatCard(
            'predicted_trend'.tr(),
            _forecastData!.trend.toUpperCase().tr(),
            _forecastData!.trend == 'növekvő' ? Icons.trending_up :
            _forecastData!.trend == 'csökkenő' ? Icons.trending_down : Icons.trending_flat,
            _forecastData!.trend == 'növekvő' ? Colors.green :
            _forecastData!.trend == 'csökkenő' ? Colors.red : Colors.blue,
          ),
          SizedBox(height: 12),

          // Szezonális minta
          if (_forecastData!.seasonalPatternDetected)
            Container(
              padding: EdgeInsets.all(16),
              margin: EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: Colors.blue.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  Icon(Icons.autorenew, color: Colors.blue),
                  SizedBox(width: 12),
                  Text(
                    'seasonal_pattern_detected'.tr(),
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: Colors.blue[800],
                    ),
                  ),
                ],
              ),
            ),

          SizedBox(height: 16),
          Text(
            'next_months_forecast'.tr(namedArgs: {'periods': _forecastData!.periodsAhead.toString()}),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),

          // Előrejelzések listája
          ...(_forecastData!.forecasts.take(6).map((forecast) =>
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    forecast.period,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('income'.tr(), style: TextStyle(color: Colors.grey[600])),
                          Text(
                            NumberFormatter.formatCurrency(forecast.predictedIncome),
                            style: TextStyle(color: Colors.green, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('expense'.tr(), style: TextStyle(color: Colors.grey[600])),
                          Text(
                            NumberFormatter.formatCurrency(forecast.predictedExpense),
                            style: TextStyle(color: Colors.red, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('balance'.tr(), style: TextStyle(color: Colors.grey[600])),
                          Text(
                            NumberFormatter.formatCurrency(forecast.predictedNet),
                            style: TextStyle(
                              color: forecast.predictedNet >= 0 ? Colors.green : Colors.red,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    'confidence_interval'.tr(namedArgs: {'lower': NumberFormatter.formatCurrency(forecast.confidenceLower), 'upper': NumberFormatter.formatCurrency(forecast.confidenceUpper)}),
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                ],
              ),
            ),
          ).toList()),
        ],
      ),
    );
  }

  Widget _buildAdvancedInsightsTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
      );
    }

    if (_advancedInsights == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: _loadAdvancedInsights,
              child: Text('load_insights'.tr()),
              style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF00D4A3)),
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadAnomalyData,
              child: Text('load_anomalies'.tr()),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadMLBudgetData,
              child: Text('ml_budget'.tr()),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.purple),
            ),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Anomáliák szekció
          if (_anomalyData != null) ...[
            Text(
              'spending_anomalies'.tr(),
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            SizedBox(height: 16),

            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    'total'.tr(),
                    '${_anomalyData!.totalAnomalies}',
                    Icons.warning_amber,
                    Colors.orange,
                  ),
                ),
                SizedBox(width: 12),
                Expanded(
                  child: _buildStatCard(
                    'high_risk'.tr(),
                    '${_anomalyData!.anomaliesBySeverity['high'] ?? 0}',
                    Icons.error,
                    Colors.red,
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),

            // Legutóbbi anomáliák
            if (_anomalyData!.recentAnomalies.isNotEmpty) ...[
              Text(
                'recent_anomalies'.tr(),
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 12),
              ...(_anomalyData!.recentAnomalies.take(3).map((anomaly) =>
                Container(
                  margin: EdgeInsets.only(bottom: 8),
                  padding: EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.red.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.warning,
                        color: anomaly.severity == 'high' ? Colors.red : Colors.orange,
                        size: 20,
                      ),
                      SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${CategoryTranslate.getLocalizedCategory(anomaly.category).tr()} - ${NumberFormatter.formatCurrency(anomaly.amount)}',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                            Text(
                              anomaly.date,
                              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                            ),
                          ],
                        ),
                      ),
                      Text(
                        anomaly.severity.toUpperCase().tr(),
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: anomaly.severity == 'high' ? Colors.red : Colors.orange,
                        ),
                      ),
                    ],
                  ),
                ),
              ).toList()),
            ],
            SizedBox(height: 24),
          ],

          // ML Költségvetés szekció
          if (_mlBudgetData != null) ...[
            Text(
              'ml_budget_recommendations'.tr(),
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            SizedBox(height: 16),

            _buildStatCard(
              'recommended_monthly_budget'.tr(),
              NumberFormatter.formatCurrency(_mlBudgetData!.totalRecommendedBudget),
              Icons.account_balance_wallet,
              Colors.green,
            ),
            SizedBox(height: 12),

            _buildStatCard(
              'spending_pattern_score'.tr(),
              () {
                double normalizedScore;
                if (_mlBudgetData!.spendingPatternScore > 1) {
                  // Ha nagyobb mint 1, akkor már százalék formában van, csak normalizáljuk 0-100 közé
                  normalizedScore = (_mlBudgetData!.spendingPatternScore).clamp(0.0, 100.0);
                } else {
                  // Ha 0-1 között van, akkor szorozzuk 100-zal
                  normalizedScore = (_mlBudgetData!.spendingPatternScore * 100).clamp(0.0, 100.0);
                }
                return '${normalizedScore.toStringAsFixed(0)}/100';
              }(),
              Icons.score,
              () {
                double normalizedScore = _mlBudgetData!.spendingPatternScore > 1
                  ? _mlBudgetData!.spendingPatternScore.clamp(0.0, 100.0)
                  : (_mlBudgetData!.spendingPatternScore * 100).clamp(0.0, 100.0);
                return normalizedScore > 70 ? Colors.green : normalizedScore > 40 ? Colors.orange : Colors.red;
              }(),
            ),
            SizedBox(height: 16),

            // Top kategória ajánlások
            Text(
              'category_recommendations'.tr(),
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            SizedBox(height: 12),

            ...(_mlBudgetData!.categoryRecommendations.take(5).map((rec) =>
              Container(
                margin: EdgeInsets.only(bottom: 8),
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 2,
                      offset: Offset(0, 1),
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
                          CategoryTranslate.getLocalizedCategory(rec.category).tr(),
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: rec.priority == 'high' ? Colors.red :
                                  rec.priority == 'medium' ? Colors.orange : Colors.green,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            rec.priority.toUpperCase().tr(),
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 4),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'recommended'.tr(namedArgs: {'amount': NumberFormatter.formatCurrency(rec.recommendedLimit)}),
                          style: TextStyle(color: Colors.green, fontSize: 12),
                        ),
                        Text(
                          'current'.tr(namedArgs: {'amount': NumberFormatter.formatCurrency(rec.currentSpending)}),
                          style: TextStyle(color: Colors.grey[600], fontSize: 12),
                        ),
                      ],
                    ),
                    if (rec.reasoning.isNotEmpty) ...[
                      SizedBox(height: 4),
                      Text(
                        rec.reasoning,
                        style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                      ),
                    ],
                  ],
                ),
              ),
            ).toList()),

            SizedBox(height: 16),

            // Személyre szabott tippek
            if (_mlBudgetData!.personalizedTips.isNotEmpty) ...[
              Text(
                'personalized_tips'.tr(),
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 12),
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: _mlBudgetData!.personalizedTips.map((tip) =>
                    Padding(
                      padding: EdgeInsets.only(bottom: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.lightbulb, color: Colors.blue, size: 16),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              tip,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.blue[800],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ).toList(),
                ),
              ),
            ],
          ],

          // Fejlett betekintések az insights adatokból
          if (_advancedInsights != null && _advancedInsights!.isNotEmpty) ...[
            SizedBox(height: 24),
            Text(
              'advanced_insights'.tr(),
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
            SizedBox(height: 16),

            // Itt feldolgozhatod az _advancedInsights Map tartalmát
            // A backend válaszának struktúrájától függ, hogyan jeleníted meg
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
              child: Text(
                'advanced_analysis_processing'.tr(),
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}