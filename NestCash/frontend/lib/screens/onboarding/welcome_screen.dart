// lib/screens/onboarding/welcome_screen.dart

import 'package:flutter/material.dart';
import 'user_intent_screen.dart';
import '/main.dart';

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({Key? key}) : super(key: key);

  @override
  _WelcomeScreenState createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late AnimationController _slideController;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    
    _fadeController = AnimationController(
      duration: Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _slideController = AnimationController(
      duration: Duration(milliseconds: 1200),
      vsync: this,
    );

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    ));

    _slideAnimation = Tween<Offset>(
      begin: Offset(0, 0.3),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOutBack,
    ));

    // Start animations
    _fadeController.forward();
    Future.delayed(Duration(milliseconds: 300), () {
      _slideController.forward();
    });
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _slideController.dispose();
    super.dispose();
  }

  void _navigateToNextStep() {
    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => UserIntentScreen(),
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
              Color(0xFF4ECDC4),
              Color(0xFFE8F6F3),
            ],
            stops: [0.0, 0.5, 1.0],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 32.0),
            child: Column(
              children: [
                Expanded(
                  flex: 6,
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: SlideTransition(
                      position: _slideAnimation,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Logo/Icon
                          Container(
                            width: 120,
                            height: 120,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.1),
                                  blurRadius: 20,
                                  offset: Offset(0, 10),
                                ),
                              ],
                            ),
                            child: Icon(
                              Icons.account_balance_wallet,
                              size: 60,
                              color: Color(0xFF00D4A3),
                            ),
                          ),
                          
                          SizedBox(height: 40),
                          
                          // Welcome Title
                          Text(
                            'Üdvözlünk a\nNestCash-ben!',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                              height: 1.2,
                            ),
                          ),
                          
                          SizedBox(height: 24),
                          
                          // Subtitle
                          Text(
                            'Az intelligens pénzügyi asszisztensed,\nami segít elérni a céljaidat',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.white.withOpacity(0.9),
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                
                Expanded(
                  flex: 4,
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Features List
                        _buildFeatureItem(
                          icon: Icons.trending_up,
                          text: 'Intelligens költségvetés tervezés',
                        ),
                        SizedBox(height: 16),
                        _buildFeatureItem(
                          icon: Icons.people_outline,
                          text: 'Közösségi tanulás és fejlődés',
                        ),
                        SizedBox(height: 16),
                        _buildFeatureItem(
                          icon: Icons.insights,
                          text: 'Személyre szabott elemzések',
                        ),
                        
                        SizedBox(height: 40),
                        
                        // Get Started Button
                        Container(
                          width: double.infinity,
                          height: 56,
                          child: ElevatedButton(
                            onPressed: _navigateToNextStep,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: Color(0xFF00D4A3),
                              elevation: 8,
                              shadowColor: Colors.black.withOpacity(0.3),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(28),
                              ),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  'Kezdjük el!',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                SizedBox(width: 8),
                                Icon(
                                  Icons.arrow_forward,
                                  size: 20,
                                ),
                              ],
                            ),
                          ),
                        ),
                        
                        SizedBox(height: 20),
                        
                        // Skip option
                        TextButton(
                          onPressed: () {
                            // Skip onboarding és MainScreen-re navigálás
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => MainScreen(
                                  username: 'Guest', // vagy szerezd be az actual username-t
                                  userId: 'guest_id', // vagy actual user ID
                                ),
                              ),
                            );
                          },
                          child: Text(
                            'Kihagyás',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.8),
                              fontSize: 16,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureItem({required IconData icon, required String text}) {
    return Row(
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.2),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Icon(
            icon,
            color: Colors.white,
            size: 20,
          ),
        ),
        SizedBox(width: 16),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 16,
              color: Colors.white.withOpacity(0.9),
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }
}