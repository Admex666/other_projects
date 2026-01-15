import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/story_engine.dart'; // Kept if needed by other parts, though likely unused in main now
import 'services/geolixo_service.dart';
import 'services/notification_service.dart';
import 'services/auth_service.dart';
import 'screens/class_selection_screen.dart'; 
import 'screens/explore_screen.dart';
import 'screens/login_screen.dart';
import 'screens/character_screen.dart';
import 'screens/character_selection_screen.dart'; // New Import

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Notifications
  final notificationService = NotificationService();
  await notificationService.init();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => GeolixoService()),
        ChangeNotifierProvider(create: (_) => AuthService()),
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
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final auth = context.read<AuthService>();
    await auth.tryAutoLogin();
    // Also try to restore character if possible?
    if (auth.isAuthenticated && auth.token != null) {
       // We could try to auto-fetch characters here, but SelectionScreen handles it.
       // However, if we want to "resume" last active character, we'd need that stored in SharedPreferences.
       // For now, defaulting to Selection Screen is safer.
    }
    
    if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    // Watch AuthService for changes to update UI automatically
    final isLoggedIn = context.select<AuthService, bool>((a) => a.isAuthenticated);
    // Watch Active Character
    final hasActiveChar = context.select<GeolixoService, bool>((s) => s.activeCharacter != null);

    if (_isLoading) {
      return const MaterialApp(
        home: Scaffold(
          backgroundColor: GeolixoTheme.background,
          body: Center(child: CircularProgressIndicator(color: GeolixoTheme.accent)),
        ),
      );
    }

    return MaterialApp(
      title: 'Geolixo',
      theme: GeolixoTheme.darkTheme,
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
  
  static final List<Widget> _screens = <Widget>[
    const ExploreScreen(), // Map with Fog of War
    const CharacterScreen(),
    const Center(child: Text('Social / Chat Placeholder', style: TextStyle(color: Colors.white))),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true, 
      appBar: AppBar(
        title: const Text("Geolixo"),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
            IconButton(
                icon: const Icon(Icons.logout, color: Colors.white54),
                onPressed: () {
                    // This will trigger notifyListeners -> MainApp rebuilds -> LoginScreen
                     // Also clear active character to prevent state leak
                    context.read<GeolixoService>().clearActiveCharacter();
                    context.read<AuthService>().logout(); 
                },
            )
        ],
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: _onItemTapped,
        backgroundColor: Colors.grey[900],
        indicatorColor: GeolixoTheme.accent.withOpacity(0.2),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.map_outlined, color: Colors.white54),
            selectedIcon: Icon(Icons.map, color: GeolixoTheme.accent),
            label: 'Felfedezés',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline, color: Colors.white54),
            selectedIcon: Icon(Icons.person, color: GeolixoTheme.accent),
            label: 'Karakter',
          ),
           NavigationDestination(
            icon: Icon(Icons.group_outlined, color: Colors.white54),
            selectedIcon: Icon(Icons.group, color: GeolixoTheme.accent),
            label: 'Közösség',
          ),
        ],
      ),
    );
  }
}
