import 'package:flutter/foundation.dart';
import 'card_model.dart';
import 'player_model.dart';

enum GamePhase { draw, action, event, end }

@immutable
class MatchModel {
  final String id;
  final PlayerModel player;
  final PlayerModel opponent;
  final List<CardModel> playerBoard;
  final List<CardModel> opponentBoard;
  final List<CardModel> playerHand;
  final List<String> matchLog;
  final int turnCount;
  final bool isPlayerTurn;
  final GamePhase phase;

  const MatchModel({
    required this.id,
    required this.player,
    required this.opponent,
    this.playerBoard = const [],
    this.opponentBoard = const [],
    this.playerHand = const [],
    this.matchLog = const [],
    this.turnCount = 1,
    this.isPlayerTurn = true,
    this.phase = GamePhase.draw,
  });

  MatchModel copyWith({
    String? id,
    PlayerModel? player,
    PlayerModel? opponent,
    List<CardModel>? playerBoard,
    List<CardModel>? opponentBoard,
    List<CardModel>? playerHand,
    List<String>? matchLog,
    int? turnCount,
    bool? isPlayerTurn,
    GamePhase? phase,
  }) {
    return MatchModel(
      id: id ?? this.id,
      player: player ?? this.player,
      opponent: opponent ?? this.opponent,
      playerBoard: playerBoard ?? this.playerBoard,
      opponentBoard: opponentBoard ?? this.opponentBoard,
      playerHand: playerHand ?? this.playerHand,
      matchLog: matchLog ?? this.matchLog,
      turnCount: turnCount ?? this.turnCount,
      isPlayerTurn: isPlayerTurn ?? this.isPlayerTurn,
      phase: phase ?? this.phase,
    );
  }
}
