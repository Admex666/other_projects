import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/session.dart';
import '../services/api_service.dart';
import '../services/story_engine.dart';
import 'lobby_screen.dart';
import 'game_screen.dart';

class SessionHistoryScreen extends StatefulWidget {
  const SessionHistoryScreen({super.key});

  @override
  State<SessionHistoryScreen> createState() => _SessionHistoryScreenState();
}

class _SessionHistoryScreenState extends State<SessionHistoryScreen> {
  late Future<List<Session>> _sessionsFuture;
  final ApiService _api = ApiService();

  @override
  void initState() {
    super.initState();
    final auth = Provider.of<AuthService>(context, listen: false);
    final user = Provider.of<StoryEngine>(context, listen: false).user;
    if (user != null && auth.token != null) {
      _sessionsFuture = _api.getUserSessions(auth.token!, user.id);
    } else {
      _sessionsFuture = Future.error("Bejelentkezés szükséges");
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
            pinned: true,
            backgroundColor: const Color(0xFF0F172A),
            flexibleSpace: FlexibleSpaceBar(
              title: Text("Közös Játékok", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
              centerTitle: false,
              titlePadding: const EdgeInsets.only(left: 20, bottom: 16),
            ),
          ),
          SliverFillRemaining(
            child: FutureBuilder<List<Session>>(
              future: _sessionsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(child: Text("Hiba: ${snapshot.error}", style: const TextStyle(color: Colors.white70)));
                }
                final sessions = snapshot.data ?? [];
                if (sessions.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.history, size: 64, color: Colors.white10),
                        const SizedBox(height: 16),
                        Text("Még nincsenek korábbi játékaid", style: GoogleFonts.outfit(color: Colors.white38)),
                      ],
                    ),
                  );
                }

                return ListView.builder(
                  padding: const EdgeInsets.all(20),
                  itemCount: sessions.length,
                  itemBuilder: (context, index) {
                    final session = sessions[index];
                    return _buildSessionCard(session);
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionCard(Session session) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white10),
      ),
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        title: Text(
          _getStoryTitle(session.campaignId),
          style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        subtitle: Text(
          "Kód: ${session.id} • ${session.status.toUpperCase()}",
          style: TextStyle(color: _getStatusColor(session.status), fontSize: 12),
        ),
        leading: CircleAvatar(
          backgroundColor: Colors.blueAccent.withOpacity(0.1),
          child: const Icon(Icons.group, color: Colors.blueAccent),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("TAGOK", style: TextStyle(fontSize: 10, letterSpacing: 2, color: Colors.white38)),
                const SizedBox(height: 12),
                ...session.players.map((p) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.person_outline, size: 16, color: Colors.white60),
                      const SizedBox(width: 12),
                      Expanded(child: Text(p.username, style: const TextStyle(color: Colors.white70))),
                      if (p.id == session.hostId)
                        const Text("HOST", style: TextStyle(color: Colors.amber, fontSize: 10)),
                    ],
                  ),
                )),
                if (session.status != 'finished') ...[
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      if (session.status == 'waiting') {
                        Navigator.push(context, MaterialPageRoute(builder: (context) => LobbyScreen(session: session)));
                      } else {
                        Navigator.push(
                          context, 
                          MaterialPageRoute(
                            builder: (context) => GameScreen(
                              storyId: session.campaignId,
                              sessionId: session.id,
                              userId: Provider.of<StoryEngine>(context, listen: false).user!.id,
                            )
                          )
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      minimumSize: const Size(double.infinity, 44),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text("VISSZALÉPÉS"),
                  ),
                ]
              ],
            ),
          )
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'active': return Colors.greenAccent;
      case 'waiting': return Colors.amberAccent;
      case 'finished': return Colors.white24;
      default: return Colors.white;
    }
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
