enum GameState {
  waiting,
  questionActive,
  reveal,
  result,
}

class Player {
  final String id;
  final String userId;
  final String username;
  int stack;
  bool isEliminated;

  Player({
    required this.id,
    required this.userId,
    required this.username,
    required this.stack,
    this.isEliminated = false,
    this.equippedSkin = "default",
    this.equippedTrail = "none",
    this.equippedAnimation = "none",
  });

  final String equippedSkin;
  final String equippedTrail;
  final String equippedAnimation;
}

class Question {
  final String questionText;
  final List<String> answers;
  final int correctAnswerIndex;

  Question({
    required this.questionText,
    required this.answers,
    required this.correctAnswerIndex,
  });
}

class Bet {
  final String playerId;
  final int amount;
  final int answerIndex;

  Bet({
    required this.playerId,
    required this.amount,
    required this.answerIndex,
  });
}

class RoundResult {
  final int totalPot;
  final Map<String, int> netChanges;

  RoundResult({
    required this.totalPot,
    required this.netChanges,
  });
}

class UserStats {
  final String userId;
  final String username;
  final int totalCoins;
  final int gold;
  final int diamonds;
  final int gamesPlayed;
  final int victories;
  final int elo;
  final String league;
  final int placementMatches;
  final int weeklyTotal;
  final String? guildTag;
  final List<String> inventory;
  final String equippedSkin;
  final String equippedTrail;

  UserStats({
    required this.userId,
    required this.username,
    required this.totalCoins,
    required this.gold,
    required this.diamonds,
    required this.gamesPlayed,
    required this.victories,
    required this.elo,
    required this.league,
    required this.placementMatches,
    required this.weeklyTotal,
    this.guildTag,
    required this.inventory,
    required this.equippedSkin,
    required this.equippedTrail,
  });

  factory UserStats.fromJson(Map<String, dynamic> json) {
    return UserStats(
      userId: json['userId'] ?? "",
      username: json['username'] ?? "",
      totalCoins: json['totalCoins'] ?? 0,
      gold: json['gold'] ?? 0,
      diamonds: json['diamonds'] ?? 0,
      gamesPlayed: json['gamesPlayed'] ?? 0,
      victories: json['victories'] ?? 0,
      elo: json['elo'] ?? 1500,
      league: json['league'] ?? "unranked",
      placementMatches: json['placementMatches'] ?? 0,
      weeklyTotal: json['weeklyTotal'] ?? 0,
      guildTag: json['guildTag'] == "none" ? null : json['guildTag'],
      inventory: List<String>.from(json['inventory'] ?? []),
      equippedSkin: json['equippedSkin'] ?? "default",
      equippedTrail: json['equippedTrail'] ?? "none",
    );
  }
}

class Guild {
  final String name;
  final String tag;
  final String description;
  final String leaderUsername;
  final Map<String, int> shares;
  final int totalShares;
  final int vaultGold;
  final int taxRate;
  final bool isPublic;
  final List<String> pendingRequests;

  Guild({
    required this.name,
    required this.tag,
    required this.description,
    required this.leaderUsername,
    required this.shares,
    required this.totalShares,
    required this.vaultGold,
    required this.taxRate,
    required this.isPublic,
    required this.pendingRequests,
  });

  factory Guild.fromJson(Map<String, dynamic> json) {
    return Guild(
      name: json['name'] ?? "",
      tag: json['tag'] ?? "",
      description: json['description'] ?? "",
      leaderUsername: json['leaderUsername'] ?? "",
      shares: Map<String, int>.from(json['shares'] ?? {}),
      totalShares: json['totalShares'] ?? 1000,
      vaultGold: json['vaultGold'] ?? 0,
      taxRate: json['taxRate'] ?? 5,
      isPublic: json['isPublic'] ?? true,
      pendingRequests: List<String>.from(json['pendingRequests'] ?? []),
    );
  }
}

class ShopItem {
  final String id;
  final String name;
  final String type;
  final int price;
  final String currency;
  final String rarity;

  ShopItem({
    required this.id,
    required this.name,
    required this.type,
    required this.price,
    required this.currency,
    required this.rarity,
  });

  factory ShopItem.fromJson(Map<String, dynamic> json) {
    return ShopItem(
      id: json['id'] ?? "",
      name: json['name'] ?? "",
      type: json['type'] ?? "skin",
      price: json['price'] ?? 0,
      currency: json['currency'] ?? "gold",
      rarity: json['rarity'] ?? "common",
    );
  }
}
