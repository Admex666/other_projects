import '../models/game_data.dart';

class RoundResult {
  final int totalPot;
  final Map<String, int> netChanges;
  RoundResult(this.totalPot, this.netChanges);
}

class RoundController {
  Question? currentQuestion;
  final Map<String, Bet> _playerBets = {};

  void startRound(Question question) {
    currentQuestion = question;
    _playerBets.clear();
  }

  void clearQuestion() {
    currentQuestion = null;
    _playerBets.clear();
  }

  void registerBet(Bet bet) {
    _playerBets[bet.playerId] = bet;
  }

  RoundResult processRoundResults(List<Player> allPlayers) {
    if (currentQuestion == null) return RoundResult(0, {});

    int totalPot = 0;
    int totalWinningBets = 0;
    List<Player> winners = [];
    Map<String, int> netChanges = {};

    // 1. Collect losing bets into the pot, identify winners
    for (var player in allPlayers) {
      if (player.isEliminated) continue;
      netChanges[player.id] = 0;

      final bet = _playerBets[player.id];
      if (bet != null) {
        // Subtract bet from stack initially
        player.stack -= bet.amount;
        netChanges[player.id] = -bet.amount;

        if (bet.answerIndex == currentQuestion!.correctAnswerIndex) {
          // Winner
          winners.add(player);
          totalWinningBets += bet.amount;
          // Return their original bet amount since they won
          player.stack += bet.amount;
          netChanges[player.id] = 0; // recovered original bet
        } else {
          // Loser - their bet goes to the pot
          totalPot += bet.amount;
        }
      }
    }

    // 2. Distribute the pot proportionally to winners
    if (totalPot > 0 && winners.isNotEmpty && totalWinningBets > 0) {
      for (var winner in winners) {
        final winnerBet = _playerBets[winner.id]!;
        double weight = winnerBet.amount / totalWinningBets;
        int wonAmount = (totalPot * weight).floor();
        winner.stack += wonAmount;
        netChanges[winner.id] = (netChanges[winner.id] ?? 0) + wonAmount;
      }
    }

    return RoundResult(totalPot, netChanges);
  }

  Bet? getBetForPlayer(String playerId) {
    return _playerBets[playerId];
  }
}
