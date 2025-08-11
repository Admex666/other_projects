import 'package:flutter/material.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:frontend/screens/dashboard_screen.dart';
import 'package:frontend/screens/partnerships_screen.dart';
import 'package:frontend/screens/profile/profile_screen.dart';
import 'package:frontend/screens/manage_accounts_screen.dart'; 
import 'package:frontend/screens/manage_categories_screen.dart';
import 'package:frontend/screens/knowledge/knowledge_screen.dart';
import 'package:frontend/screens/analysis_screen.dart';
import 'package:frontend/screens/forum/forum_main_screen.dart';
import 'package:frontend/widgets/notification_badge.dart';
import 'package:frontend/screens/manage_limits_screen.dart';
import 'package:frontend/screens/challenges/challenges_main_screen.dart';
import 'package:frontend/screens/habits/habits_main_screen.dart';
import 'package:frontend/screens/pti/pti_main_screen.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:provider/provider.dart';
import 'package:frontend/providers/subscription_provider.dart';
import 'package:frontend/services/subscription_service.dart';
import 'package:frontend/screens/subscription/subscription_screen.dart';
import 'package:frontend/screens/subscription/plans_screen.dart';
import 'package:frontend/providers/accountability_provider.dart';
import 'package:frontend/services/accountability_service.dart';

void main() {
  runApp(NestCashApp());
}

class NestCashApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // AuthService - singleton
        Provider<AuthService>(
          create: (_) => AuthService(),
        ),
        
        // SubscriptionService - depends on AuthService
        ProxyProvider<AuthService, SubscriptionService>(
          create: (context) => SubscriptionService(
            authService: context.read<AuthService>(),
          ),
          update: (context, auth, previous) => SubscriptionService(
            authService: auth,
          ),
        ),
        
        // SubscriptionProvider - depends on SubscriptionService
        ChangeNotifierProxyProvider<SubscriptionService, SubscriptionProvider>(
          create: (context) => SubscriptionProvider(
            subscriptionService: context.read<SubscriptionService>(),
          ),
          update: (context, subscriptionService, previous) => 
            previous ?? SubscriptionProvider(
              subscriptionService: subscriptionService,
            ),
        ),

        // ÚJ: AccountabilityProvider hozzáadása
        ChangeNotifierProxyProvider<AuthService, AccountabilityProvider>(
          create: (context) => AccountabilityProvider(
            service: AccountabilityService(),
          ),
          update: (context, authService, previous) => 
            previous ?? AccountabilityProvider(
              service: AccountabilityService(),
            ),
        ),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'NestCash',
        theme: ThemeData(primarySwatch: Colors.teal),
        home: AuthWrapper(),
        routes: {
          '/subscription': (context) => const SubscriptionScreen(),
          '/plans': (context) => PlansScreen(
            currentTier: context.read<SubscriptionProvider>().currentTier,
          ),
        },
      ),
    );
  }
}

// Global navigation
class MainScreen extends StatefulWidget {
  final String userId;
  final String? username;
  
  const MainScreen({required this.userId, this.username});

  @override
  _MainScreenState createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;
  String _currentUsername = 'User'; // Alapértelmezett érték
  final AuthService _authService = AuthService(); // AuthService hozzáadása

  late final List<Widget> _widgetOptions;

  @override
  void initState() {
    super.initState();
    _loadUsername();
    
    // Subscription data betöltése a bejelentkezés után
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SubscriptionProvider>().loadSubscriptionInfo();
    });
    
    _widgetOptions = <Widget>[
      DashboardScreen(username: _currentUsername, userId: widget.userId,),
      AnalysisScreen(userId: widget.userId),
      const SizedBox.shrink(),
      const SizedBox.shrink(),
      ProfileScreen(username: _currentUsername, userId: widget.userId),
    ];
  }

  Future<void> _loadUsername() async {
    try {
      final username = widget.username ?? await _authService.getCurrentUsername();
      if (username != null && mounted) {
        setState(() {
          _currentUsername = username;
          // Widget options újraépítése az új username-mel
          _widgetOptions[0] = DashboardScreen(username: _currentUsername, userId: widget.userId);
          _widgetOptions[4] = ProfileScreen(username: _currentUsername, userId: widget.userId);
        });
      }
    } catch (e) {
      print('Error loading username: $e');
    }
  }

  void _onItemTapped(int index) {
    if (index == 2) {
      _showAddTransactionOptions(context);
    } else if (index == 3) {
      _showForumChallengesOptions(context);
    } else {
      setState(() {
        _selectedIndex = index;
      });
    }
  }

  bool _shouldShowAppBar() {
    // Ne jelenjen meg AppBar az AnalysisScreen (index 1) és a középső opció (index 2) esetében
    return _selectedIndex != 1 && _selectedIndex != 2;
  }

  // Módosítsd a _showAddTransactionOptions metódust a main.dart fájlban
