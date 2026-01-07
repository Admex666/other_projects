
import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:latlong2/latlong.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SocketService {
  WebSocketChannel? _channel;
  Timer? _heartbeatTimer;
  static const String prodWs = "wss://storyturak-backend.onrender.com/ws";
  static const String localWs = "ws://192.168.31.86:8001/ws";

  Stream<dynamic> get stream => _channel?.stream ?? const Stream.empty();

  Future<void> connect(String sessionId, String userId) async {
    final prefs = await SharedPreferences.getInstance();
    final isLocal = prefs.getBool('use_local_backend') ?? false;
    final localIp = prefs.getString('local_ip') ?? '10.0.2.2';
    final baseUrl = isLocal ? "ws://$localIp:8001/ws" : prodWs;

    _channel = WebSocketChannel.connect(
      Uri.parse("$baseUrl/$sessionId/$userId"),
    );

    _startHeartbeat();
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      _channel?.sink.add(jsonEncode({"type": "HEARTBEAT"}));
    });
  }

  void sendPosition(LatLng pos) {
    _channel?.sink.add(jsonEncode({
      "type": "POSITION",
      "lat": pos.latitude,
      "lng": pos.longitude
    }));
  }

  void sendAdvance(String storyId, String nodeId, Map<String, dynamic> variables) {
    _channel?.sink.add(jsonEncode({
      "type": "STORY_ADVANCE",
      "storyId": storyId,
      "nodeId": nodeId,
      "variables": variables
    }));
  }

  void sendReady(bool ready) {
    _channel?.sink.add(jsonEncode({
      "type": "USER_READY",
      "ready": ready
    }));
  }

  void sendStart() {
    _channel?.sink.add(jsonEncode({
      "type": "GAME_START"
    }));
  }

  void disconnect() {
    _heartbeatTimer?.cancel();
    _channel?.sink.close();
  }
}
