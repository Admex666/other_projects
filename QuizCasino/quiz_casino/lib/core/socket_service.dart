import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'package:flutter/foundation.dart';

class SocketService {
  static final SocketService _instance = SocketService._internal();
  factory SocketService() => _instance;
  SocketService._internal();

  late IO.Socket socket;
  bool isConnected = false;

  // Callbacks
  Function(dynamic)? onMatchFound;
  Function(dynamic)? onStateUpdate;
  Function(int)? onTick;
  Function(dynamic)? onMatchEnded;
  Function(dynamic)? onUserStats;

  void init(String url) {
    socket = IO.io(url, <String, dynamic>{
      'transports': ['websocket'],
      'autoConnect': false,
    });

    socket.onConnect((_) {
      debugPrint('Connected to server!');
      isConnected = true;
    });

    socket.onDisconnect((_) {
      debugPrint('Disconnected from server!');
      isConnected = false;
    });

    socket.on('match_found', (data) {
      if (onMatchFound != null) onMatchFound!(data);
    });

    socket.on('state_update', (data) {
      if (onStateUpdate != null) onStateUpdate!(data);
    });

    socket.on('tick', (data) {
      if (onTick != null) onTick!(data);
    });

    socket.on('match_ended', (data) {
      if (onMatchEnded != null) onMatchEnded!(data);
    });

    socket.on('user_stats', (data) {
      if (onUserStats != null) onUserStats!(data);
    });

    socket.connect();
  }

  void joinQueue(String username, String userId) {
    socket.emit('join_queue', {'username': username, 'userId': userId});
  }

  void placeBet(String roomId, int amount) {
    socket.emit('place_bet', {'roomId': roomId, 'amount': amount});
  }

  void selectAnswer(String roomId, int index) {
    socket.emit('select_answer', {'roomId': roomId, 'index': index});
  }

  void dispose() {
    socket.dispose();
  }
}
