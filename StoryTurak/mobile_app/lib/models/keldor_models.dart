import 'package:latlong2/latlong.dart';

enum CharacterClass {
  archivist,
  vigilante,
  collector,
}

enum EncounterType {
  quest,
  random,
  story,
}

enum EncounterNodeType {
  narrative,
  choice,
  fight,
  input,
  order,
}

class EncounterChoice {
  final String text;
  final String nextNodeId;
  final String? condition;

  EncounterChoice({
    required this.text,
    required this.nextNodeId,
    this.condition,
  });

  factory EncounterChoice.fromJson(Map<String, dynamic> json) {
    return EncounterChoice(
      text: json['text'],
      nextNodeId: json['next_node_id'],
      condition: json['condition'],
    );
  }
}

class EncounterNode {
  final String id;
  final EncounterNodeType type;
  final String text;
  final String? image;
  final List<EncounterChoice>? choices;
  final String? nextNodeId;
  // Combat
  final String? enemyId;
  final int? enemyHp;
  final String? enemyClass; // 'archivist', 'vigilante', 'collector' (or monster types mapping to these)
  final String? weaknessItemId;
  // Input
  final String? correctAnswer;
  final List<String>? validAnswers;
  final String? successNodeId;
  final String? failureNodeId;
  final String? buttonText;
  final List<String>? options;

  EncounterNode({
    required this.id,
    required this.type,
    required this.text,
    this.image,
    this.choices,
    this.nextNodeId,
    this.enemyId,
    this.enemyHp,
    this.enemyClass,
    this.weaknessItemId,
    this.correctAnswer,
    this.validAnswers,
    this.successNodeId,
    this.failureNodeId,
    this.buttonText,
    this.options,
  });

  factory EncounterNode.fromJson(Map<String, dynamic> json) {
    return EncounterNode(
      id: json['id'],
      type: EncounterNodeType.values.firstWhere(
        (e) => e.toString().split('.').last == json['type'],
        orElse: () => EncounterNodeType.narrative,
      ),
      text: json['text'],
      image: json['image'],
      choices: (json['choices'] as List?)
          ?.map((c) => EncounterChoice.fromJson(c))
          .toList(),
      nextNodeId: json['next_node_id'],
      enemyId: json['enemy_id'],
      enemyHp: json['enemy_hp'],
      enemyClass: json['enemy_class'],
      weaknessItemId: json['weakness_item_id'],
      correctAnswer: json['correct_answer'],
      validAnswers: (json['valid_answers'] as List?)?.map((v) => v as String).toList(),
      successNodeId: json['success_node_id'],
      failureNodeId: json['failure_node_id'],
      buttonText: json['button_text'],
      options: (json['options'] as List?)?.map((o) => o as String).toList(),
    );
  }
}

class Encounter {
  final String id;
  final String title;
  final String description;
  final EncounterType type;
  final Map<String, EncounterNode> nodes;
  final String startNodeId;
  final LatLng location;
  final String zoneId;

  Encounter({
    required this.id,
    required this.title,
    required this.description,
    required this.type,
    required this.nodes,
    required this.startNodeId,
    required this.location,
    required this.zoneId,
  });

  factory Encounter.fromJson(Map<String, dynamic> json) {
    final nodesMap = (json['nodes'] as Map<String, dynamic>).map(
      (key, value) => MapEntry(key, EncounterNode.fromJson(value)),
    );

    final locData = json['location'];
    final loc = LatLng(locData[0].toDouble(), locData[1].toDouble());

    return Encounter(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      type: EncounterType.values.firstWhere((e) => e.name == json['type'].toString().toLowerCase(), orElse: () => EncounterType.story),
      nodes: nodesMap,
      startNodeId: json['start_node_id'],
      location: loc,
      zoneId: json['zone_id'],
    );
  }
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

class Item {
  // ... (remains same)
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
  final int steps;
  final int weeklySteps;
  final int maxHp;
  final int currentHp;
  final List<InventorySlot> inventory;

