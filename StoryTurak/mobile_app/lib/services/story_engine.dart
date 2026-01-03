
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/story.dart';

class StoryEngine extends ChangeNotifier {
  Story? _currentStory;
  StoryNode? _currentNode;
  Map<String, dynamic> _variables = {};
  final Set<String> _visitedNodes = {};

  StoryNode? get currentNode => _currentNode;
  String? get storyId => _currentStory?.id;

  double get progress {
    if (_currentStory == null || _currentStory!.nodes.isEmpty) return 0.0;
    return (_visitedNodes.length / _currentStory!.nodes.length).clamp(0.0, 1.0);
  }

  void loadStory(Story story, {String? startAtNodeId}) {
    _currentStory = story;
    _variables = Map.from(story.initialState);
    _visitedNodes.clear();
    _advanceTo(startAtNodeId ?? story.startNode, save: false);
  }

  Future<void> _advanceTo(String nodeId, {bool save = true}) async {
    if (_currentStory == null) return;
    
    final node = _currentStory!.nodes[nodeId];
    if (node != null) {
      _currentNode = node;
      _visitedNodes.add(nodeId);
      notifyListeners();
      if (save) await _saveState();
    }
  }

  Future<void> _saveState() async {
    if (_currentStory == null || _currentNode == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('last_story_id', _currentStory!.id);
    await prefs.setString('last_node_id', _currentNode!.id);
  }

  static Future<Map<String, String>?> getLastState() async {
    final prefs = await SharedPreferences.getInstance();
    final storyId = prefs.getString('last_story_id');
    final nodeId = prefs.getString('last_node_id');
    if (storyId != null && nodeId != null) {
      return {'storyId': storyId, 'nodeId': nodeId};
    }
    return null;
  }

  Future<void> clearSave() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('last_story_id');
    await prefs.remove('last_node_id');
  }

  void handleInput(String input) {
    if (_currentNode == null || _currentNode!.type != NodeType.input) return;

    final valid = _currentNode!.validAnswers?.any(
      (ans) => ans.trim().toLowerCase() == input.trim().toLowerCase()
    ) ?? false;

    if (valid) {
      if (_currentNode!.successNext != null) {
        _advanceTo(_currentNode!.successNext!);
      }
    }
  }

  void makeChoice(int index) {
    if (_currentNode == null || _currentNode!.type != NodeType.choice) return;
    
    final choices = _currentNode!.choices;
    if (choices != null && index < choices.length) {
      _advanceTo(choices[index].next);
    }
  }

  void next() {
    if (_currentNode?.next != null) {
      _advanceTo(_currentNode!.next!);
    }
  }
}
