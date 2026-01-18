import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/story.dart';
import '../models/session.dart';
import 'api_service.dart';

class StoryEngine extends ChangeNotifier {
  Story? _currentStory;
  StoryNode? _currentNode;
  Map<String, dynamic> _variables = {};
  final Set<String> _visitedNodes = {};
  Player? _user;
  String? _token;
  final ApiService _api = ApiService();

  StoryNode? get currentNode => _currentNode;
  Story? get story => _currentStory;
  String? get storyId => _currentStory?.id;
  Player? get user => _user;
  Map<String, dynamic> get variables => _variables;

  void setUser(Player user) {
    _user = user;
    _saveUserToPrefs(user);
    notifyListeners();
  }

  void setToken(String? token) {
      _token = token;
  }

  Future<void> _saveUserToPrefs(Player user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_json', json.encode(user.toJson()));
  }

  Future<void> loadUserFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('user_json');
    if (userJson != null) {
      _user = Player.fromJson(json.decode(userJson));
      notifyListeners();
    }
  }

  Future<void> logout() async {
    _user = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_json');
    notifyListeners();
  }

  double get progress {
    if (_currentStory == null || _currentStory!.nodes.isEmpty) return 0.0;
    return (_visitedNodes.length / _currentStory!.nodes.length).clamp(0.0, 1.0);
  }

  void loadStory(Story story, {String? startAtNodeId, Map<String, dynamic>? initialVars}) {
    _currentStory = story;
    _variables = initialVars ?? Map.from(story.initialState);
    _visitedNodes.clear();
    _advanceTo(startAtNodeId ?? story.startNode, save: false);
  }

  Future<void> _advanceTo(String nodeId, {bool save = true}) async {
    if (_currentStory == null) return;
    
    final node = _currentStory!.nodes[nodeId];
    if (node != null) {
      // Handle condition nodes (Auto-advance)
      if (node.type == NodeType.condition) {
        bool result = _evaluateCondition(node.condition);
        String? nextId = result ? node.successNext : node.failureNext;
        if (nextId != null) {
          return _advanceTo(nextId, save: save);
        }
      }

      _currentNode = node;
      _visitedNodes.add(nodeId);
      
      // Execute onEnter actions
      if (node.onEnter != null) {
        _executeActions(node.onEnter!);
      }

      // XP Rewards
      if (save && _user != null && _token != null) {
        int xpGain = 10;
        if (node.next == null && node.type == NodeType.narrative) xpGain = 100; // Finish
        _user!.xp += xpGain;
        _api.addXp(_token!, _user!.id, xpGain).catchError((e) => debugPrint("XP sync failed: $e"));
      }

      // Analytics
      if (_token != null) {
        _api.logEvent(_token!, _user?.id, "node_entered", {
          "storyId": _currentStory!.id,
          "nodeId": nodeId,
          "timestamp": DateTime.now().toIso8601String(),
        }).catchError((e) => debugPrint("Analytics failed: $e"));
      }

      notifyListeners();
      if (save) await _saveState();
    }
  }

  void _executeActions(dynamic actions) {
    final List<String> actionList = actions is List ? List<String>.from(actions) : [actions.toString()];
    
    for (var action in actionList) {
      final parts = action.split(':');
      if (parts[0] == 'set') {
        final kv = parts[1].split('=');
        if (kv.length == 2) {
          var val = kv[1];
          if (val == 'true') {
            _variables[kv[0]] = true;
          } else if (val == 'false') {
            _variables[kv[0]] = false;
          } else {
            _variables[kv[0]] = val;
          }
        } else {
          _variables[parts[1]] = true;
        }
      }
    }
  }

  bool _evaluateCondition(String? condition) {
    if (condition == null) return true;
    
    // Simple boolean flag check for now
    if (condition.startsWith('!')) {
      return _variables[condition.substring(1)] != true;
    }
    
    // Support "key == value" if needed later, but for now simple flags
    if (condition.contains(' == ')) {
        var parts = condition.split(' == ');
        return _variables[parts[0]].toString() == parts[1].replaceAll("'", "").replaceAll('"', "");
    }

    return _variables[condition] == true;
  }

  Future<void> _saveState() async {
    if (_currentStory == null || _currentNode == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('last_story_id', _currentStory!.id);
    await prefs.setString('last_node_id', _currentNode!.id);
    await prefs.setString('last_variables', json.encode(_variables));
    
    // Sync with backend if logged in
    if (_user != null && _token != null) {
      try {
        await _api.saveProgress(_token!, _user!.id, _currentStory!.id, _currentNode!.id, _variables);
      } catch (e) {
        debugPrint("Progess sync failed: $e");
      }
    }
  }

  static Future<Map<String, dynamic>?> getLastState() async {
    final prefs = await SharedPreferences.getInstance();
    final storyId = prefs.getString('last_story_id');
    final nodeId = prefs.getString('last_node_id');
    final varsJson = prefs.getString('last_variables');
    if (storyId != null && nodeId != null) {
      return {
        'storyId': storyId, 
        'nodeId': nodeId,
        'variables': varsJson != null ? json.decode(varsJson) : null
      };
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

    bool valid = false;
    
    // 1. Valid Answers List
    if (_currentNode!.validAnswers != null) {
        valid = _currentNode!.validAnswers!.any(
          (ans) => ans.trim().toLowerCase() == input.trim().toLowerCase()
        );
    } 
    // 2. Numeric Answer
    else if (_currentNode!.numericAnswer != null) {
        valid = int.tryParse(input) == _currentNode!.numericAnswer;
    }
    // 3. String Fallback for Order (if somehow called via text)
    else if (_currentNode!.orderAnswer != null) {
        final items = input.split(',').map((e) => e.trim().toLowerCase()).toList();
        valid = listEquals(items, _currentNode!.orderAnswer!.map((e) => e.toLowerCase()).toList());
    }

    _processValidationResult(valid);
  }

  void checkOrder(List<String> userOrder) {
    if (_currentNode == null || _currentNode!.orderAnswer == null) return;
    
    final correctOrder = _currentNode!.orderAnswer!.map((e) => e.toLowerCase()).toList();
    final currentOrder = userOrder.map((e) => e.toLowerCase()).toList();
    
    bool valid = listEquals(correctOrder, currentOrder);
    _processValidationResult(valid);
  }

  void _processValidationResult(bool valid) {
    if (valid) {
      if (_currentNode!.successNext != null) {
        _advanceTo(_currentNode!.successNext!);
      }
    } else {
      if (_currentNode!.failureNext != null) {
        _advanceTo(_currentNode!.failureNext!);
      }
    }
  }

  void makeChoice(int index) {
    if (_currentNode == null || _currentNode!.type != NodeType.choice) return;
    
    final choices = _currentNode!.choices;
    if (choices != null && index < choices.length) {
      final choice = choices[index];
      if (choice.onSelect != null) {
        _executeActions(choice.onSelect!);
      }
      _advanceTo(choice.next);
    }
  }

  void next() {
    if (_currentNode?.next != null) {
      _advanceTo(_currentNode!.next!);
    }
  }
}
