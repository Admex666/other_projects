import 'dart:math';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../domain/models/match_model.dart';
import '../domain/models/player_model.dart';
import '../domain/models/card_model.dart';

part 'match_provider.g.dart';

@riverpod
class MatchController extends _$MatchController {
  @override
  MatchModel build() {
    return _initialMatch();
  }

  MatchModel _initialMatch() {
    final player = PlayerModel(
      id: 'p1',
      name: 'Csaba the Bold',
      deck: [],
      collection: [],
      avatarUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuANXtGJagaTNFqE3-ASqqy7N5QWiDqDqXbwthOm9976xyJAwO7cz2LNioYLuGGNPtYgUlTmjCXL7pPoXGCG4mmq5e1QSq0HgETqpz5Wduk_85nh8nud0bx3VPBuUGfO0Tk6sra8g3nkoj_o-LYR0CTCE9QE4koY18fVMpibm7FrFC1-YZ_sOlMqyaae-WBdihd2QbZ7Q9bQiFN8fKiZcP7jHKsLKTd0nVOiTOK4TxHt5dp3hfaelszioF4iZxwM7JkHkCScbDCe5g',
    );

    final opponent = PlayerModel(
      id: 'opp1',
      name: 'Nagyúr of Chaos',
      hp: 30,
      deck: [],
      collection: [],
    );

    return MatchModel(
      id: 'm1',
      player: player,
      opponent: opponent,
      matchLog: ['Match Started!'],
    );
  }

  void endTurn() {
    final nextIsPlayerTurn = !state.isPlayerTurn;
    state = state.copyWith(
      isPlayerTurn: nextIsPlayerTurn,
      turnCount: nextIsPlayerTurn ? state.turnCount + 1 : state.turnCount,
      phase: GamePhase.draw,
      matchLog: [...state.matchLog, nextIsPlayerTurn ? 'Player turn started.' : 'Opponent turn started.'],
    );
  }

  void playCard(CardModel card) {
    if (!state.isPlayerTurn) return;
    if (state.player.mana < card.manaCost) return;

    state = state.copyWith(
      player: state.player.copyWith(mana: state.player.mana - card.manaCost),
      playerBoard: [...state.playerBoard, card],
      playerHand: state.playerHand.where((c) => c.id != card.id).toList(),
      matchLog: [...state.matchLog, 'Played ${card.name}'],
    );
  }

  void attack(CardModel attacker, CardModel target) {
    // Basic damage logic
    final luckRoll = Random().nextInt(10);
    final stabilityRoll = state.player.stability;
    
    String message = '${attacker.name} attacks ${target.name}';
    
    // Controlled Chaos Logic
    if (luckRoll > stabilityRoll) {
      message += ' - It went wrong! (Missed)';
    } else {
      // Apply damage
      // (This is a simplified version for now)
    }

    state = state.copyWith(
      matchLog: [...state.matchLog, message],
    );
  }
}
