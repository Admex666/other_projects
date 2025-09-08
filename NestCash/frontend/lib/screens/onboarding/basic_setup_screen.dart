// lib/screens/onboarding/basic_setup_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/onboarding_model.dart';
import '../../services/onboarding_service.dart';
import 'package:frontend/screens/onboarding/user_intent_screen.dart';
import 'tutorial_screen.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../../services/auth_service.dart';
import '../../services/analytics_service.dart';
import '../../models/referral_model.dart';
import '../../config/config.dart';
import 'package:easy_localization/easy_localization.dart';


class BasicSetupScreen extends StatefulWidget {
  final String userType;
  final ReferralSource? referralSource;
  final String? referralDetails;
  const BasicSetupScreen({
      Key? key,
      required this.userType,
      this.referralSource,
      this.referralDetails,
    }) : super(key: key);

  @override
  _BasicSetupScreenState createState() => _BasicSetupScreenState();
}

class _BasicSetupScreenState extends State<BasicSetupScreen> with TickerProviderStateMixin {
  final OnboardingService _onboardingService = OnboardingService();
  final AnalyticsService _analyticsService = AnalyticsService();

  final _formKey = GlobalKey<FormState>();
  final _balanceController = TextEditingController();
  final _subAccountNameController = TextEditingController(); // Módosítva: alszámla név
  final _accountNameController = TextEditingController();

  String _selectedCurrency = 'HUF';
  String _selectedMainAccount = 'likvid'; // ÚJ: főszámla választás
  bool _isLoading = false;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  final List<String> _currencies = [
    'HUF',
    'EUR',
    'USD',
    'GBP',
    'CHF',
  ];

  // ÚJ: Főszámlák
  final Map<String, String> _mainAccounts = {
    'likvid': 'ob_basic_setup.main_accounts.liquid'.tr(),
    'befektetes': 'ob_basic_setup.main_accounts.investment'.tr(),
    'megtakaritas': 'ob_basic_setup.main_accounts.savings'.tr(),
  };

  final Map<String, String> _currencySymbols = {
    'HUF': 'Ft',
    'EUR': '€',
    'USD': '\$',
    'GBP': '£',
    'CHF': 'CHF',
  };

  @override
  void initState() {
    super.initState();
    _trackBasicSetupScreenView();
    _animationController = AnimationController(
      duration: Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _balanceController.dispose();
    _accountNameController.dispose();
    super.dispose();
  }

  Future<void> _trackBasicSetupScreenView() async {
    try {
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 2,
        stepType: 'basic_setup_started',
      );
    } catch (e) {
      print('Analytics tracking error: $e');
    }
  }
  /*
  String _formatCurrency(String value) {
    if (value.isEmpty) return '';

    // Remove any non-digit characters except decimal point
    String cleanValue = value.replaceAll(RegExp(r'[^\d.]'), '');

    if (cleanValue.isEmpty) return '';

    double? amount = double.tryParse(cleanValue);
    if (amount == null) return value;

    // Format with thousands separator
    String formatted = amount.toStringAsFixed(0);
    RegExp reg = RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))');
    formatted = formatted.replaceAllMapped(reg, (Match match) => '${match[1]} ');

    return '$formatted ${_currencySymbols[_selectedCurrency]}';
  }
  */

