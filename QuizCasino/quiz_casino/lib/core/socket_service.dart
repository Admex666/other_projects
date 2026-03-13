import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'package:flutter/foundation.dart';
import '../models/game_data.dart';

class SocketService {
  static final SocketService _instance = SocketService._internal();
  factory SocketService() => _instance;
  SocketService._internal();

  IO.Socket? _socket;
  IO.Socket get socket {
    if (_socket == null) {
      init("https://quiz-casino.onrender.com");
    }
    return _socket!;
  }
  bool isConnected = false;

  // Callbacks
  Function(dynamic)? onMatchFound;
  Function(dynamic)? onStateUpdate;
  Function(int)? onTick;
  Function(dynamic)? onMatchEnded;

  void init(String url) {
    if (_socket != null) return;
    
    _socket = IO.io(url, <String, dynamic>{
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

    socket.on('user_stats', (data) => _onUserStats?.call(UserStats.fromJson(data)));
    socket.on('auth_success', (data) => _onAuthSuccess?.call(UserStats.fromJson(data)));
    _socket!.on('auth_error', (data) => _onAuthError?.call(data['message'] ?? "Unknown error"));
    
    _socket!.connect();
  }

  Function(UserStats)? _onUserStats;
  Function(UserStats)? _onAuthSuccess;
  Function(String)? _onAuthError;

  void onUserStats(Function(UserStats) callback) => _onUserStats = callback;
  void onAuthSuccess(Function(UserStats) callback) => _onAuthSuccess = callback;
  void onAuthError(Function(String) callback) => _onAuthError = callback;

  void joinQueue(String username, String userId) {
    socket.emit('join_queue', {'username': username, 'userId': userId});
  }

  void leaveQueue() {
    socket.emit('leave_queue');
  }

  void getStats(String userId, {String? username}) {
    socket.emit('get_stats', {'username': username ?? userId});
  }

  void login(String username, String password) {
    socket.emit('auth_login', {'username': username, 'password': password});
  }

  void register(String username, String password) {
    socket.emit('auth_register', {'username': username, 'password': password});
  }

  void placeBet(String roomId, int amount) {
    socket.emit('place_bet', {'roomId': roomId, 'amount': amount});
  }

  void selectAnswer(String roomId, int index) {
    socket.emit('select_answer', {'roomId': roomId, 'index': index});
  }

  void dispose() {
    _socket?.dispose();
  }
}
