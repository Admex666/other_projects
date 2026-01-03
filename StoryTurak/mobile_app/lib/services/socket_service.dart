
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:latlong2/latlong.dart';

class SocketService {
  WebSocketChannel? _channel;
  final String baseUrl = "wss://storyturak-backend.onrender.com/ws"; // Match your backend address

  Stream<dynamic> get stream => _channel?.stream ?? const Stream.empty();

  void connect(String sessionId, String userId) {
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
