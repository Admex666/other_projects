import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:frontend/screens/dashboard_screen.dart';
import 'package:frontend/screens/accountability/partnerships_screen.dart';
import 'package:frontend/screens/profile/profile_screen.dart';
import 'package:frontend/screens/manage_accounts_screen.dart'; 
import 'package:frontend/screens/manage_categories_screen.dart';
import 'package:frontend/screens/knowledge/knowledge_screen.dart';
import 'package:frontend/screens/analysis_screen.dart';
import 'package:frontend/screens/forum/forum_main_screen.dart';
import 'package:frontend/widgets/notification_badge.dart';
import 'package:frontend/screens/limits/manage_limits_screen.dart';
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
import 'package:frontend/screens/accountability/accountability_setup_screen.dart';
import 'package:frontend/screens/admin_dashboard_screen.dart';
import 'package:frontend/services/analytics_service.dart';
import 'package:frontend/services/language_service.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/add_incomes_screen.dart';
// Firebase
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'firebase_options.dart'; // Ez a flutterfire configure után generálódik
import 'package:frontend/services/nestcash_analytics_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  // Flutter framework hibák küldése Crashlytics-be
  FlutterError.onError = (errorDetails) {
    FirebaseCrashlytics.instance.recordFlutterFatalError(errorDetails);
  };
  
  // Platform hibák kezelése (iOS/Android natív hibák)
  PlatformDispatcher.instance.onError = (error, stack) {
    FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
    return true;
  };

  await EasyLocalization.ensureInitialized();

  runApp(
    EasyLocalization(
      supportedLocales: LanguageService.supportedLocales,
      path: 'assets/translations',
      fallbackLocale: const Locale('hu', 'HU'),
      child: NestCashApp(),
    ),
  );
}

class NestCashApp extends StatelessWidget {
  static FirebaseAnalytics analytics = FirebaseAnalytics.instance;
  static FirebaseAnalyticsObserver observer = FirebaseAnalyticsObserver(analytics: analytics);

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
    
        // AccountabilityProvider
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
      child: Builder(
        builder: (context) => MaterialApp(
          navigatorObservers: [observer],
          navigatorKey: LanguageService.navigatorKey,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          locale: context.locale,
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
  String _currentUsername = 'User';
  final AuthService _authService = AuthService();

  late final List<Widget> _widgetOptions;

  @override
  void initState() {
    super.initState();
    _loadUsername();
    
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await NestCashAnalyticsService.initializeUser(
        userId: widget.userId,
        username: widget.username,
        subscriptionTier: 'free', // TODO: dynamic subscription tier
      );
      
      await NestCashAnalyticsService.trackScreenView('main_screen');

      context.read<SubscriptionProvider>().loadSubscriptionInfo();

      _logScreenView();
      _setFirebaseUserProperties();
      
      try {
        final analyticsService = AnalyticsService();
        analyticsService.trackSession();
      } catch (e) {
        print('Session tracking failed on screen init: $e');
      }

      try {
        final analyticsService = AnalyticsService();
        analyticsService.trackSession();
      } catch (e) {
        await NestCashAnalyticsService.trackError(
          error: e,
          context: 'session_tracking_failed',
          screenName: 'main_screen',
        );
      }
    });
    
    // Egyszerűsített widget opciók (csak 3 screen)
    _widgetOptions = <Widget>[
      DashboardScreen(username: _currentUsername, userId: widget.userId,),
      const SizedBox.shrink(), // Add transaction placeholder
      ProfileScreen(username: _currentUsername, userId: widget.userId),
    ];
  }

  Future<void> _logScreenView() async {
    await FirebaseAnalytics.instance.logScreenView(
      screenName: 'main_screen',
      screenClass: 'MainScreen',
    );
  }

  Future<void> _setFirebaseUserProperties() async {
    // Felhasználó azonosító beállítása Analytics-ben
    await FirebaseAnalytics.instance.setUserId(id: widget.userId);
    
    // Crashlytics felhasználó azonosító
    await FirebaseCrashlytics.instance.setUserIdentifier(widget.userId);
    
    // Custom user properties
    await FirebaseAnalytics.instance.setUserProperty(
      name: 'username',
      value: _currentUsername,
    );
    
    // Crashlytics custom keys
    await FirebaseCrashlytics.instance.setCustomKey('username', _currentUsername);
    await FirebaseCrashlytics.instance.setCustomKey('user_id', widget.userId);
  }

  Future<void> _loadUsername() async {
    try {
      final username = widget.username ?? await _authService.getCurrentUsername();
      if (username != null && mounted) {
        setState(() {
          _currentUsername = username;
          // Widget options újraépítése az új username-mel
          _widgetOptions[0] = DashboardScreen(username: _currentUsername, userId: widget.userId);
          _widgetOptions[2] = ProfileScreen(username: _currentUsername, userId: widget.userId);
        });
        await _setFirebaseUserProperties();
      }
    } catch (e) {
      print('Error loading username: $e');
      FirebaseCrashlytics.instance.recordError(
        e,
        StackTrace.current,
        fatal: false,
        reason: 'Error loading username in MainScreen',
      );
    }
  }

  void _onItemTapped(int index) async {
    final fromScreen = _selectedIndex == 0 ? 'dashboard' : 'profile';

    if (index == 1) {
      await NestCashAnalyticsService.trackButtonPress(
        'add_transaction_fab',
        screenName: fromScreen,
      );
      _showAddTransactionOptions(context);
    } else {
      final toScreen = index == 0 ? 'dashboard' : 'profile';
      
      await NestCashAnalyticsService.trackNavigation(
        fromScreen: fromScreen,
        toScreen: toScreen,
        method: 'bottom_navigation',
      );
      
      setState(() {
        _selectedIndex = index;
      });

      await NestCashAnalyticsService.trackScreenView(toScreen);
    }
  }

