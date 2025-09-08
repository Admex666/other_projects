// lib/screens/onboarding/user_intent_screen.dart

import 'package:flutter/material.dart';
import '../../models/onboarding_model.dart';
import '../../services/onboarding_service.dart';
import 'basic_setup_screen.dart';
import 'package:frontend/screens/onboarding/welcome_screen.dart';
import '../../services/analytics_service.dart';
import 'package:frontend/screens/onboarding/referral_screen.dart';
import 'package:easy_localization/easy_localization.dart';

class UserIntentScreen extends StatefulWidget {
  const UserIntentScreen({Key? key}) : super(key: key);

  @override
  _UserIntentScreenState createState() => _UserIntentScreenState();
}

class _UserIntentScreenState extends State<UserIntentScreen> with TickerProviderStateMixin {
  final OnboardingService _onboardingService = OnboardingService();
  final AnalyticsService _analyticsService = AnalyticsService();

  final Set<UserIntent> _selectedIntents = {};
  bool _isLoading = false;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _trackIntentScreenView();
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
    super.dispose();
  }

  Future<void> _trackIntentScreenView() async {
    try {
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 1,
        stepType: 'intent_selection_started',
      );
    } catch (e) {
      print('Analytics tracking error: $e');
    }
  }

  void _toggleIntent(UserIntent intent) {
    setState(() {
      if (_selectedIntents.contains(intent)) {
        _selectedIntents.remove(intent);
      } else {
        _selectedIntents.add(intent);
        // Track intent selection
        _analyticsService.trackFeatureUsage('intent_selected_${intent.toString().split('.').last}');
      }
    });
  }

  Future<void> _saveIntentsAndContinue() async {
    if (_selectedIntents.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('ob_user_intent.at_least_one_option'.tr()),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Track completion
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 1,
        stepType: 'intent_selection_completed',
        additionalData: {
          'selected_intents': _selectedIntents.map((e) => e.toString()).toList(),
          'intent_count': _selectedIntents.length,
        },
      );

      final result = await _onboardingService.saveUserIntents(_selectedIntents.toList());
      
      if (mounted) {
        // Track user type determination
        await _analyticsService.trackFeatureUsage('user_type_determined');

        final determinedTypeString = result['determined_type']?.toString().split('.').last ?? 'aware_spender';

        Navigator.push(
          context,
          PageRouteBuilder(
            pageBuilder: (context, animation, secondaryAnimation) => ReferralScreen(userType: determinedTypeString),
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              return SlideTransition(
                position: Tween<Offset>(
                  begin: Offset(1.0, 0.0),
                  end: Offset.zero,
                ).animate(animation),
                child: child,
              );
            },
            transitionDuration: Duration(milliseconds: 300),
          ),
        );

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_user_intent.type_determined_message'.tr(namedArgs: {'type': result['determined_type']?.toString().split('.').last ?? 'ob_user_intent.unknown_type'.tr()})),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_user_intent.error_occurred'.tr(namedArgs: {'error': e.toString()})),
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
                            pageBuilder: (context, animation, secondaryAnimation) => WelcomeScreen(),
                            transitionsBuilder: (context, animation, secondaryAnimation, child) {
                              return SlideTransition(
                                position: Tween<Offset>(
                                  begin: Offset(-1.0, 0.0), // balról jön be
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
                            'ob_user_intent.step_1'.tr(),
                            style: TextStyle(
                              color: Colors.black.withOpacity(0.8),
                              fontSize: 14,
                            ),
                          ),
                          Text(
                            'ob_user_intent.goal_assessment'.tr(),
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
                          '1/4',
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
                    child: Column(
                      children: [
                        SizedBox(height: 32),
                        
                        // Title and Description
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 24),
                          child: Column(
                            children: [
                              Text(
                                'ob_user_intent.title'.tr(),
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 24,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.black87,
                                ),
                              ),
                              SizedBox(height: 12),
                              Text(
                                'ob_user_intent.description'.tr(),
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.grey[600],
                                  height: 1.4,
                                ),
                              ),
                            ],
                          ),
                        ),

                        SizedBox(height: 32),

                        // Intent Options
                        Expanded(
                          child: SingleChildScrollView(
                            padding: EdgeInsets.symmetric(horizontal: 24),
                            child: Column(
                              children: UserIntent.values.map((intent) {
                                return Container(
                                  margin: EdgeInsets.only(bottom: 16),
                                  child: _buildIntentCard(intent),
                                );
                              }).toList(),
                            ),
                          ),
                        ),

                        // Continue Button
                        Container(
                          padding: EdgeInsets.all(24),
                          child: Column(
                            children: [
                              Container(
                                width: double.infinity,
                                height: 56,
                                child: ElevatedButton(
                                  onPressed: _isLoading ? null : _saveIntentsAndContinue,
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
                                              'ob_user_intent.continue_button'.tr(),
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
                              
                              Text(
                                'ob_user_intent.selected_options_count'.tr(namedArgs: {'count': _selectedIntents.length.toString()}),
                                style: TextStyle(
                                  color: Colors.grey[600],
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
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

  Widget _buildIntentCard(UserIntent intent) {
    final isSelected = _selectedIntents.contains(intent);
    
    return GestureDetector(
      onTap: () => _toggleIntent(intent),
      child: AnimatedContainer(
        duration: Duration(milliseconds: 200),
        padding: EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isSelected ? Color(0xFF00D4A3).withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? Color(0xFF00D4A3) : Colors.grey[300]!,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 8,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            // Selection indicator
            Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? Color(0xFF00D4A3) : Colors.transparent,
                border: Border.all(
                  color: isSelected ? Color(0xFF00D4A3) : Colors.grey[400]!,
                  width: 2,
                ),
              ),
              child: isSelected
                  ? Icon(Icons.check, color: Colors.white, size: 16)
                  : null,
            ),
            
            SizedBox(width: 16),
            
            // Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    intent.displayName,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: isSelected ? Color(0xFF00D4A3) : Colors.black87,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    intent.description,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}