  Character({
    required this.id,
    required this.userId,
    required this.name,
    required this.characterClass,
    required this.level,
    required this.steps,
    required this.weeklySteps,
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
        orElse: () => CharacterClass.vigilante,
      ),
      level: json['level'],
      steps: json['steps'],
      weeklySteps: json['weekly_steps'] ?? 0,
      maxHp: json['max_hp'],
      currentHp: json['current_hp'] ?? json['max_hp'],
      inventory: (json['inventory'] as List?)
          ?.map((i) => InventorySlot.fromJson(i))
          .toList() ?? [],
    );
  }

  Character copyWith({
    String? id,
    String? userId,
    String? name,
    CharacterClass? characterClass,
    int? level,
    int? steps,
    int? weeklySteps,
    int? maxHp,
    int? currentHp,
    List<InventorySlot>? inventory,
  }) {
    return Character(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      name: name ?? this.name,
      characterClass: characterClass ?? this.characterClass,
      level: level ?? this.level,
      steps: steps ?? this.steps,
      weeklySteps: weeklySteps ?? this.weeklySteps,
      maxHp: maxHp ?? this.maxHp,
      currentHp: currentHp ?? this.currentHp,
      inventory: inventory ?? this.inventory,
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
  complete_encounter,
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

class QuestStage {
  final String id;
  final String description;
  final LatLng location;
  final String? encounterId;

  QuestStage({
    required this.id,
    required this.description,
    required this.location,
    this.encounterId,
  });

  factory QuestStage.fromJson(Map<String, dynamic> json) {
    return QuestStage(
      id: json['id'],
      description: json['description'],
      location: LatLng(json['location'][0].toDouble(), json['location'][1].toDouble()),
      encounterId: json['encounter_id'],
    );
  }
}

class Quest {
  final String id;
  final String title;
  final String description;
  final String? flavorText;
  final String? imageUrl;
  final LatLng startLocation;
  final List<QuestStage> stages;
  final double estimatedDistanceKm;
  final int estimatedDurationMin;
  final String difficulty;
  final int minLevel;
  final List<String> introSteps;
  final List<QuestObjective> objectives;
  final int rewardsSteps;
  final String? starterZoneId;

  Quest({
    required this.id,
    required this.title,
    required this.description,
    this.flavorText,
    this.imageUrl,
    required this.startLocation,
    required this.stages,
    this.estimatedDistanceKm = 0.0,
    this.estimatedDurationMin = 30,
    this.difficulty = "Közepes",
    required this.minLevel,
    this.introSteps = const [],
    required this.objectives,
    required this.rewardsSteps,
    required this.starterZoneId,
  });

  factory Quest.fromJson(Map<String, dynamic> json) {
    return Quest(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      flavorText: json['flavor_text'],
      imageUrl: json['image_url'],
      startLocation: json['start_location'] != null
          ? LatLng(json['start_location'][0].toDouble(), json['start_location'][1].toDouble())
          : (json['location'] != null 
              ? LatLng(json['location'][0].toDouble(), json['location'][1].toDouble())
              : const LatLng(0, 0)),
      stages: (json['stages'] as List?)
          ?.map((s) => QuestStage.fromJson(s))
          .toList() ?? [],
      estimatedDistanceKm: (json['estimated_distance_km'] ?? 0.0).toDouble(),
      estimatedDurationMin: json['estimated_duration_min'] ?? 30,
      difficulty: json['difficulty'] ?? "Közepes",
      minLevel: json['min_level'],
      introSteps: (json['intro_steps'] as List?)?.map((s) => s as String).toList() ?? [],
      objectives: (json['objectives'] as List?)
          ?.map((o) => QuestObjective.fromJson(o))
          .toList() ?? [],
      rewardsSteps: json['rewards_steps'] ?? 0,
      starterZoneId: json['starter_zone_id'],
    );
  }
}

class UserQuest {
  final String id;
  final String questId;
  final QuestStatus status;
  final int currentStageIndex;
  final int currentObjectiveIndex;
  final int currentCount;

  UserQuest({
    required this.id,
    required this.questId,
    required this.status,
    required this.currentStageIndex,
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
      currentStageIndex: json['current_stage_index'] ?? 0,
      currentObjectiveIndex: json['current_objective_index'] ?? 0,
      currentCount: json['current_count'],
      questTitle: json['quest_title'],
      questDescription: json['quest_description'],
    );
  }
}
