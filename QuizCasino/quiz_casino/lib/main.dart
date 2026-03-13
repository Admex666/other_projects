import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/audio_manager.dart';
import 'core/game_manager.dart';
import 'theme.dart';
import 'ui/main_shell.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AudioManager().init();
  runApp(const QuizCasinoApp());
}

class QuizCasinoApp extends StatelessWidget {
  const QuizCasinoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => GameManager()),
      ],
      child: MaterialApp(
        title: 'KnowCoin',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.themeData,
        home: const MainShell(),
      ),
    );
  }
}
