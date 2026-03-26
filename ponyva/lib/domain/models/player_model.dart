import 'package:flutter/foundation.dart';
import 'card_model.dart';

@immutable
class PlayerModel {
  final String id;
  final String name;
  final int level;
  final int xp;
  final int hp;
  final int maxHp;
  final int stability;
  final int actionPoints;
  final int maxActionPoints;
  final int mana;
  final int maxMana;
  final List<CardModel> deck;
  final List<CardModel> collection;
  final String? avatarUrl;

  const PlayerModel({
    required this.id,
    required this.name,
    this.level = 1,
    this.xp = 0,
    this.hp = 30,
    this.maxHp = 30,
    this.stability = 10,
    this.actionPoints = 3,
    this.maxActionPoints = 3,
    this.mana = 0,
    this.maxMana = 10,
    required this.deck,
    required this.collection,
    this.avatarUrl,
  });

  PlayerModel copyWith({
    String? id,
    String? name,
    int? level,
    int? xp,
    int? hp,
    int? maxHp,
    int? stability,
    int? actionPoints,
    int? maxActionPoints,
    int? mana,
    int? maxMana,
    List<CardModel>? deck,
    List<CardModel>? collection,
    String? avatarUrl,
  }) {
    return PlayerModel(
      id: id ?? this.id,
      name: name ?? this.name,
      level: level ?? this.level,
      xp: xp ?? this.xp,
      hp: hp ?? this.hp,
      maxHp: maxHp ?? this.maxHp,
      stability: stability ?? this.stability,
      actionPoints: actionPoints ?? this.actionPoints,
      maxActionPoints: maxActionPoints ?? this.maxActionPoints,
      mana: mana ?? this.mana,
      maxMana: maxMana ?? this.maxMana,
      deck: deck ?? this.deck,
      collection: collection ?? this.collection,
      avatarUrl: avatarUrl ?? this.avatarUrl,
    );
  }
}
