import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'screens/game_screen.dart';
import 'screens/intro_screen.dart';
import 'screens/lobby_screen.dart';
import 'services/story_engine.dart';


void main() {
  runApp(const StoryTurakApp());
}

class StoryTurakApp extends StatelessWidget {
  const StoryTurakApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StoryTurak',
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF3B82F6), // Blue 500
        scaffoldBackgroundColor: const Color(0xFF0F172A), // Slate 900
        textTheme: GoogleFonts.interTextTheme(
          Theme.of(context).textTheme,
        ).apply(
          bodyColor: const Color(0xFFF8FAFC),
          displayColor: const Color(0xFFF8FAFC),
        ),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3B82F6),
          secondary: Color(0xFFF59E0B), // Amber 500
          surface: Color(0xFF1E293B), // Slate 800
        ),
        useMaterial3: true,
      ),
      home: const CampaignListScreen(),
    );
  }
}

class CampaignListScreen extends StatefulWidget {
  const CampaignListScreen({super.key});

  @override
  State<CampaignListScreen> createState() => _CampaignListScreenState();
}

class _CampaignListScreenState extends State<CampaignListScreen> {
  
  Map<String, String>? _lastState;

  @override
  void initState() {
    super.initState();
    _checkLastState();
  }

  Future<void> _checkLastState() async {
    final state = await StoryEngine.getLastState();
    if (mounted) setState(() => _lastState = state);
  }

  void _continueGame() {
    if (_lastState == null) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => GameScreen(
          storyId: _lastState!['storyId']!,
          initialNodeId: _lastState!['nodeId'],
        ),
      ),
    ).then((_) => _checkLastState());
  }

  void _startSolo(String storyId) {
    if (storyId == 'mist-01') {
       Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => IntroScreen(storyId: storyId)),
      ).then((_) => _checkLastState());
    } else {
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => GameScreen(storyId: storyId)),
      ).then((_) => _checkLastState());
    }
  }

  void _startTeam(String storyId) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => LobbyScreen(campaignId: storyId, isHost: true),
      ),
    );
  }

  void _joinTeam() {
    // Show dialog to enter code, then navigate to LobbyScreen(isHost: false)
    showDialog(context: context, builder: (ctx) {
        final controller = TextEditingController();
        return AlertDialog(
            title: const Text("Csatlakozás"),
            content: TextField(
                controller: controller, 
                decoration: const InputDecoration(labelText: "Kód (pl. ABCD)")
            ),
            actions: [
                TextButton(
                    onPressed: () {
                         // TODO: Validate and join
                         Navigator.pop(ctx);
                         // For MVP just navigating to lobby with dummy session
                    }, 
                    child: const Text("OK")
                )
            ],
        );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Kalandok'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
            IconButton(icon: const Icon(Icons.link), onPressed: _joinTeam)
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_lastState != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: _buildContinueCard(),
            ),
          _buildCampaignCard(
            title: "A Vigadó Árnyéka",
            description: "Nyomozás a pesti Duna-parton.",
            onSolo: () => _startSolo('vigado-01'),
            onTeam: () => _startTeam('vigado-01'),
          ),
          _buildCampaignCard(
            title: "A Ködön Járó",
            description: "Okkult nyomozás a belvárosban. (ÚJ!)",
            onSolo: () => _startSolo('mist-01'),
            onTeam: () => _startTeam('mist-01'),
          ),
        ],
      ),
    );
  }

  Widget _buildCampaignCard({required String title, required String description, 
        required VoidCallback onSolo, required VoidCallback onTeam}) {
    return Card(
      elevation: 4,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            height: 150,
            decoration: const BoxDecoration(
              borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
              color: Colors.grey, 
            ),
            child: const Center(child: Icon(Icons.image, size: 50, color: Colors.white54)),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                 Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                 const SizedBox(height: 8),
                 Text(description, style: const TextStyle(fontSize: 14, color: Colors.white70)),
                 const SizedBox(height: 16),
                 Row(
                     children: [
                         Expanded(child: ElevatedButton(onPressed: onSolo, child: const Text("EGYEDÜL"))),
                         const SizedBox(width: 8),
                         Expanded(child: OutlinedButton(onPressed: onTeam, child: const Text("CSAPAT")))
                     ],
                 )
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildContinueCard() {
    return Card(
      color: Colors.blueAccent.withOpacity(0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16), 
        side: const BorderSide(color: Colors.blueAccent, width: 1)
      ),
      child: ListTile(
        leading: const Icon(Icons.history, color: Colors.blueAccent),
        title: const Text("FOLYAMATBAN LÉVŐ JÁTÉK", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1.2)),
        subtitle: const Text("Kattints a folytatáshoz..."),
        trailing: const Icon(Icons.chevron_right),
        onTap: _continueGame,
      ),
    );
  }
}

