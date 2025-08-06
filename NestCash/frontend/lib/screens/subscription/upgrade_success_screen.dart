// lib/screens/subscription/upgrade_success_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/subscription.dart';
import '../../providers/subscription_provider.dart';
import '../../widgets/subscription/tier_badge.dart';
import '../../utils/subscription_utils.dart';
import 'subscription_screen.dart';

class UpgradeSuccessScreen extends StatefulWidget {
  final SubscriptionTier newTier;

  const UpgradeSuccessScreen({
    super.key,
    required this.newTier,
  });

  @override
  State<UpgradeSuccessScreen> createState() => _UpgradeSuccessScreenState();
}

class _UpgradeSuccessScreenState extends State<UpgradeSuccessScreen>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late AnimationController _confettiController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    
    _confettiController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.elasticOut,
    ));

    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: const Interval(0.3, 1.0, curve: Curves.easeInOut),
    ));

    // Start animations
    _animationController.forward();
    _confettiController.forward();

    // Refresh subscription data
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SubscriptionProvider>().loadSubscriptionInfo(forceRefresh: true);
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    _confettiController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tierColor = SubscriptionUtils.getTierColor(widget.newTier);

    return Scaffold(
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  tierColor.withOpacity(0.1),
                  Colors.white,
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
          
          // Confetti animation
          AnimatedBuilder(
            animation: _confettiController,
            builder: (context, child) {
              return CustomPaint(
                painter: ConfettiPainter(_confettiController.value),
                size: MediaQuery.of(context).size,
              );
            },
          ),
          
          // Main content
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  // Close button
                  Align(
                    alignment: Alignment.topRight,
                    child: IconButton(
                      onPressed: () => _navigateToHome(context),
                      icon: const Icon(Icons.close),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.white.withOpacity(0.9),
                      ),
                    ),
                  ),
                  
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Success icon with animation
                        ScaleTransition(
                          scale: _scaleAnimation,
                          child: Container(
                            padding: const EdgeInsets.all(24),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: tierColor.withOpacity(0.3),
                                  blurRadius: 20,
                                  offset: const Offset(0, 8),
                                ),
                              ],
                            ),
                            child: Icon(
                              Icons.check_circle,
                              size: 80,
                              color: tierColor,
                            ),
                          ),
                        ),
                        
                        const SizedBox(height: 32),
                        
                        // Success message
                        FadeTransition(
                          opacity: _fadeAnimation,
                          child: Column(
                            children: [
                              Text(
                                'Sikeres frissítés!',
                                style: TextStyle(
                                  fontSize: 28,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.grey[800],
                                ),
                                textAlign: TextAlign.center,
                              ),
                              
                              const SizedBox(height: 16),
                              
                              Text(
                                'Üdvözlünk a ${widget.newTier.displayName} csomagban!',
                                style: TextStyle(
                                  fontSize: 18,
                                  color: Colors.grey[600],
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                        
                        const SizedBox(height: 40),
                        
                        // New tier badge
                        FadeTransition(
                          opacity: _fadeAnimation,
                          child: TierBadge(
                            tier: widget.newTier,
                            showPrice: true,
                            size: 120,
                          ),
                        ),
                        
                        const SizedBox(height: 40),
                        
                        // Features unlocked
                        FadeTransition(
                          opacity: _fadeAnimation,
                          child: SingleChildScrollView(
                            child: _buildUnlockedFeatures(),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  // Action buttons
                  FadeTransition(
                    opacity: _fadeAnimation,
                    child: Column(
                      children: [
                        // Explore features button
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            onPressed: () => _navigateToHome(context),
                            icon: const Icon(Icons.explore),
                            label: const Text(
                              'Funkciók felfedezése',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: tierColor,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),
                        
                        const SizedBox(height: 12),
                        
                        // View subscription details button
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: () => _navigateToSubscriptionScreen(context),
                            icon: const Icon(Icons.settings),
                            label: const Text('Előfizetés kezelése'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: tierColor,
                              side: BorderSide(color: tierColor),
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
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
        ],
      ),
    );
  }

  Widget _buildUnlockedFeatures() {
    final unlockedFeatures = _getUnlockedFeatures(widget.newTier);
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: SubscriptionUtils.getTierColor(widget.newTier).withOpacity(0.2),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Text(
            'Feloldott funkciók:',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 12),
          ...unlockedFeatures.map((feature) => Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              children: [
                Icon(
                  Icons.new_releases,
                  color: SubscriptionUtils.getTierColor(widget.newTier),
                  size: 18,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    feature,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[700],
                    ),
                  ),
                ),
              ],
            ),
          )),
        ],
      ),
    );
  }

  List<String> _getUnlockedFeatures(SubscriptionTier tier) {
    switch (tier) {
      case SubscriptionTier.plus:
        return [
          'Korlátlan kihívások',
          'Korlátlan szokások',
          'Teljes elemzések',
          'Import funkciók',
          'Tömeges szerkesztés',
          'Teljes tudástár',
        ];
      case SubscriptionTier.pro:
        return [
          'Személyre szabott elemzések',
          'Exkluzív tartalmak',
          'Tanulási útvonalak',
          'Exkluzív kihívások',
          'Accountability csoportok',
          'Javaslatok',
        ];
      case SubscriptionTier.free:
        return [];
    }
  }

  void _navigateToHome(BuildContext context) {
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  void _navigateToSubscriptionScreen(BuildContext context) {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => const SubscriptionScreen(),
      ),
    );
  }
}

class ConfettiPainter extends CustomPainter {
  final double animationValue;

  ConfettiPainter(this.animationValue);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;

    final colors = [
      Colors.red,
      Colors.blue,
      Colors.green,
      Colors.yellow,
      Colors.purple,
      Colors.orange,
    ];

    for (int i = 0; i < 50; i++) {
      final color = colors[i % colors.length];
      paint.color = color.withOpacity(0.8);

      // Calculate confetti positions
      final x = (size.width * (i * 0.1) % 1.0);
      final y = size.height * animationValue + (i * 20.0) % size.height - size.height;
      
      // Only draw if within screen bounds
      if (y > -10 && y < size.height + 10) {
        canvas.drawCircle(
          Offset(x, y),
          3.0,
          paint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}