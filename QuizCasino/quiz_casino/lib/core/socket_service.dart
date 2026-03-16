import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/game_data.dart';
import 'constants.dart';

class SocketService {
  static final SocketService _instance = SocketService._internal();
  factory SocketService() => _instance;
  SocketService._internal();

  IO.Socket? _socket;
  IO.Socket get socket {
    if (_socket == null) {
      init(AppConstants.serverUrl);
    }
    return _socket!;
  }
  bool isConnected = false;

  // Callbacks
  Function(dynamic)? onMatchFound;
  Function(dynamic)? onStateUpdate;
  Function(dynamic)? onTick;
  Function(dynamic)? onMatchEnded;
  Function(String, List<UserStats>)? onLeaderboardUpdate;
  Function(UserStats)? onPlayerInfo;
  Function(List<dynamic>)? onShopCatalog;
  Function(Map<String, dynamic>)? onPurchaseResult;

  void init(String url) {
    if (_socket != null) return;
    
    _socket = IO.io(url, <String, dynamic>{
      'transports': ['websocket', 'polling'],
      'autoConnect': false,
      'forceNew': true,
    });

    socket.on('connect', (_) {
      debugPrint('DEBUG: Socket Connected! ID: ${socket.id}');
      isConnected = true;
    });

    socket.on('connect_error', (data) {
      debugPrint('DEBUG: Socket Connect Error: $data');
    });

    socket.on('connect_timeout', (data) {
      debugPrint('DEBUG: Socket Connect Timeout: $data');
    });

    socket.onError((data) {
      debugPrint('DEBUG: Socket General Error: $data');
    });

    socket.on('disconnect', (_) {
      debugPrint('DEBUG: Socket Disconnected!');
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

    socket.on('leaderboard_update', (data) {
      final league = data['league'] as String;
      final players = (data['players'] as List).map((p) => UserStats.fromJson(p)).toList();
      if (onLeaderboardUpdate != null) onLeaderboardUpdate!(league, players);
    });

    socket.on('user_stats', (data) => _onUserStats?.call(UserStats.fromJson(data)));
    socket.on('auth_success', (data) => _onAuthSuccess?.call(UserStats.fromJson(data)));
    socket.on('player_info', (data) => onPlayerInfo?.call(UserStats.fromJson(data)));
    socket.on('shop_catalog', (data) => onShopCatalog?.call(data as List<dynamic>));
    socket.on('purchase_result', (data) => onPurchaseResult?.call(Map<String, dynamic>.from(data)));
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
    debugPrint('DEBUG: Calling joinQueue, status: ${socket.connected}');
    socket.emit('join_queue', {'username': username, 'userId': userId});
  }

  void leaveQueue() {
    debugPrint('DEBUG: Calling leaveQueue, status: ${socket.connected}');
    socket.emit('leave_queue');
  }

  void getStats(String userId, {String? username}) {
    debugPrint('DEBUG: Calling getStats for ${username ?? userId}, status: ${socket.connected}');
    socket.emit('get_stats', {'username': username ?? userId});
  }

  void login(String username, String password) {
    debugPrint('DEBUG: Emitting auth_login for $username, socket.connected: ${socket.connected}');
    socket.emit('auth_login', {'username': username, 'password': password});
  }

  void register(String username, String password) {
    debugPrint('DEBUG: Emitting auth_register for $username, socket.connected: ${socket.connected}');
    socket.emit('auth_register', {'username': username, 'password': password});
  }

  void placeBet(String roomId, int amount) {
    socket.emit('place_bet', {'roomId': roomId, 'amount': amount});
  }

  void selectAnswer(String roomId, int index) {
    socket.emit('select_answer', {'roomId': roomId, 'index': index});
  }

  void getLeaderboard(String league) {
    socket.emit('get_leaderboard', {'league': league});
  }

  void createGuild(String username, String name, String tag) {
    socket.emit('create_guild', {
      'username': username,
      'name': name,
      'tag': tag,
    });
  }

  void getGuild(String tag) {
    socket.emit('get_guild', {'tag': tag});
  }

  void searchGuilds(String? query) {
    socket.emit('search_guilds', {'query': query});
  }

  void requestToJoin(String username, String guildTag) {
    socket.emit('request_to_join', {'username': username, 'guildTag': guildTag});
  }

  void handleJoinRequest(String leaderUsername, String guildTag, String applicantUsername, bool accept) {
    socket.emit('handle_join_request', {
      'leaderUsername': leaderUsername,
      'guildTag': guildTag,
      'applicantUsername': applicantUsername,
      'accept': accept,
    });
  }

  void updateGuildSettings(String leaderUsername, String guildTag, bool isPublic) {
    socket.emit('update_guild_settings', {
      'leaderUsername': leaderUsername,
      'guildTag': guildTag,
      'settings': { 'isPublic': isPublic }
    });
  }

  void getPlayerInfo(String username) {
    socket.emit('get_player_info', {'username': username});
  }

  void leaveGuild(String username, String guildTag) {
    socket.emit('leave_guild', {'username': username, 'guildTag': guildTag});
  }

  void kickMember(String leaderUsername, String guildTag, String targetUsername) {
    socket.emit('kick_member', {
      'leaderUsername': leaderUsername,
      'guildTag': guildTag,
      'targetUsername': targetUsername
    });
  }

  void deleteGuild(String leaderUsername, String guildTag) {
    socket.emit('delete_guild', {'leaderUsername': leaderUsername, 'guildTag': guildTag});
  }

  void getShopCatalog() {
    socket.emit('get_shop_catalog');
  }

  void purchaseItem(String username, String itemId) {
    socket.emit('purchase_item', {'username': username, 'itemId': itemId});
  }

  void equipItem(String username, String itemId) {
    socket.emit('equip_item', {'username': username, 'itemId': itemId});
  }

  Future<Map<String, dynamic>?> fetchVersion() async {
    try {
      final response = await http.get(Uri.parse('${AppConstants.serverUrl}/version'));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (e) {
      debugPrint('DEBUG: Error fetching version: $e');
    }
    return null;
  }

  void dispose() {
    _socket?.dispose();
  }
}
