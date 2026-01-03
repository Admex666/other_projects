
import 'dart:async';
import 'package:flutter/material.dart';
import '../models/session.dart';
import '../services/api_service.dart';
import 'game_screen.dart';

class LobbyScreen extends StatefulWidget {
  final String campaignId;
  final bool isHost;
  final Session? initialSession;

  const LobbyScreen({
    super.key,
    required this.campaignId,
    required this.isHost,
    this.initialSession,
  });

  @override
  State<LobbyScreen> createState() => _LobbyScreenState();
}

class _LobbyScreenState extends State<LobbyScreen> {
  final ApiService _api = ApiService();
  Session? _session;
  Timer? _poller;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialSession != null) {
      _session = widget.initialSession;
    } else if (widget.isHost) {
      _createSession();
    }
  }

  Future<void> _createSession() async {
    setState(() => _isLoading = true);
    try {
      final host = Player(id: 'host_${DateTime.now().millisecondsSinceEpoch}', name: 'Host'); // TODO: Real User
      final session = await _api.createSession(widget.campaignId, host);
      setState(() {
        _session = session;
        _isLoading = false;
      });
      _startPolling();
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Hiba: $e')));
    }
  }

  void _startPolling() {
    // MVP Polling until WebSocket is implemented
    _poller = Timer.periodic(const Duration(seconds: 2), (timer) async {
       if (_session == null) return;
       // implement endpoint to get session status if needed
    });
  }

  @override
  void dispose() {
    _poller?.cancel();
    super.dispose();
  }

  void _startGame() {
    // TODO: Verify all ready
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => GameScreen(storyId: widget.campaignId)),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading || _session == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(title: const Text("Lobby")),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            Text("Kód: ${_session!.id}", style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 32),
            Expanded(
              child: ListView.builder(
                itemCount: _session!.players.length,
                itemBuilder: (ctx, i) {
                  final p = _session!.players[i];
                  return ListTile(
                    leading: const Icon(Icons.person),
                    title: Text(p.name),
                    trailing: p.isReady 
                      ? const Icon(Icons.check_circle, color: Colors.green)
                      : const Icon(Icons.circle_outlined),
                  );
                },
              ),
            ),
            if (widget.isHost)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _startGame,
                  child: const Text("INDÍTÁS"),
                ),
              ),
            if (!widget.isHost)
               const Text("Várakozás a házigazdára..."),
          ],
        ),
      ),
    );
  }
}
