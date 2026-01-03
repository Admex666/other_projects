
class Session {
  final String id;
  final String campaignId;
  final String hostId;
  final String status;
  final List<Player> players;

  Session({
    required this.id,
    required this.campaignId,
    required this.hostId,
    required this.status,
    required this.players,
  });

  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      id: json['id'],
      campaignId: json['campaignId'],
      hostId: json['hostId'],
      status: json['status'],
      players: (json['players'] as List)
          .map((p) => Player.fromJson(p))
          .toList(),
    );
  }
}

class Player {
  final String id;
  final String name;
  final bool isReady;

  Player({
    required this.id,
    required this.name,
    this.isReady = false,
  });

  factory Player.fromJson(Map<String, dynamic> json) {
    return Player(
      id: json['id'],
      name: json['name'],
      isReady: json['isReady'] ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'isReady': isReady,
  };
}
