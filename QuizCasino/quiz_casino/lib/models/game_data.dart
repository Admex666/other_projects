enum GameState {
  waiting,
  questionActive,
  reveal,
  result,
}

class Player {
  final String id;
  final String username;
  int stack;
  bool isEliminated;

  Player({
    required this.id,
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
