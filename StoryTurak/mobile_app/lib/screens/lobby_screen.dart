
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/session.dart';
import '../services/story_engine.dart';
import '../services/socket_service.dart';
import '../services/api_service.dart';
import 'game_screen.dart';

class LobbyScreen extends StatefulWidget {
  final Session session;
  const LobbyScreen({super.key, required this.session});

  @override
  State<LobbyScreen> createState() => _LobbyScreenState();
}

class _LobbyScreenState extends State<LobbyScreen> {
  late Session _session;
  final SocketService _socket = SocketService();
  bool _isReady = false;

  @override
  void initState() {
    super.initState();
    _session = widget.session;
    _initSocket();
  }

  Future<void> _initSocket() async {
    final engine = Provider.of<StoryEngine>(context, listen: false);
    await _socket.connect(_session.id, engine.user!.id);
    _socket.stream.listen(_handleMessage);
  }

  void _handleMessage(dynamic data) {
    if (data is String) {
      final msg = json.decode(data);
      setState(() {
        if (msg['type'] == 'SESSION_UPDATE') {
          _session = Session.fromJson(msg['session']);
        } else if (msg['type'] == 'GAME_START') {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => GameScreen(
                storyId: _session.campaignId,
                sessionId: _session.id,
                userId: Provider.of<StoryEngine>(context, listen: false).user!.id,
              ),
            ),
          );
        }
      });
    }
  }

  void _toggleReady() {
    setState(() => _isReady = !_isReady);
    _socket.sendReady(_isReady);
  }

  void _startGame() {
    _socket.sendStart();
  }

  @override
  void dispose() {
    _socket.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final engine = Provider.of<StoryEngine>(context);
    final isHost = _session.hostId == engine.user?.id;
    final allReady = _session.players.every((p) => p.isReady || p.id == _session.hostId);

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: const Text("Várakozóterem"),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () async {
              final api = ApiService();
              final auth = Provider.of<AuthService>(context, listen: false);
              if (auth.token != null) {
                final updated = await api.getSession(auth.token!, _session.id);
                setState(() => _session = updated);
              }
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(32),
              decoration: BoxDecoration(
                color: Colors.blueAccent.withOpacity(0.1),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.blueAccent.withOpacity(0.3)),
              ),
              child: Column(
                children: [
                  Text("SZOBAKÓD", style: GoogleFonts.outfit(fontSize: 12, letterSpacing: 4, color: Colors.blueAccent)),
                  const SizedBox(height: 8),
                  Text(_session.id, style: GoogleFonts.outfit(fontSize: 48, fontWeight: FontWeight.bold, color: Colors.white)),
                ],
              ),
            ),
            const SizedBox(height: 32),
            Text("Játékosok", style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: _session.players.length,
                itemBuilder: (context, index) {
                  final p = _session.players[index];
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: p.isReady ? Colors.greenAccent : Colors.white10,
                      child: Icon(Icons.person, color: p.isReady ? Colors.black : Colors.white24),
                    ),
                    title: Text(p.username),
                    trailing: p.id == _session.hostId 
                        ? const Text("GAZDA", style: TextStyle(color: Colors.amber, fontSize: 10))
                        : p.isReady ? const Icon(Icons.check_circle, color: Colors.greenAccent) : const Icon(Icons.hourglass_empty, color: Colors.white24),
                  );
                },
              ),
            ),
            if (!isHost)
              ElevatedButton(
                onPressed: _toggleReady,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isReady ? Colors.greenAccent : Colors.blueAccent,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: Text(_isReady ? "KÉSZEN ÁLLOK" : "KÉSZ VAGYOK"),
              ),
            if (isHost)
              ElevatedButton(
                onPressed: allReady ? _startGame : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.amber,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text("JÁTÉK INDÍTÁSA"),
              ),
            const SizedBox(height: 12),
            const Text(
              "A játék akkor indul, ha mindenki kész.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white24, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