  Future<void> _saveBasicSetupAndContinue() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Track setup data
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 2,
        stepType: 'basic_setup_completed',
        additionalData: {
          'currency': _selectedCurrency,
          'main_account': _selectedMainAccount,
          'has_initial_balance': _balanceController.text.isNotEmpty,
          'has_sub_account_name': _subAccountNameController.text.isNotEmpty,
        },
      );

      // Parse balance
      String balanceText = _balanceController.text;
      double initialBalance = 0.0;

      if (balanceText.isNotEmpty) {
        String cleanBalance = balanceText.replaceAll(RegExp(r'[^\d.]'), '');
        initialBalance = double.tryParse(cleanBalance) ?? 0.0;
      }

      // Először mentjük az alapbeállításokat
      final setupData = BasicSetupData(
        preferredCurrency: _selectedCurrency,
        initialBalance: initialBalance,
        mainAccountName: _subAccountNameController.text.trim(),
        referralSource: widget.referralSource,
        referralDetails: widget.referralDetails,
      );

      await _onboardingService.saveBasicSetup(setupData);

      // Majd létrehozzuk az első alszámlát (ha van egyenleg és név)
      if (initialBalance > 0 && _subAccountNameController.text.trim().isNotEmpty) {
        await _createFirstSubAccount(initialBalance);
        await _analyticsService.trackFeatureUsage('first_sub_account_created');
      }

      if (mounted) {
        await _analyticsService.trackFeatureUsage('basic_setup_navigation_to_tutorial');
        _navigateToTutorial();

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_basic_setup.settings_saved_success_message'.tr()),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_basic_setup.error_occurred'.tr(namedArgs: {'error': e.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  // Alapértelmezett alszámla létrehozása
  Future<void> _createDefaultSubAccount() async {
    final AuthService authService = AuthService();
    final token = await authService.getToken();

    if (token == null) return;

    final response = await http.put(
      Uri.parse('${ApiConfig.baseUrl}/accounts/me/$_selectedMainAccount/Alapértelmezett'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'balance': 0.0,
        'currency': _selectedCurrency,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('ob_basic_setup.default_account_creation_failed'.tr());
    }
  }

  Future<void> _saveWithDefaultsAndContinue() async {
    setState(() => _isLoading = true);

    try {
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 2,
        stepType: 'basic_setup_skipped',
        additionalData: {
          'skipped_reason': 'user_chose_defaults',
        },
      );

      // Alapértelmezett értékek beállítása
      final setupData = BasicSetupData(
        preferredCurrency: _selectedCurrency,
        initialBalance: 0.0, // Alapértelmezett: 0
        mainAccountName: 'ob_basic_setup.default_account_name'.tr(), // Alapértelmezett név
      );

      await _onboardingService.saveBasicSetup(setupData);

      // Alapértelmezett alszámla létrehozása ha szükséges
      await _createDefaultSubAccount();

      if (mounted) {
        _navigateToTutorial();

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_basic_setup.default_settings_saved_success_message'.tr()),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_basic_setup.error_occurred'.tr(namedArgs: {'error': e.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  // ÚJ: Első alszámla létrehozása
  Future<void> _createFirstSubAccount(double balance) async {
    final AuthService authService = AuthService();
    final token = await authService.getToken();

    if (token == null) return;

    final subAccountName = _subAccountNameController.text.trim();
    final response = await http.put(
      Uri.parse('${ApiConfig.baseUrl}/accounts/me/$_selectedMainAccount/$subAccountName'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'balance': balance,
        'currency': _selectedCurrency,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('ob_basic_setup.sub_account_creation_failed'.tr());
    }
  }

  void _navigateToTutorial() {
    // TODO: Navigate to appropriate tutorial screen
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('ob_basic_setup.setup_complete_dialog_title'.tr()),
        content: Text('ob_basic_setup.setup_complete_dialog_content'.tr()),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();

              final userTypeEnum = UserTypeExtension.fromString(widget.userType); // Konvertálás a statikus metódussal

              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => TutorialScreen(userType: userTypeEnum,)),
              );
            },
            child: Text('ob_basic_setup.continue_button'.tr()),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
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
        child: SafeArea(
          child: Column(
            children: [
              // Header
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.arrow_back, color: Colors.black),
                      onPressed: () {
                        Navigator.pushReplacement(
                          context,
                          PageRouteBuilder(
                            pageBuilder: (context, animation, secondaryAnimation) => UserIntentScreen(),
                            transitionsBuilder: (context, animation, secondaryAnimation, child) {
                              return SlideTransition(
                                position: Tween<Offset>(
                                  begin: Offset(-1.0, 0.0),
                                  end: Offset.zero,
                                ).animate(animation),
                                child: child,
                              );
                            },
                            transitionDuration: Duration(milliseconds: 300),
                          ),
                        );
                      },
                    ),
                    Expanded(
                      child: Column(
                        children: [
                          Text(
                            'ob_basic_setup.step_number'.tr(),
                            style: TextStyle(
                              color: Colors.black.withOpacity(0.8),
                              fontSize: 14,
                            ),
                          ),
                          Text(
                            'ob_basic_setup.title'.tr(),
                            style: TextStyle(
                              color: Colors.black,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Progress indicator
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.grey.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Center(
                        child: Text(
                          '3/4',
                          style: TextStyle(
                            color: Colors.black,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Content
              Expanded(
                child: Container(
                  margin: EdgeInsets.symmetric(horizontal: 0),
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: SingleChildScrollView(
                      padding: EdgeInsets.all(24),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(height: 16),

                            // Title and Description módosítása:
                            Text(
                              'ob_basic_setup.first_account_title'.tr(),
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 12),
                            Text(
                              'ob_basic_setup.first_account_description'.tr(),
                              style: TextStyle(
                                fontSize: 16,
                                color: Colors.grey[600],
                                height: 1.4,
                              ),
                            ),

                            SizedBox(height: 40),

                            // ÚJ: Főszámla választás
                            Text(
                              'ob_basic_setup.main_account_prompt'.tr(),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w600,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 12),
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.grey[300]!),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 8,
                                    offset: Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: DropdownButtonFormField<String>(
                                value: _selectedMainAccount,
                                decoration: InputDecoration(
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                                  prefixIcon: Icon(
                                    Icons.account_balance,
                                    color: Color(0xFF00D4A3),
                                  ),
                                ),
                                items: _mainAccounts.entries.map((entry) {
                                  return DropdownMenuItem(
                                    value: entry.key,
                                    child: Text(entry.value),
                                  );
                                }).toList(),
                                onChanged: (value) {
                                  setState(() {
                                    _selectedMainAccount = value!;
                                  });
                                  _analyticsService.trackFeatureUsage('main_account_selected_$value');
                                },
                              ),
                            ),

                            SizedBox(height: 32),

                            // Currency Selection
                            Text(
                              'ob_basic_setup.preferred_currency'.tr(),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w600,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 12),
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.grey[300]!),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 8,
                                    offset: Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: DropdownButtonFormField<String>(
                                value: _selectedCurrency,
                                decoration: InputDecoration(
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                                  hintText: 'ob_basic_setup.currency_hint'.tr(),
                                ),
                                items: _currencies.map((currency) {
                                  return DropdownMenuItem(
                                    value: currency,
                                    child: Row(
                                      children: [
                                        Text(
                                          _currencySymbols[currency]!,
                                          style: TextStyle(
                                            fontWeight: FontWeight.bold,
                                            color: Color(0xFF00D4A3),
                                          ),
                                        ),
                                        SizedBox(width: 12),
                                        Text(currency),
                                      ],
                                    ),
                                  );
                                }).toList(),
                                onChanged: (value) {
                                  setState(() {
                                    _selectedCurrency = value!;
                                  });
                                  _analyticsService.trackFeatureUsage('currency_selected_$value');
                                },
                              ),
                            ),

                            SizedBox(height: 32),

                            // Initial Balance
                            Text(
                              'ob_basic_setup.initial_balance_label'.tr(),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w600,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 12),
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.grey[300]!),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 8,
                                    offset: Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: TextFormField(
                                controller: _balanceController,
                                keyboardType: TextInputType.numberWithOptions(decimal: true),
                                inputFormatters: [
                                  FilteringTextInputFormatter.allow(RegExp(r'[\d\s.,]')),
                                ],
                                decoration: InputDecoration(
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                                  hintText: '0 ${_currencySymbols[_selectedCurrency]}',
                                  hintStyle: TextStyle(color: Colors.grey[400]),
                                  prefixIcon: Icon(
                                    Icons.account_balance_wallet_outlined,
                                    color: Color(0xFF00D4A3),
                                  ),
                                ),
                                onChanged: (value) {
                                  // Live formatting would go here if needed
                                },
                              ),
                            ),
                            Padding(
                              padding: EdgeInsets.only(left: 16, top: 8),
                              child: Text(
                                'ob_basic_setup.initial_balance_info'.tr(),
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[500],
                                ),
                              ),
                            ),

                            SizedBox(height: 32),

                            // Account Name
                            Text(
                              'ob_basic_setup.sub_account_name_label'.tr(),
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w600,
                                color: Colors.black87,
                              ),
                            ),
                            SizedBox(height: 12),
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.grey[300]!),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 8,
                                    offset: Offset(0, 2),
                                  ),
                                ],
                              ),
                              child: TextFormField(
                                controller: _subAccountNameController,
                                decoration: InputDecoration(
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                                  hintText: 'ob_basic_setup.sub_account_name_hint'.tr(),
                                  hintStyle: TextStyle(color: Colors.grey[400]),
                                  prefixIcon: Icon(
                                    Icons.account_circle_outlined,
                                    color: Color(0xFF00D4A3),
                                  ),
                                ),
                                validator: (value) {
                                  if (value == null || value.trim().isEmpty) {
                                    return 'ob_basic_setup.sub_account_name_validation'.tr();
                                  }
                                  return null;
                                },
                              ),
                            ),

                            SizedBox(height: 48),

                            // Info Box
                            Container(
                              padding: EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: Color(0xFF00D4A3).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: Color(0xFF00D4A3).withOpacity(0.3),
                                ),
                              ),
                              child: Row(
                                children: [
                                  Icon(
                                    Icons.info_outline,
                                    color: Color(0xFF00D4A3),
                                    size: 24,
                                  ),
                                  SizedBox(width: 16),
                                  Expanded(
                                    child: Text(
                                      'ob_basic_setup.info_box_text'.tr(),
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Color(0xFF00D4A3),
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            SizedBox(height: 40),

                            // Continue Button
                            Container(
                              width: double.infinity,
                              height: 56,
                              child: ElevatedButton(
                                onPressed: _isLoading ? null : _saveBasicSetupAndContinue,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Color(0xFF00D4A3),
                                  foregroundColor: Colors.white,
                                  elevation: 0,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(28),
                                  ),
                                ),
                                child: _isLoading
                                    ? CircularProgressIndicator(color: Colors.white)
                                    : Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Text(
                                            'ob_basic_setup.save_button'.tr(),
                                            style: TextStyle(
                                              fontSize: 18,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                          SizedBox(width: 8),
                                          Icon(Icons.arrow_forward, size: 20),
                                        ],
                                      ),
                              ),
                            ),

                            SizedBox(height: 16),

                            // Skip Button
                            Center(
                              child: TextButton(
                                onPressed: _isLoading ? null : _saveWithDefaultsAndContinue, // Módosítva
                                child: Text(
                                  'ob_basic_setup.skip_button'.tr(),
                                  style: TextStyle(
                                    color: Colors.grey[600],
                                    fontSize: 16,
                                    decoration: TextDecoration.underline,
                                  ),
                                ),
                              ),
                            ),

                            SizedBox(height: 32),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}