import 'package:flutter/material.dart';
import 'package:frontend/models/challenge.dart';
import 'package:frontend/models/limit.dart';
import 'package:frontend/services/challenge_service.dart';
import 'package:frontend/services/transaction_service.dart';
import 'package:frontend/services/account_service.dart';
import 'package:frontend/services/limit_service.dart';
import 'package:frontend/widgets/pti_summary_widget.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/add_incomes_screen.dart';
import 'package:frontend/screens/challenges/challenges_main_screen.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/screens/transactions_screen.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:intl/intl.dart';
import 'package:easy_localization/easy_localization.dart'; 
import 'package:frontend/utils/category_translate.dart';
import 'package:frontend/services/nestcash_analytics_service.dart';

class DashboardScreen extends StatefulWidget {
  final String username;
  final String? userId;

  const DashboardScreen({
    required this.username, 
    this.userId,
  });

  @override
  _DashboardScreenState createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ChallengeService _challengeService = ChallengeService();
  final AuthService _authService = AuthService();
  
  bool _isLoading = true;
  List<Challenge> _recommendedChallenges = [];
  
  // Placeholder data - ezeket API hívásokkal kell lecserélni
  double _netBalance = 0.0;
  double _totalIncome = 0.0;
  double _totalExpenses = 0.0;
  List<Map<String, dynamic>> _recentTransactions = [];
  List<Limit> _warningLimits = [];

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await NestCashAnalyticsService.trackScreenView('dashboard_screen');
    });

    _loadDashboardData();
  }

  void _handleAuthError() {
    print('AUTH ERROR HANDLER CALLED!');
    _authService.logout();
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('auth_session_expired'.tr()), // Localized string
          backgroundColor: Colors.red,
        ),
      );
      
      // Navigáció az AuthWrapper-re (ugyanúgy mint a ProfileScreen-ben)
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => AuthWrapper()),
        (Route<dynamic> route) => false,
      );
    }
  }

  Future<void> _loadDashboardData() async {
    final startTime = DateTime.now();

    await NestCashAnalyticsService.trackFeatureUsed('dashboard_refresh');

    print('Loading dashboard data...');
    setState(() => _isLoading = true);
    
    // Párhuzamosan töltjük be az adatokat, de külön-külön kezeljük a hibákat
    final results = await Future.wait([
      _loadBalanceDataSafely(),
      _loadRecentTransactionsSafely(), 
      _loadLimitWarningsSafely(),
      _loadRecommendedChallengesSafely(),
    ]);
    
    final hasAnyError = results.any((result) => result == false);
    
    if (hasAnyError && mounted) {
      // Csak akkor mutatunk hibaüzenetet, ha kritikus hiba van
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('some_data_load_failed'.tr()), // Localized string
          backgroundColor: Colors.orange,
          duration: Duration(seconds: 3),
        ),
      );
    }
    
    if (mounted) {
      setState(() => _isLoading = false);
    }
    
    print('Dashboard data loading completed');

    final duration = DateTime.now().difference(startTime);
      await NestCashAnalyticsService.trackPerformanceMetric(
        'dashboard_load',
        duration.inMilliseconds,
        screenName: 'dashboard_screen',
        thresholdMs: 3000, // Ha 3 másodpercnél tovább tart, performance issue
      );
  }

  bool _isAuthError(dynamic error) {
    print('Checking for auth error: $error');
    print('Error type: ${error.runtimeType}');
    
    // Explicit AuthService kivételek
    if (error.toString().contains('401: Unauthorized')) {
      print('AuthService 401 exception detected');
      return true;
    }
    
    // HTTP státusz kódok ellenőrzése
    if (error.toString().contains('HTTP 401') || 
        error.toString().contains('401:')) {
      print('401 HTTP error detected');
      return true;
    }
    
    final errorStr = error.toString().toLowerCase();
    bool isAuth = errorStr.contains('401') || 
          errorStr.contains('unauthorized') || 
          errorStr.contains('not authenticated') ||
          errorStr.contains('unauthenticated') ||
          (errorStr.contains('token') && (errorStr.contains('invalid') || errorStr.contains('expired'))) ||
          errorStr.contains('authentication failed') ||
          errorStr.contains('access denied');
          
    print('Is auth error: $isAuth');
    return isAuth;
  }

  Future<bool> _loadBalanceDataSafely() async {
    try {
      await _loadBalanceData();
      return true;
    } catch (e) {
      print('Balance loading failed: $e');
      print('Error type: ${e.runtimeType}');
      print('Error string for auth check: ${e.toString().toLowerCase()}');

      if (_isAuthError(e)) {
        print('Authentication error detected! Calling _handleAuthError().');
        _handleAuthError();
        return false; // Fontos: return false auth error esetén
      } else {
        print('Not an authentication error according to _isAuthError.');
      }
      
      return false;
    }
  }

  // Biztonságos tranzakció betöltés  
  Future<bool> _loadRecentTransactionsSafely() async {
    try {
      await _loadRecentTransactions();
      return true;
    } catch (e) {
      print('Recent transactions loading failed: $e');
      
      if (_isAuthError(e)) {
      _handleAuthError();
    }

      return false;
    }
  }

  // Biztonságos limit figyelmeztetések betöltés
  Future<bool> _loadLimitWarningsSafely() async {
    try {
      await _loadLimitWarnings();
      return true;
    } catch (e) {
      print('Limit warnings loading failed: $e');

      if (_isAuthError(e)) {
      _handleAuthError();
    }
      // Üres lista esetén nincs hiba
      setState(() => _warningLimits = []);
      return true;
    }
  }

  // Biztonságos kihívások betöltés
  Future<bool> _loadRecommendedChallengesSafely() async {
    try {
      await _loadRecommendedChallenges();
      return true;
    } catch (e) {
      print('Recommended challenges loading failed: $e');

      if (_isAuthError(e)) {
      _handleAuthError();
    }
      
      // Üres lista esetén nincs hiba
      setState(() => _recommendedChallenges = []);
      return true;
    }
  }

  // Javított _loadBalanceData() metódus implementálása
  Future<void> _loadBalanceData() async {
    try {
      final accountService = AccountService();
      final transactionService = TransactionService();
      
      // Számlák összesítésének lekérése (ez adja a valós egyenlegeket)
      final accountSummary = await accountService.getAccountSummary();
      
      // Havi tranzakciós statisztikák lekérése (bevételek/kiadások)
      final monthlyStats = await transactionService.getMonthlyStats();
      
      setState(() {
        // A valós számlaegyenleg az AccountService-ből jön
        _netBalance = accountSummary['total'] ?? 0.0;
        
        // A havi bevételek és kiadások a TransactionService-ből jönnek
        _totalIncome = (monthlyStats['total_income'] as num?)?.toDouble() ?? 0.0;
        _totalExpenses = (monthlyStats['total_expenses'] as num?)?.toDouble() ?? 0.0;
      });
    } catch (e) {
      print('Error loading balance data: $e');
      // Fallback: próbáljuk meg csak az AccountService-t használni
      try {
        final accountService = AccountService();
        final accountSummary = await accountService.getAccountSummary();
        
        setState(() {
          _netBalance = accountSummary['total'] ?? 0.0;
          // Ha a TransactionService nem működik, akkor placeholder adatok
          _totalIncome = 450000.0;
          _totalExpenses = 320000.0;
        });
      } catch (e2) {
        print('Error loading account data: $e2');
        // Végső fallback adatok
        setState(() {
          _totalIncome = 450000.0;
          _totalExpenses = 320000.0;
          _netBalance = _totalIncome - _totalExpenses;
        });
      }
    }
  }

  // A _loadRecentTransactions() metódus implementálása
  Future<void> _loadRecentTransactions() async {
    try {
      final transactionService = TransactionService();
      final transactions = await transactionService.getRecentTransactions(limit: 5);
      
      print('Loaded ${transactions.length} recent transactions'); // Debug log
      
      setState(() {
        _recentTransactions = transactions.map((transaction) {
          try {
            // Több lehetséges mező nevvel számolunk (angol/magyar backend szerint)
            final type = transaction['type'] ?? transaction['tipus'];
            final amount = (transaction['amount'] ?? transaction['osszeg'] ?? 0 as num).toDouble();
            final description = transaction['description'] ?? transaction['leiras'] ?? 'unknown_transaction'.tr(); // Localized string
            final category = transaction['kategoria'] ?? transaction['category'] ?? 'other'.tr(); // Localized string
            final dateStr = transaction['date'] ?? transaction['datum'];
            
            // Dátum parse-olás több formátummal
            DateTime date = DateTime.now();
            if (dateStr != null) {
              try {
                date = DateTime.parse(dateStr.toString());
              } catch (e) {
                print('Error parsing date: $dateStr, using current date');
              }
            }
            
            // Típus meghatározása
            bool isExpense = false;
            if (type != null) {
              isExpense = type == 'expense' || type == 'kiadas';
            } else {
              // Ha nincs típus, az összeg alapján döntünk
              isExpense = amount < 0;
            }
            
            return {
              'id': transaction['id'] ?? transaction['_id'] ?? '',
              'title': description,
              'amount': amount,
              'category': category,
              'date': date,
              'isExpense': isExpense,
              'icon': _getTransactionIcon(category, isExpense),
            };
          } catch (e) {
            print('Error processing transaction: $transaction, error: $e');
            // Fallback transaction
            return {
              'id': '',
              'title': 'invalid_transaction'.tr(), // Localized string
              'amount': 0.0,
              'category': 'other'.tr(), // Localized string
              'date': DateTime.now(),
              'isExpense': false,
              'icon': Icons.error,
            };
          }
        }).toList();
      });
      
      print('Successfully processed ${_recentTransactions.length} transactions'); // Debug log
    } catch (e) {
      print('Error loading recent transactions: $e');
      // Fallback: megtartjuk a placeholder adatokat, de jelezzük, hogy nem sikerült betölteni
      setState(() {
        _recentTransactions = [
          {
            'id': 'error',
            'title': 'transactions_load_failed'.tr(), // Localized string
            'amount': 0.0,
            'category': 'error'.tr(), // Localized string
            'date': DateTime.now(),
            'isExpense': false,
            'icon': Icons.error_outline,
          }
        ];
      });
    }
  }

  // Segéd metódus ikonok meghatározásához
