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
  });
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
  final int gamesPlayed;
  final int victories;

  UserStats({
    required this.userId,
    required this.username,
    required this.totalCoins,
    required this.gamesPlayed,
    required this.victories,
  });

  factory UserStats.fromJson(Map<String, dynamic> json) {
    return UserStats(
      userId: json['userId'] ?? "",
      username: json['username'] ?? "",
      totalCoins: json['totalCoins'] ?? 0,
      gamesPlayed: json['gamesPlayed'] ?? 0,
      victories: json['victories'] ?? 0,
    );
  }
}
