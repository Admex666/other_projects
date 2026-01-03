
import 'package:flutter/material.dart';
import 'dart:async';
import 'game_screen.dart';

class IntroScreen extends StatefulWidget {
  final String storyId;
  const IntroScreen({super.key, required this.storyId});

  @override
  State<IntroScreen> createState() => _IntroScreenState();
}

class _IntroScreenState extends State<IntroScreen> {
  int _step = 0;
  List<String> _texts = [
    "Budapest, 2026.",
    "A Várost ellepte a Bíbor Köd.",
    "Az emberek vakok rá. Csak mi, a Vándorok látjuk az Igazságot.",
    "A Mentorod eltűnt. Te maradtál az utolsó remény."
  ];

  void _next() {
    if (_step < _texts.length - 1) {
      setState(() => _step++);
    } else {
      Navigator.pushReplacement(
        context, 
        MaterialPageRoute(builder: (_) => GameScreen(storyId: widget.storyId))
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          Image.asset("assets/mist_city_intro.png", fit: BoxFit.cover),
          Container(color: Colors.black.withOpacity(0.6)), // Dim overlay
          
          SafeArea(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedSwitcher(
                  duration: const Duration(seconds: 1),
                  child: Padding(
                    key: ValueKey(_step),
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      _texts[_step],
                      style: const TextStyle(
                        fontFamily: 'Courier', 
                        fontSize: 24, 
                        color: Colors.white, 
                        fontWeight: FontWeight.bold,
                        shadows: [Shadow(blurRadius: 10, color: Colors.purple)]
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
                const SizedBox(height: 50),
                TextButton(
                  onPressed: _next,
                  child: const Text("TOVÁBB >>", style: TextStyle(color: Colors.white54)),
                )
              ],
            ),
          ),
          Positioned(
            top: 40,
            right: 20,
            child: IconButton(
              icon: const Icon(Icons.close, color: Colors.white54),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
        ],
      ),
    );
  }
}
