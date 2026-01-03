
import 'package:latlong2/latlong.dart';

class Story {
  final String id;
  final String title;
  final String startNode;
  final Map<String, dynamic> initialState;
  final Map<String, StoryNode> nodes;

  Story({
    required this.id,
    required this.title,
    required this.startNode,
    required this.initialState,
    required this.nodes,
  });

  factory Story.fromJson(Map<String, dynamic> json) {
    var nodesJson = json['nodes'] as Map<String, dynamic>;
    Map<String, StoryNode> parsedNodes = {};
    nodesJson.forEach((key, value) {
      parsedNodes[key] = StoryNode.fromJson(value);
    });

    return Story(
      id: json['id'],
      title: json['title'],
      startNode: json['startNode'],
      initialState: json['initialState'] ?? {},
      nodes: parsedNodes,
    );
  }
}

enum NodeType { narrative, location_wait, input, choice }

class StoryNode {
  final String id;
  final NodeType type;
  final String text;
  final String? image;
  final String? next;
  final String? buttonText;
  
  // Location
  final LatLng? targetLocation;
  final String? fallbackButton;

  // Input
  final List<String>? validAnswers;
  final String? successNext;
  final String? failureMessage;

  // Choice
  final List<StoryChoice>? choices;

  StoryNode({
    required this.id,
    required this.type,
    required this.text,
    this.image,
    this.next,
    this.buttonText,
    this.targetLocation,
    this.fallbackButton,
    this.validAnswers,
    this.successNext,
    this.failureMessage,
    this.choices,
  });

  factory StoryNode.fromJson(Map<String, dynamic> json) {
    NodeType type = NodeType.values.firstWhere(
        (e) => e.toString().split('.').last == json['type'],
        orElse: () => NodeType.narrative);

    LatLng? loc;
    if (json['targetLocation'] != null) {
      loc = LatLng(
        (json['targetLocation']['lat'] as num).toDouble(),
        (json['targetLocation']['lng'] as num).toDouble(),
      );
    }

    List<StoryChoice>? choices;
    if (json['choices'] != null) {
      choices = (json['choices'] as List)
          .map((c) => StoryChoice.fromJson(c))
          .toList();
    }

    return StoryNode(
      id: json['id'],
      type: type,
      text: json['text'],
      image: json['image'],
      next: json['next'],
      buttonText: json['buttonText'],
      targetLocation: loc,
      fallbackButton: json['fallbackButton'],
      validAnswers: (json['validAnswers'] as List?)?.map((e) => e.toString()).toList(),
      successNext: json['successNext'],
      failureMessage: json['failureMessage'],
      choices: choices,
    );
  }
}

class StoryChoice {
  final String text;
  final String next;

  StoryChoice({required this.text, required this.next});

  factory StoryChoice.fromJson(Map<String, dynamic> json) {
    return StoryChoice(
      text: json['text'],
      next: json['next'],
    );
  }
}
