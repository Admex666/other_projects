// lib/screens/onboarding/referral_screen.dart

import 'package:flutter/material.dart';
import '../../models/referral_model.dart';
import '../../services/analytics_service.dart';
import 'basic_setup_screen.dart';

class ReferralScreen extends StatefulWidget {
  final String userType;

  const ReferralScreen({
    Key? key,
    required this.userType,
  }) : super(key: key);

  @override
  _ReferralScreenState createState() => _ReferralScreenState();
}

class _ReferralScreenState extends State<ReferralScreen> with TickerProviderStateMixin {
  final AnalyticsService _analyticsService = AnalyticsService();
  
  ReferralSource? _selectedSource;
  String? _otherDetails;
  final TextEditingController _detailsController = TextEditingController();
  
  bool _isLoading = false;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _trackReferralScreenView();
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
    _detailsController.dispose();
    super.dispose();
  }

  Future<void> _trackReferralScreenView() async {
    try {
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 2,
        stepType: 'referral_selection_started',
      );
    } catch (e) {
      print('Analytics tracking error: $e');
    }
  }

  void _selectSource(ReferralSource source) {
    setState(() {
      _selectedSource = source;
    });
    
    // Track referral source selection
    _analyticsService.trackFeatureUsage('referral_source_selected_${source.value}');
  }

  Future<void> _continueToBasicSetup() async {
    if (_selectedSource == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Kérjük, válassz egy opciót!'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Track completion
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 2,
        stepType: 'referral_selection_completed',
        additionalData: {
          'referral_source': _selectedSource!.value,
          'has_details': _otherDetails?.isNotEmpty ?? false,
        },
      );

      if (mounted) {
        Navigator.push(
          context,
          PageRouteBuilder(
            pageBuilder: (context, animation, secondaryAnimation) => BasicSetupScreen(
              userType: widget.userType,
              referralSource: _selectedSource!,
              referralDetails: _otherDetails,
            ),
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
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba történt: ${e.toString()}'),
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
                      onPressed: () => Navigator.pop(context),
                    ),
                    Expanded(
                      child: Column(
                        children: [
                          Text(
                            '2. lépés',
                            style: TextStyle(
                              color: Colors.black.withOpacity(0.8),
                              fontSize: 14,
                            ),
                          ),
                          Text(
                            'Honnan hallottál rólunk?',
                            style: TextStyle(
                              color: Colors.black,
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.grey.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Center(
                        child: Text(
                          '2/4',
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
                                'Segíts megértenünk!',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 24,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.black87,
                                ),
                              ),
                              SizedBox(height: 12),
                              Text(
                                'Honnan hallottál a NestCash-ről? Ez segít nekünk jobban megérteni, hogyan találnak meg minket az emberek.',
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

                        // Referral Source Options
                        Expanded(
                          child: SingleChildScrollView(
                            padding: EdgeInsets.symmetric(horizontal: 24),
                            child: Column(
                              children: ReferralSource.values.map((source) {
                                return Container(
                                  margin: EdgeInsets.only(bottom: 16),
                                  child: _buildSourceCard(source),
                                );
                              }).toList() + [
                                // Extra details field for "other"
                                if (_selectedSource == ReferralSource.other) ...[
                                  //SizedBox(height: 16),
                                  Container(
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(16),
                                      border: Border.all(color: Colors.grey[300]!),
                                    ),
                                    child: TextField(
                                      controller: _detailsController,
                                      decoration: InputDecoration(
                                        hintText: 'Írd le részletesebben...',
                                        border: InputBorder.none,
                                        contentPadding: EdgeInsets.all(20),
                                      ),
                                      maxLines: 3,
                                      onChanged: (value) {
                                        _otherDetails = value.trim().isEmpty ? null : value.trim();
                                      },
                                    ),
                                  ),
                                ],
                              ],
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
                                  onPressed: _isLoading ? null : _continueToBasicSetup,
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
                                              'Folytatás',
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
                              
                              // Skip option
                              SizedBox(height: 16),
                              TextButton(
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    PageRouteBuilder(
                                      pageBuilder: (context, animation, secondaryAnimation) => BasicSetupScreen(
                                        userType: widget.userType,
                                        referralSource: null,
                                        referralDetails: null,
                                      ),
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
                                },
                                child: Text(
                                  'Kihagyás',
                                  style: TextStyle(
                                    color: Colors.grey[600],
                                    fontSize: 16,
                                  ),
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

  Widget _buildSourceCard(ReferralSource source) {
    final isSelected = _selectedSource == source;
    
    return GestureDetector(
      onTap: () => _selectSource(source),
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
                    source.displayName,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: isSelected ? Color(0xFF00D4A3) : Colors.black87,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    source.description,
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