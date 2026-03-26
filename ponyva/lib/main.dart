import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme.dart';
import 'presentation/screens/main_menu_screen.dart';

void main() {
  runApp(
    const ProviderScope(
      child: PaprikaStormApp(),
    ),
  );
}

class PaprikaStormApp extends StatelessWidget {
  const PaprikaStormApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Paprika Storm',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const MainMenuScreen(),
    );
  }
}