  // Drawer builder metódus
  Widget _buildDrawer() {
    return Drawer(
      child: Column(
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(
              color: Color(0xFF00D4A3),
            ),
            child: SizedBox(
              width: double.infinity,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  const CircleAvatar(
                    radius: 30,
                    backgroundColor: Colors.white,
                    child: Icon(
                      Icons.person,
                      size: 30,
                      color: Color(0xFF00D4A3),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    _currentUsername,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 15),
                ],
              ),
            ),
          ),
          
          // Drawer menü items
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                // PÉNZÜGYEK SZEKCIÓ
                _buildSectionHeader('finances'.tr()),
                _buildDrawerItem(
                  icon: Icons.bar_chart,
                  title: 'analyses'.tr(),
                  color: Colors.blue,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => AnalysisScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.account_balance_wallet,
                  title: 'accounts'.tr(),
                  color: Colors.blueAccent,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ManageAccountsScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.category,
                  title: 'categories'.tr(),
                  color: Colors.purpleAccent,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ManageCategoriesScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.speed,
                  title: 'limits'.tr(),
                  color: Colors.orange,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ManageLimitsScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                
                const SizedBox(height: 10),
                
                // FEJLŐDÉS SZEKCIÓ
                _buildSectionHeader('development'.tr()),
                _buildDrawerItem(
                  icon: Icons.trending_up,
                  title: 'pti_full'.tr(),
                  color: const Color(0xFF6C63FF),
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PTIMainScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.psychology,
                  title: 'habits_'.tr(),
                  color: Colors.teal,
                  onTap: () {
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
                ),
                _buildDrawerItem(
                  icon: Icons.school_outlined,
                  title: 'knowledge_base'.tr(),
                  color: Colors.deepOrange,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => KnowledgeScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                
                const SizedBox(height: 10),
                
                // KÖZÖSSÉG SZEKCIÓ
                _buildSectionHeader('community'.tr()),
                _buildDrawerItem(
                  icon: Icons.people_alt_outlined,
                  title: 'accountability_partner'.tr(),
                  color: const Color.fromARGB(255, 212, 60, 0),
                  onTap: () async {
                    Navigator.pop(context);
                    
                    final provider = Provider.of<AccountabilityProvider>(context, listen: false);
                    await provider.loadProfile();
                    
                    if (provider.hasProfile) {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => PartnershipsScreen(),
                        ),
                      );
                    } else {
                      final result = await Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => AccountabilitySetupScreen(),
                        ),
                      );
                      
                      if (result == true) {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => PartnershipsScreen(),
                          ),
                        );
                      }
                    }
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.forum,
                  title: 'forum'.tr(),
                  color: const Color(0xFF00D4A3),
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ForumMainScreen(userId: widget.userId),
                      ),
                    );
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.emoji_events,
                  title: 'challenges'.tr(),
                  color: Colors.deepPurple,
                  onTap: () {
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
                ),
                
                // ADMIN SZEKCIÓ (ha szükséges)
                if (_currentUsername == 'admin') ...[
                  const SizedBox(height: 10),
                  _buildSectionHeader('admin'.tr()),
                  _buildDrawerItem(
                    icon: Icons.admin_panel_settings,
                    title: 'admin_dashboard'.tr(),
                    color: Colors.red[600]!,
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => AdminDashboardScreen(),
                        ),
                      );
                    },
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  // Helper metódusok a drawer-hez
  Widget _buildSectionHeader(String title) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: Colors.grey[600],
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildDrawerItem({
    required IconData icon,
    required String title,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        title: Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.w500,
            fontSize: 14,
          ),
        ),
        onTap: onTap,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }

  // MÓDOSÍTOTT: _shouldShowAppBar metódus
  bool _shouldShowAppBar() {
    return true; // Most minden screen-en megjelenjen az AppBar
  }

void _showAddTransactionOptions(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (BuildContext bc) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: const BoxDecoration(
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
              'quick_add'.tr(),
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => AddIncomesScreen(userId: widget.userId),
                        ),
                      );
                    },
                    icon: const Icon(Icons.add, color: Colors.white),
                    label: Text('income'.tr(), style: const TextStyle(color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00D4A3),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => AddExpensesScreen(userId: widget.userId),
                        ),
                      );
                    },
                    icon: const Icon(Icons.remove, color: Colors.white),
                    label: Text('expense'.tr(), style: const TextStyle(color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.redAccent,
                      padding: const EdgeInsets.symmetric(vertical: 16),
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

@override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: _buildDrawer(),
      appBar: _shouldShowAppBar() ? AppBar(
        backgroundColor: const Color(0xFF00D4A3),
        elevation: 0,
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
      // MÓDOSÍTOTT: BottomNavigationBar
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: const BoxDecoration(
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
            _buildNavItem(Icons.add_circle_outline, 1),
            _buildNavItem(Icons.person_outline, 2),
          ],
        ),
      ),
    );
  }

  // Helper method hozzáadása a screen címekhez:
String _getScreenTitle(int index) {
    switch (index) {
      case 0:
        return 'welcome_back'.tr(namedArgs: {'username': _currentUsername});
      case 2:
        return 'profile'.tr();
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
          color: isSelected && index != 1 ? const Color(0xFF00D4A3) : Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: isSelected && index != 1 ? Colors.white : Colors.grey[600],
          size: 26,
        ),
      ),
    );
  }
}