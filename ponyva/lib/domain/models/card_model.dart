import 'package:flutter/foundation.dart';

enum CardType { character, event, equipment }

enum CardRarity { common, rare, epic, legendary }

enum Faction { betyar, sarkany, folk, punk }

@immutable
class CardModel {
  final String id;
  final String name;
  final String description;
  final CardType type;
  final CardRarity rarity;
  final Faction faction;
  final int attack;
  final int hp;
  final int luck;
  final int stability;
  final int manaCost;
  final String? imageUrl;

  const CardModel({
    required this.id,
    required this.name,
    required this.description,
    required this.type,
    required this.rarity,
    required this.faction,
    required this.attack,
    required this.hp,
    required this.luck,
    required this.stability,
    required this.manaCost,
    this.imageUrl,
  });

  CardModel copyWith({
    String? id,
    String? name,
    String? description,
    CardType? type,
    CardRarity? rarity,
    Faction? faction,
    int? attack,
    int? hp,
    int? luck,
    int? stability,
    int? manaCost,
    String? imageUrl,
  }) {
    return CardModel(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      type: type ?? this.type,
      rarity: rarity ?? this.rarity,
      faction: faction ?? this.faction,
      attack: attack ?? this.attack,
      hp: hp ?? this.hp,
      luck: luck ?? this.luck,
      stability: stability ?? this.stability,
      manaCost: manaCost ?? this.manaCost,
      imageUrl: imageUrl ?? this.imageUrl,
    );
  }
}
