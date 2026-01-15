import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/story_engine.dart';
import 'services/geolixo_service.dart'; // Import service
import 'services/notification_service.dart'; // Import Notifications
import 'screens/class_selection_screen.dart';
import 'screens/explore_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final engine = StoryEngine();
  final geolixoService = GeolixoService(); // Init service
  final notificationService = NotificationService();
  await notificationService.init(); // Init notifications
  await engine.loadUserFromPrefs();
  
  runApp(
    MultiProvider( // Use MultiProvider
      providers: [
        ChangeNotifierProvider.value(value: engine),
        ChangeNotifierProvider.value(value: geolixoService),
      ],
      child: const StoryTurakApp(),
    ),
  );
}

class StoryTurakApp extends StatelessWidget {
  const StoryTurakApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Geolixo',
      debugShowCheckedModeBanner: false,
      theme: GeolixoTheme.darkTheme,
      initialRoute: '/',
      routes: {
        '/': (context) => const ClassSelectionScreen(),
        '/map': (context) => const ExploreScreen(),
      },
    );
  }
}
