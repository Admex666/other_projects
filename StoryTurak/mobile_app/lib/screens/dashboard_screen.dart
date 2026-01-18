import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../widgets/campaign_card.dart';
import '../services/story_engine.dart';
import '../screens/game_screen.dart';
import '../screens/intro_screen.dart';
import '../screens/lobby_screen.dart';
import '../services/api_service.dart';
import '../models/session.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _lastState;

  @override
  void initState() {
    super.initState();
    _checkLastState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = Provider.of<AuthService>(context, listen: false);
      if (auth.token != null) {
        Provider.of<KeldorService>(context, listen: false).fetchQuests(auth.token!);
      }
    });
  }

  Future<void> _checkLastState() async {
    final state = await StoryEngine.getLastState();
    if (mounted) {
      setState(() => _lastState = state);
    }
  }

  void _continueGame() {
    if (_lastState == null) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => GameScreen(
          storyId: _lastState!['storyId']!,
          initialNodeId: _lastState!['nodeId'],
          initialVars: _lastState!['variables'],
        ),
      ),
    ).then((_) => _checkLastState());
  }

  void _startSolo(String storyId) {
    bool hasIntro = false;
    try {
      final keldor = Provider.of<KeldorService>(context, listen: false);
      final quest = keldor.allQuests.firstWhere((q) => q.id == storyId);
      hasIntro = quest.introSteps.isNotEmpty;
    } catch (_) {}

    if (hasIntro) {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 120,
            floating: false,
            pinned: true,
            backgroundColor: const Color(0xFF0F172A),
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                "Felfedezés",
                style: GoogleFonts.outfit(fontWeight: FontWeight.bold),
              ),
              centerTitle: false,
              titlePadding: const EdgeInsets.only(left: 20, bottom: 16),
            ),
          ),
          
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   if (_lastState != null) ...[
                    _buildContinueCard(),
                    const SizedBox(height: 32),
                  ],
                  
                  Text(
                    "KIEMELT SÉTÁK",
                    style: GoogleFonts.outfit(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                      color: Colors.blueAccent,
                    ),
                  ),
                  const SizedBox(height: 20),
                  
                  Consumer<KeldorService>(
                    builder: (context, keldor, child) {
                      if (keldor.allQuests.isEmpty) {
                        return const Center(child: CircularProgressIndicator());
                      }
                      return Column(
                        children: keldor.allQuests.map((quest) => Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: CampaignCard(
                            title: quest.title,
                            image: quest.imageUrl ?? "assets/placeholder.png",
                            difficulty: quest.difficulty,
                            duration: "${quest.estimatedDurationMin} perc",
                            onTap: () => _startSolo(quest.id),
                          ),
                        )).toList(),
                      );
                    },
                  ),

                  const SizedBox(height: 32),
                  Text(
                    "TÖBBSZEREPLŐS JÁTÉK",
                    style: GoogleFonts.outfit(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                      color: Colors.amber,
                    ),
                  ),
                  const SizedBox(height: 16),
                  _buildMultiplayerCard(),
                  
                  const SizedBox(height: 100), // Spacing for bottom bar
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMultiplayerCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.amber.withOpacity(0.05),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.amber.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _showMultiplayerDialog(isHost: true),
                  icon: const Icon(Icons.add),
                  label: const Text("SZERVER INDÍTÁSA"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.amber,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _showMultiplayerDialog(isHost: false),
                  icon: const Icon(Icons.group_add),
                  label: const Text("CSATLAKOZÁS"),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.amber,
                    side: const BorderSide(color: Colors.amber),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showMultiplayerDialog({required bool isHost}) {
    final keldor = Provider.of<KeldorService>(context, listen: false);
    String? selectedStoryId = keldor.allQuests.isNotEmpty ? keldor.allQuests.first.id : null;
    final codeController = TextEditingController();
    final api = ApiService();
    final engine = Provider.of<StoryEngine>(context, listen: false);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom, left: 24, right: 24, top: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              isHost ? "Új játék indítása" : "Csatlakozás kód alapján",
              style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            if (isHost) ...[
              const Text("Válassz történetet:"),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: selectedStoryId,
                dropdownColor: const Color(0xFF1E293B),
                items: keldor.allQuests.map((q) => DropdownMenuItem(
                  value: q.id,
                  child: Text(q.title, style: GoogleFonts.outfit()),
                )).toList(),
                onChanged: (v) => selectedStoryId = v,
                decoration: InputDecoration(
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ] else ...[
              TextField(
                controller: codeController,
                autofocus: true,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 8),
                textAlign: TextAlign.center,
                decoration: InputDecoration(
                  hintText: "ABCD",
                  counterText: "",
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                maxLength: 4,
              ),
            ],
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () async {
                try {
                  Session session;
                  final auth = Provider.of<AuthService>(context, listen: false);
                  final token = auth.token;
                  if (token == null) throw Exception("Bejelentkezés szükséges");

                  if (isHost) {
                    session = await api.createSession(token, selectedStoryId!, engine.user!);
                  } else {
                    session = await api.joinSession(token, codeController.text.toUpperCase(), engine.user!);
                  }
                  if (mounted) {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (context) => LobbyScreen(session: session)));
                  }
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Hiba: $e")));
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blueAccent,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Text(isHost ? "SZERVER LÉTREHOZÁSA" : "SZOBA KERESÉSE"),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildContinueCard() {
    return InkWell(
      onTap: _continueGame,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.blueAccent.withOpacity(0.1),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.blueAccent.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blueAccent,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 32),
            ),
            const SizedBox(width: 20),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "FOLYTATÁS",
                    style: GoogleFonts.outfit(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.5,
                      color: Colors.blueAccent,
                    ),
                  ),
                  Text(
                    _getStoryTitle(_lastState!['storyId']!),
                    style: GoogleFonts.outfit(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.blueAccent),
          ],
        ),
      ),
    );
  }

  String _getStoryTitle(String id) {
    try {
      final keldor = Provider.of<KeldorService>(context, listen: false);
      return keldor.allQuests.firstWhere((q) => q.id == id).title;
    } catch (_) {
      return "Ismeretlen kaland";
    }
  }
}
