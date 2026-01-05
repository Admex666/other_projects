
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:latlong2/latlong.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SocketService {
  WebSocketChannel? _channel;
  static const String prodWs = "wss://storyturak-backend.onrender.com/ws";
  static const String localWs = "ws://192.168.31.86:8001/ws";

  Stream<dynamic> get stream => _channel?.stream ?? const Stream.empty();

  Future<void> connect(String sessionId, String userId) async {
    final prefs = await SharedPreferences.getInstance();
    final isLocal = prefs.getBool('use_local_backend') ?? false;
    final baseUrl = isLocal ? localWs : prodWs;

    _channel = WebSocketChannel.connect(
      Uri.parse("$baseUrl/$sessionId/$userId"),
    );
  }

  void sendPosition(LatLng pos) {
    _channel?.sink.add(jsonEncode({
      "type": "POSITION",
      "lat": pos.latitude,
      "lng": pos.longitude
    }));
  }

  void sendAdvance(String nodeId) {
    _channel?.sink.add(jsonEncode({
      "type": "STORY_ADVANCE",
      "nodeId": nodeId
    }));
  }

  void disconnect() {
    _channel?.sink.close();
  }
}