IconData _getTransactionIcon(String category, bool isExpense) {
    if (!isExpense) {
      return Icons.attach_money;
    }
    
    switch (category.toLowerCase()) {
      case 'élelmiszer':
      case 'food':
        return Icons.restaurant;
      case 'lakhatás':
      case 'housing':
        return Icons.home;
      case 'közlekedés':
      case 'transport':
        return Icons.directions_car;
      case 'szórakozás':
      case 'entertainment':
        return Icons.movie;
      case 'ruházat':
      case 'clothing':
        return Icons.shopping_bag;
      case 'egészség':
      case 'health':
        return Icons.local_hospital;
      case 'oktatás':
      case 'education':
        return Icons.school;
      default:
        return Icons.shopping_cart;
    }
  }

  Future<void> _loadLimitWarnings() async {
    try {
      final limitService = LimitService();
      final limits = await limitService.getLimits(activeOnly: true);
      
      // Csak azokat a limiteket mutatjuk, amelyek túllépés közelében vannak (80% felett)
      final warningLimits = limits.where((limit) {
        final usagePercentage = limit.usagePercentage ?? 0.0;
        return usagePercentage >= 0.8; // 80% felett figyelmeztetés
      }).toList();
      
      setState(() {
        _warningLimits = warningLimits;
      });
    } catch (e) {
      print('Error loading limit warnings: $e');
      // Üres lista marad
    }
  }

  Future<void> _loadRecommendedChallenges() async {
    try {
      final challenges = await _challengeService.getRecommendedChallenges(limit: 3);
      setState(() {
        _recommendedChallenges = challenges;
      });
    } catch (e) {
      print('Error loading recommended challenges: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        body: Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
          ),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            try {
              await _loadDashboardData();
            } catch (e) {
              if (_isAuthError(e)) {
                _handleAuthError();
              }
            }
          },
          color: Color(0xFF00D4A3),
          child: SingleChildScrollView(
            physics: AlwaysScrollableScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Fejléc gradient háttér
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Color(0xFF00D4A3),
                        Color(0xFFE8F6F3),
                      ],
                      stops: [0.0, 1.0],
                    ),
                  ),
                  child: Column(
                    children: [
                      SizedBox(height: 20),
                      _buildSummaryCards(),
                      SizedBox(height: 20),
                    ],
                  ),
                ),

                // Fő tartalom
                Container(
                  decoration: BoxDecoration(
                    color: Color(0xFFF0F8F0),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: Column(
                    children: [
                      SizedBox(height: 20),
                      
                      // Korlát figyelmeztetések
                      if (_warningLimits.isNotEmpty) _buildLimitWarnings(),
                      
                      // PTI Widget
                      if (widget.userId != null)
                        PTISummaryWidget(
                          userId: widget.userId!,
                          username: widget.username,
                        ),
                      
                      // Ajánlott kihívások
                      if (_recommendedChallenges.isNotEmpty) _buildRecommendedChallenges(),
                      
                      // Legutóbbi tranzakciók
                      _buildRecentTransactions(),
                      
                      SizedBox(height: 100), // Bottom navigation padding
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      floatingActionButton: _buildQuickAddButton(),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }

  Widget _buildSummaryCards() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          // Nettó egyenleg kártya
          Container(
            width: double.infinity,
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
              children: [
                Text(
                  'net_balance'.tr(), // Localized string
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 14,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  '${_formatCurrency(_netBalance)}',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: _netBalance >= 0 ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ),
          
          SizedBox(height: 16),
          
          // Bevétel és kiadás kártyák
          Row(
            children: [
              Expanded(
                child: _buildBalanceCard(
                  'monthly_incomes'.tr(), // Localized string
                  _totalIncome,
                  Color(0xFF00D4A3),
                  Icons.trending_up,
                ),
              ),
              SizedBox(width: 16),
              Expanded(
                child: _buildBalanceCard(
                  'monthly_expenses'.tr(), // Localized string
                  _totalExpenses,
                  Colors.redAccent,
                  Icons.trending_down,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBalanceCard(String title, double amount, Color color, IconData icon) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 20),
              ),
              Spacer(),
            ],
          ),
          SizedBox(height: 12),
          Text(
            title,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 12,
            ),
          ),
          SizedBox(height: 4),
          Text(
            _formatCurrency(amount),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLimitWarnings() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'warnings'.tr(), // Localized string
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 12),
          ..._warningLimits.map((limit) => _buildLimitWarningCard(limit)),
        ],
      ),
    );
  }

  Widget _buildLimitWarningCard(Limit limit) {
    // Százalék számítás javítása
    double percentage = (limit.usagePercentage ?? 0);
    
    // Ha az érték nagyobb mint 1, akkor már százalékban van
    if (percentage > 1) {
      percentage = percentage / 100;
    }
    
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.orange.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.orange.shade200),
      ),
      child: Row(
        children: [
          Icon(
            Icons.warning,
            color: Colors.orange,
            size: 24,
          ),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  limit.name,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                Text(
                  '${_formatCurrency(limit.currentSpending ?? 0)} / ${_formatCurrency(limit.amount)}',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${(percentage * 100).toStringAsFixed(0)}%', // Javítás itt
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.orange,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendedChallenges() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'recommended_challenges'.tr(), // Localized string
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              TextButton(
                onPressed: () {
                  Navigator.push(
                     context,
                     MaterialPageRoute(
                       builder: (context) => ChallengesMainScreen(
                        userId: widget.userId!, 
                        username: widget.username,
                        ),
                     ),
                   );
                },
                child: Text(
                  'all'.tr(), // Localized string
                  style: TextStyle(color: Color(0xFF00D4A3)),
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          SizedBox(
            height: 175,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _recommendedChallenges.length,
              itemBuilder: (context, index) {
                final challenge = _recommendedChallenges[index];
                return _buildChallengeCard(challenge);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChallengeCard(Challenge challenge) {
    return Container(
      width: 280,
      margin: EdgeInsets.only(right: 16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Color(0xFF00D4A3).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  challenge.difficulty.displayName,
                  style: TextStyle(
                    color: Color(0xFF00D4A3),
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Spacer(),
              Text(
                '${challenge.durationDays} ' + 'days_abbr'.tr(), // Localized string
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          Text(
            challenge.title,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          SizedBox(height: 8),
          Text(
            challenge.shortDescription ?? challenge.description,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 12,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          Spacer(),
          Row(
            children: [
              Icon(
                Icons.people,
                size: 16,
                color: Colors.grey[600],
              ),
              SizedBox(width: 4),
              Text(
                '${challenge.participantCount} ' + 'participants_abbr'.tr(), // Localized string
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
              Spacer(),
              Icon(
                Icons.emoji_events,
                size: 16,
                color: Colors.amber,
              ),
              SizedBox(width: 4),
              Text(
                '${challenge.rewards.points} ' + 'points_abbr'.tr(), // Localized string
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRecentTransactions() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'recent_transactions'.tr(), // Localized string
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              TextButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => TransactionsScreen(
                        userId: widget.userId!,
                        username: widget.username,
                      ),
                    ),
                  );
                },
                child: Text(
                  'all'.tr(), // Localized string
                  style: TextStyle(color: Color(0xFF00D4A3)),
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          ..._recentTransactions.take(5).map((transaction) => _buildTransactionItem(transaction)),
        ],
      ),
    );
  }

  Widget _buildTransactionItem(Map<String, dynamic> transaction) {
    final isExpense = transaction['isExpense'] as bool;
    final amount = transaction['amount'] as double;
    final date = transaction['date'] as DateTime;
    
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () async {
          await NestCashAnalyticsService.trackFeatureUsed(
            'transaction_item_tap',
            parameters: {
              'transaction_id': transaction['id'],
              'transaction_type': transaction['isExpense'] ? 'expense' : 'income',
              'category': transaction['category'],
            },
          );
          // Navigate to transaction details
        },
        child: Row(
          children: [
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: (isExpense ? Colors.red : Colors.green).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                transaction['icon'] as IconData,
                color: isExpense ? Colors.red : Colors.green,
                size: 24,
              ),
            ),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    transaction['title'] as String,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  Text(
                    '${_formatDate(date)} • ${CategoryTranslate.getLocalizedCategory(transaction['category']).tr()}',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Text(
              _formatCurrency(amount),
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
                color: isExpense ? Colors.red : Colors.green,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickAddButton() {
    return Container(
      margin: EdgeInsets.only(bottom: 40),
      child: FloatingActionButton.extended(
        onPressed: _showQuickAddDialog,
        backgroundColor: Color(0xFF00D4A3),
        icon: Icon(Icons.add, color: Colors.white),
        label: Text(
          'quick_add'.tr(), // Localized string
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  void _showQuickAddDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (BuildContext context) {
        return Container(
          padding: EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'quick_add'.tr(), // Localized string
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        if (widget.userId != null) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => AddIncomesScreen(userId: widget.userId!),
                            ),
                          );
                        }
                      },
                      icon: Icon(Icons.add, color: Colors.white),
                      label: Text('income'.tr(), style: TextStyle(color: Colors.white)), // Localized string
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Color(0xFF00D4A3),
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        if (widget.userId != null) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => AddExpensesScreen(userId: widget.userId!),
                            ),
                          );
                        }
                      },
                      icon: Icon(Icons.remove, color: Colors.white),
                      label: Text('expense'.tr(), style: TextStyle(color: Colors.white)), // Localized string
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent,
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
  
  String _formatCurrency(double amount) {
    final absAmount = amount.abs();
    final sign = amount < 0 ? '-' : '';

    // Használjuk az intl csomag NumberFormat osztályát a szám tagolásához
    // A 'hu' locale használatával a magyar formátumot kapjuk, ami szóközzel tagol
    final formatter = NumberFormat('#,##0', 'hu'); 
    
    // Formázzuk az abszolút értéket
    final formattedAmount = formatter.format(absAmount);

    return '$sign$formattedAmount ' + 'currency'.tr(); // Localized string
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date).inDays;
    
    if (difference == 0) {
      return 'today'.tr(); // Localized string
    } else if (difference == 1) {
      return 'yesterday'.tr(); // Localized string
    } else if (difference < 7) {
      return 'days_ago'.tr(namedArgs: {'days': difference.toString()}); // Localized string with parameter
    } else {
      return '${date.month}/${date.day}';
    }
  }
}