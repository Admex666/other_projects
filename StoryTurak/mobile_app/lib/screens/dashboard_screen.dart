
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../widgets/campaign_card.dart';
import '../services/story_engine.dart';
import '../screens/game_screen.dart';
import '../screens/intro_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final StoryEngine _engine = StoryEngine();
  Map<String, String>? _lastState;

  @override
  void initState() {
    super.initState();
    _checkLastState();
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
                  
                  CampaignCard(
                    title: "A Ködön Járó",
                    image: "assets/mist_walker_cover.png",
                    difficulty: "Közepes",
                    duration: "45 perc",
                    onTap: () => _startSolo('mist-01'),
                  ),
                  
                  CampaignCard(
                    title: "A Vigadó Árnyéka",
                    image: "assets/vigado_noir.png",
                    difficulty: "Könnyű",
                    duration: "30 perc",
                    onTap: () => _startSolo('vigado-01'),
                  ),
                  
                  CampaignCard(
                    title: "Normafa Árnyai",
                    image: "assets/normafa_cover.png",
                    difficulty: "Közepes",
                    duration: "90 perc",
                    onTap: () => _startSolo('normafa-01'),
                  ),
                  
                  const SizedBox(height: 100), // Spacing for bottom bar
                ],
              ),
            ),
          ),
        ],
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
    switch (id) {
      case 'mist-01': return "A Ködön Járó";
      case 'vigado-01': return "A Vigadó Árnyéka";
      case 'normafa-01': return "Normafa Árnyai";
      default: return "Ismeretlen kaland";
    }
  }
}
