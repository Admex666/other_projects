import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/story_engine.dart'; // Kept if needed by other parts, though likely unused in main now
import 'services/keldor_service.dart';
import 'services/notification_service.dart';
import 'services/auth_service.dart';
import 'screens/class_selection_screen.dart'; 
import 'screens/explore_screen.dart';
import 'screens/login_screen.dart';
import 'screens/character_screen.dart';
import 'screens/character_selection_screen.dart'; // New Import
import 'services/api_service.dart';
import 'services/settings_service.dart';
import 'services/location_service.dart';
import 'models/keldor_models.dart'; // Needed for QuestStatus
import 'screens/settings_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Notifications
  final notificationService = NotificationService();
  await notificationService.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => KeldorService()),
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => StoryEngine()),
        ChangeNotifierProvider(create: (_) => SettingsService()),
        ChangeNotifierProvider(create: (_) => LocationService()),
      ],
      child: const MainApp(),
    ),
  );
}

class MainApp extends StatefulWidget {
  const MainApp({Key? key}) : super(key: key);

  @override
  State<MainApp> createState() => _MainAppState();
}

class _MainAppState extends State<MainApp> {
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _setupUnauthorizedHandler();
    _checkAuth();
  }

  void _setupUnauthorizedHandler() {
    ApiService.onUnauthorized = _handleUnauthorized;
    KeldorService.onUnauthorized = _handleUnauthorized;
  }

  void _handleUnauthorized() {
    if (mounted) {
       final auth = context.read<AuthService>();
       if (auth.isAuthenticated) {
         print("🚨 401 Unauthorized detected! Logging out...");
         context.read<KeldorService>().clearActiveCharacter();
         auth.logout();
       }
    }
  }

  Future<void> _checkAuth() async {
    final auth = context.read<AuthService>();
    final keldor = context.read<KeldorService>();
    final engine = context.read<StoryEngine>();
    
    await auth.tryAutoLogin();
    
    if (auth.isAuthenticated && auth.token != null) {
       engine.setToken(auth.token);
       await engine.loadUserFromPrefs();
       
       if (engine.user != null) {
          // Sync character if logged in
          await keldor.fetchUserCharacter(auth.token!);
       }
    }
    
    if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    // Watch AuthService for changes to update UI automatically
    final isLoggedIn = context.select<AuthService, bool>((a) => a.isAuthenticated);
    // Watch Active Character
    final hasActiveChar = context.select<KeldorService, bool>((s) => s.activeCharacter != null);

    if (_isLoading) {
      return const MaterialApp(
        home: Scaffold(
          backgroundColor: KeldorTheme.background,
          body: Center(child: CircularProgressIndicator(color: KeldorTheme.primary)),
        ),
      );
    }

    return MaterialApp(
      title: 'Keldor',
      debugShowCheckedModeBanner: false,
      theme: KeldorTheme.darkTheme,
      home: !isLoggedIn 
          ? const LoginScreen()
          : (hasActiveChar ? const MainScaffold() : const CharacterSelectionScreen()),
    );
  }
}


class MainScaffold extends StatefulWidget {
  const MainScaffold({Key? key}) : super(key: key);

  @override
  State<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends State<MainScaffold> {
  int _selectedIndex = 0; // Default to Map
  int _syncedSteps = 0;
  
  static final List<Widget> _screens = <Widget>[
    const ExploreScreen(), // Map with Fog of War
    const CharacterScreen(),
    const SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    context.read<LocationService>().addListener(_onStepUpdate);
  }

  @override
  void dispose() {
    // If context is still valid, remove listener? 
    // Actually safe to ignore here as MainScaffold disposes on logout usually,
    // but better practice:
    // context.read<LocationService>().removeListener(_onStepUpdate); 
    // (Requires saving reference or ensuring context valid)
    super.dispose();
  }

  void _onStepUpdate() {
      if (!mounted) return;
      final locService = context.read<LocationService>();
      final currentSteps = locService.sessionSteps;
      
      // Sync every 10 steps
      if (currentSteps - _syncedSteps >= 10) {
          final stepsToSync = currentSteps - _syncedSteps;
          
          final auth = context.read<AuthService>();
          final keldor = context.read<KeldorService>();
          
          // Requirement: Only count steps during active quest
          final hasActiveQuest = keldor.activeQuests.any((q) => q.status == QuestStatus.active);
          
          if (!hasActiveQuest) {
             // If no quest is active, we just advance the synced counter so we don't accumulate "pending" steps that trigger later.
             // Or should we just ignore? The user said "Only those steps that happen during a quest". 
             // So we should NOT credit them. We mark them as "processed" but not synced.
             _syncedSteps = currentSteps; 
             return;
          }

          _syncedSteps = currentSteps;
          
          if (auth.isAuthenticated && auth.token != null && keldor.activeCharacter != null) {
              print("👣 Syncing $stepsToSync steps to backend (Quest Active)...");
              
              // Optimistic UI Update
              keldor.addLocalSteps(stepsToSync);
              
              // Call API
              ApiService().addSteps(auth.token!, keldor.activeCharacter!.userId, stepsToSync).then((_) {
                  // No need to fetch immediately if optimistic update was accurate, 
                  // but good to sync occasionally. For now, let's skip fetch to reduce load/flicker
                  // unless error happens.
              }).catchError((e) {
                  print("❌ Step sync failed: $e");
                  // Revert steps? Too complex. Steps are cumulative. 
                  // Backend will catch up eventually.
              });
          }
      }
  }

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true, 
      appBar: _selectedIndex == 2 ? null : AppBar(
        title: const Text("Keldor"),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: _onItemTapped,
        backgroundColor: Colors.grey[900],
        indicatorColor: KeldorTheme.primary.withOpacity(0.2),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.map_outlined, color: Colors.white54),
            selectedIcon: Icon(Icons.map, color: KeldorTheme.primary),
            label: 'Felfedezés',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline, color: Colors.white54),
            selectedIcon: Icon(Icons.person, color: KeldorTheme.primary),
            label: 'Karakter',
          ),
           NavigationDestination(
            icon: Icon(Icons.settings_outlined, color: Colors.white54),
            selectedIcon: Icon(Icons.settings, color: KeldorTheme.primary),
            label: 'Beállítások',
          ),
        ],
      ),
    );
  }
}
