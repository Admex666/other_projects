import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/story_engine.dart';
import 'services/keldor_service.dart';
import 'services/notification_service.dart';
import 'services/auth_service.dart';
import 'screens/class_selection_screen.dart'; 
import 'screens/explore_screen.dart';
import 'screens/login_screen.dart';
import 'screens/character_screen.dart';
import 'screens/character_selection_screen.dart';
import 'services/api_service.dart';
import 'services/settings_service.dart';
import 'services/location_service.dart';
import 'models/keldor_models.dart';
import 'screens/shop_screen.dart';
import 'screens/collection_screen.dart';
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
    const ShopScreen(),
    const CollectionScreen(),
    const SettingsScreen(),
  ];

  @override
  void initState() {
    super.initState();
    context.read<LocationService>().addListener(_onStepUpdate);
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkTutorial());
  }

  Future<void> _checkTutorial() async {
      // Small delay to ensure location is ready or at least attempted
      await Future.delayed(const Duration(seconds: 2));
      if (!mounted) return;


      final locService = context.read<LocationService>();
      LatLng? location;
      
      try {
        location = await locService.getCurrentLocation();
      } catch (e) {
        print("Tutorial check failed - Location error: $e");
        // Fallback to last known position if available
        location = locService.lastPosition;
      }
      
      if (location != null) {
          final auth = context.read<AuthService>();
          final keldor = context.read<KeldorService>();
          
          if (auth.token != null) {
              bool started = await keldor.checkAndStartTutorial(auth.token!, location);
              if (started && mounted) {
                  _showTutorialDialog();
              }
          }
      }
  }

  void _showTutorialDialog() {
      showDialog(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => AlertDialog(
              backgroundColor: Colors.black87,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: KeldorTheme.primary, width: 2)
              ),
              title: Row(children: const [
                  Icon(Icons.warning_amber_rounded, color: KeldorTheme.primary),
                  SizedBox(width: 8),
                  Text("BEJÖVŐ ADÁS", style: TextStyle(color: KeldorTheme.primary, fontWeight: FontWeight.bold))
              ]),
              content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                      Text("Ügynök! A rendszerünk sikeresen aktivált téged.", style: TextStyle(color: Colors.white)),
                      SizedBox(height: 12),
                      Text("A szkennered egy alacsony szintű anomáliát észlelt a közvetlen közeledben.", style: TextStyle(color: Colors.white70)),
                      SizedBox(height: 12),
                      Text("Ez a vizsgamunkád. Menj oda, és semlegesítsd!", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  ],
              ),
              actions: [
                  TextButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      child: const Text("VETTEM", style: TextStyle(color: KeldorTheme.primary, fontWeight: FontWeight.bold, fontSize: 16))
                  )
              ],
          )
      );
  }

  @override
  void dispose() {
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
              }).catchError((e) {
                  print("❌ Step sync failed: $e");
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
      appBar: _selectedIndex == 4 ? null : AppBar( // Hide AppBar on Settings (index 4)
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
            icon: Icon(Icons.storefront_outlined, color: Colors.white54),
            selectedIcon: Icon(Icons.storefront, color: KeldorTheme.primary),
            label: 'Bolt',
          ),
           NavigationDestination(
            icon: Icon(Icons.auto_stories_outlined, color: Colors.white54),
            selectedIcon: Icon(Icons.auto_stories, color: KeldorTheme.primary),
            label: 'Gyűjtemény',
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
