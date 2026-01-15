import 'package:latlong2/latlong.dart';

enum CharacterClass {
  soldier,
  poet,
  tax_collector,
  pilgrim,
}

enum EncounterType {
  fight,
  puzzle,
  narrative,
  shop,
}

class Zone {
  final String id;
  final String name;
  final String description;
  final List<LatLng> boundaryPoints;
  final int difficultyLevel;

  Zone({
    required this.id,
    required this.name,
    required this.description,
    required this.boundaryPoints,
    required this.difficultyLevel,
  });

  factory Zone.fromJson(Map<String, dynamic> json) {
    return Zone(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      boundaryPoints: (json['boundary_points'] as List)
          .map((p) => LatLng(p[0] as double, p[1] as double))
          .toList(),
      difficultyLevel: json['difficulty_level'] ?? 1,
    );
  }
}

class Encounter {
  final String id;
  final String title;
  final String description;
  final EncounterType type;
  final String zoneId;

  Encounter({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.zoneId,
  });

  factory Encounter.fromJson(Map<String, dynamic> json) {
    return Encounter(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      type: EncounterType.values.firstWhere(
        (e) => e.toString().split('.').last == json['type'],
        orElse: () => EncounterType.narrative,
      ),
      zoneId: json['zone_id'],
    );
  }
}

class Item {
  final String id;
  final String name;
  final String description;
  final String type;
  final int value;
  final String iconCode;

  Item({
    required this.id,
    required this.name,
    required this.description,
    required this.type,
    required this.value,
    required this.iconCode,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    return Item(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      type: json['type'],
      value: json['value'],
      iconCode: json['icon_code'],
    );
  }
}

class InventorySlot {
  final String itemId;
  final int quantity;
  final bool equipped;
  
  // Optional metadata enriched by backend
  final String? name;
  final String? description;
  final String? iconCode;
  final Map<String, dynamic>? stats;

  InventorySlot({
    required this.itemId,
    required this.quantity,
    required this.equipped,
    this.name,
    this.description,
    this.iconCode,
    this.stats,
  });

  factory InventorySlot.fromJson(Map<String, dynamic> json) {
    return InventorySlot(
      itemId: json['item_id'],
      quantity: json['quantity'],
      equipped: json['equipped'],
      name: json['name'],
      description: json['description'],
      iconCode: json['icon_code'],
      stats: json['stats'] != null ? Map<String, dynamic>.from(json['stats']) : null,
    );
  }
}

class Character {
  final String id;
  final String userId;
  final String name;
  final CharacterClass characterClass;
  final int level;
  final int xp;
  final int maxHp;
  final int currentHp;
  final List<InventorySlot> inventory;

  Character({
    required this.id,
    required this.userId,
    required this.name,
    required this.characterClass,
    required this.level,
    required this.xp,
    required this.maxHp,
    required this.currentHp,
    required this.inventory,
  });

  factory Character.fromJson(Map<String, dynamic> json) {
    return Character(
      id: json['id'],
      userId: json['user_id'],
      name: json['name'],
      characterClass: CharacterClass.values.firstWhere(
        (e) => e.toString().split('.').last == json['character_class'],
        orElse: () => CharacterClass.pilgrim,
      ),
      level: json['level'],
      xp: json['xp'],
      maxHp: json['max_hp'],
      currentHp: json['current_hp'] ?? json['max_hp'],
      inventory: (json['inventory'] as List?)
          ?.map((i) => InventorySlot.fromJson(i))
          .toList() ?? [],
    );
  }
}

// Quest System Models

enum QuestStatus {
  available,
  active,
  completed,
  failed,
}

enum QuestObjectiveType {
  visit_zone,
  defeat_enemy,
  collect_item,
}

class QuestObjective {
  final String id;
  final QuestObjectiveType type;
  final String targetId;
  final int count;
  final String description;

  QuestObjective({
    required this.id,
    required this.type,
    required this.targetId,
    required this.count,
    required this.description,
  });

  factory QuestObjective.fromJson(Map<String, dynamic> json) {
    return QuestObjective(
      id: json['id'],
      type: QuestObjectiveType.values.firstWhere(
         (e) => e.toString().split('.').last == json['type'],
         orElse: () => QuestObjectiveType.visit_zone
      ),
      targetId: json['target_id'],
      count: json['count'],
      description: json['description'],
    );
  }
}

class Quest {
  final String id;
  final String title;
  final String description;
  final int minLevel;
  final List<QuestObjective> objectives;
  final int rewardsXp;
  final String? starterZoneId;

  Quest({
    required this.id,
    required this.title,
    required this.description,
    required this.minLevel,
    required this.objectives,
    required this.rewardsXp,
    required this.starterZoneId,
  });

  factory Quest.fromJson(Map<String, dynamic> json) {
    return Quest(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      minLevel: json['min_level'],
      objectives: (json['objectives'] as List)
          .map((o) => QuestObjective.fromJson(o))
          .toList(),
      rewardsXp: json['rewards_xp'],
      starterZoneId: json['starter_zone_id'],
    );
  }
}

class UserQuest {
  final String id;
  final String questId;
  final QuestStatus status;
  final int currentObjectiveIndex;
  final int currentCount;

  UserQuest({
    required this.id,
    required this.questId,
    required this.status,
    required this.currentObjectiveIndex,
    required this.currentCount,
    this.questTitle,
    this.questDescription,
  });

  final String? questTitle;
  final String? questDescription;

  factory UserQuest.fromJson(Map<String, dynamic> json) {
    return UserQuest(
      id: json['id'],
      questId: json['quest_id'],
      status: QuestStatus.values.firstWhere(
         (e) => e.toString().split('.').last == json['status'],
         orElse: () => QuestStatus.available
      ),
      currentObjectiveIndex: json['current_objective_index'],
      currentCount: json['current_count'],
      questTitle: json['quest_title'],
      questDescription: json['quest_description'],
    );
  }
}