void _showAddTransactionOptions(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (BuildContext bc) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            // Számlák kezelése gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ManageAccountsScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.account_balance_wallet, color: Colors.white),
                label: const Text(
                  'Számlák',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Kategóriák kezelése gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ManageCategoriesScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.category, color: Colors.white),
                label: const Text(
                  'Kategóriák',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purpleAccent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Limitek kezelése gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ManageLimitsScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.speed, color: Colors.white),
                label: const Text(
                  'Limitek',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
          ],
        ),
      );
    },
  );
}

void _showForumChallengesOptions(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (BuildContext bc) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            // PTI gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PTIMainScreen(
                        userId: widget.userId,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.trending_up, color: Colors.white),
                label: const Text(
                  'PTI - Pénzügyi Tudatosság Index',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6C63FF),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Szokások gomb (ide helyezzük át)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => HabitsMainScreen(
                        userId: widget.userId,
                        username: _currentUsername,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.psychology, color: Colors.white),
                label: const Text(
                  'Szokások',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.teal,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Partner gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => PartnershipsScreen(),
                    ),
                  );
                },
                icon: const Icon(Icons.people_alt_outlined, color: Colors.white),
                label: const Text(
                  'Accountability Partner',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color.fromARGB(255, 212, 60, 0),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Fórum gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ForumMainScreen(
                        userId: widget.userId,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.forum, color: Colors.white),
                label: const Text(
                  'Fórum',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00D4A3),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Kihívások gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ChallengesMainScreen(
                        userId: widget.userId,
                        username: _currentUsername,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.emoji_events, color: Colors.white),
                label: const Text(
                  'Kihívások',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Tudástár gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => KnowledgeScreen(
                        userId: widget.userId,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.school_outlined, color: Colors.white),
                label: const Text(
                  'Tudástár',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepOrange,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
          ],
        ),
      );
    },
  );
}

@override
Widget build(BuildContext context) {
  return Scaffold(
    appBar: _shouldShowAppBar() ? AppBar(
      backgroundColor: const Color(0xFF00D4A3),
      elevation: 0,
      automaticallyImplyLeading: false,
      title: Text(
        _getScreenTitle(_selectedIndex),
        style: const TextStyle(
          color: Colors.black,
          fontWeight: FontWeight.bold,
        ),
      ),
      actions: [
        AppBarNotificationBadge(userId: widget.userId),
      ],
    ) : null,
    body: _widgetOptions.elementAt(_selectedIndex),
      bottomNavigationBar: Container(
        padding: EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: Color(0xFFF0F8F0),
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _buildNavItem(Icons.home_outlined, 0),
            _buildNavItem(Icons.bar_chart_outlined, 1),
            _buildNavItem(Icons.swap_horiz_outlined, 2),
            _buildNavItem(Icons.mood_outlined, 3),
            _buildNavItem(Icons.person_outline, 4),
          ],
        ),
      ),
    );
  }

  // Helper method hozzáadása a screen címekhez:
String _getScreenTitle(int index) {
    switch (index) {
      case 0:
        return 'Üdv újra, $_currentUsername!';
      case 1:
        return 'Elemzések';
      case 3:
        return 'Fórum';
      case 4:
        return 'Profil';
      default:
        return 'NestCash';
    }
  }

  Widget _buildNavItem(IconData icon, int index) {
    bool isSelected = index == _selectedIndex;
    return GestureDetector(
      onTap: () => _onItemTapped(index),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected && index != 2 ? const Color(0xFF00D4A3) : Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: isSelected && index != 2 ? Colors.white : Colors.grey[600],
          size: 26,
        ),
      ),
    );
  }
}