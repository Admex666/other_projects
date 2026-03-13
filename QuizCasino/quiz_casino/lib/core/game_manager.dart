import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/game_data.dart';
import 'audio_manager.dart';
import 'socket_service.dart';

class GameManager extends ChangeNotifier {
  GameState currentState = GameState.waiting;
  List<Player> players = [];
  List<Player> finalPlayers = []; // Set on match_ended for the leaderboard
  late Player localPlayer;
  String _roomId = '';
  UserStats? userStats;

  bool isInitialized = false;

  // Used to trigger "You've been eliminated" popup
  bool justEliminated = false;
  bool _wasEliminatedLastFrame = false;

  // Match Rules & State from server
  int currentRound = 1;
  final int maxRounds = 7;
  final int shieldRounds = 2;
  final int questionDurationSec = 15;
  final int revealDurationSec = 5;
  int currentMinBet = 10;

  int currentTimer = 0;
  RoundResult? lastRoundResult;
  Question? currentQuestion;

  // UI Local State
  int selectedAnswerIndex = -1;
  int currentBetAmount = 10;

  Function(int placement, int pointsGained)? onMatchEnded;

  void clearJustEliminated() {
    justEliminated = false;
    _wasEliminatedLastFrame = true;
    notifyListeners();
  }

  GameManager() {
    _initAsync();
  }

  Future<void> _initAsync() async {
    await _initLocalPlayer();
    _setupSockets();
    isInitialized = true;
    notifyListeners();
  }

  Future<void> _initLocalPlayer() async {
    final prefs = await SharedPreferences.getInstance();
    
    String? storedId = prefs.getString('user_id');
    if (storedId == null) {
      storedId = "u_${DateTime.now().millisecondsSinceEpoch}";
      await prefs.setString('user_id', storedId);
    }

    String username = "Player_${storedId.substring(storedId.length - 5)}";
    
    localPlayer = Player(
      id: "temp", 
      userId: storedId, 
      username: username, 
      stack: 100
    );
    players = [localPlayer];
  }

  void _setupSockets() {
    final socketSvc = SocketService();
    // Live Render server
    socketSvc.init('https://other-projects-79dx.onrender.com');

    socketSvc.onMatchFound = (data) {
      _roomId = data['roomId'];
      debugPrint("Matched into room $_roomId");
    };

    socketSvc.onStateUpdate = (data) {
      final parsedState = _parseGameState(data['currentState']);
      
      final prevState = currentState;
      currentState = parsedState;
      currentRound = data['currentRound'] ?? 1;
      currentTimer = data['currentTimer'] ?? 0;
      currentMinBet = data['currentMinBet'] ?? 10;
      
      debugPrint("State update: $currentState, Round: $currentRound, Timer: $currentTimer");
      
      // Players
      if (data['players'] != null) {
        try {
          players = (data['players'] as List).map((p) => Player(
            id: p['id'],
            userId: p['userId'] ?? "",
            username: p['username'],
            stack: p['stack'],
            isEliminated: p['isEliminated'] ?? false,
          )).toList();
        } catch (e) {
          debugPrint("Error parsing players in state update: $e");
        }

        // Update localPlayer reference
        final found = players.where((p) => p.username == localPlayer.username);
        if (found.isNotEmpty) {
          final prev = localPlayer;
          localPlayer = found.first;
          if (!_wasEliminatedLastFrame && !prev.isEliminated && localPlayer.isEliminated) {
            justEliminated = true;
          }
        }
      }

      // Question – update on questionActive AND reveal (reveal sends the real correctAnswerIndex)
      if (data['currentQuestion'] != null && currentState != GameState.waiting) {
        final q = data['currentQuestion'];
        currentQuestion = Question(
          questionText: q['questionText'],
          answers: (q['answers'] as List).map((e) => e.toString()).toList(),
          correctAnswerIndex: q['correctAnswerIndex'] ?? -1,
        );
      } else if (currentState == GameState.waiting) {
        currentQuestion = null;
      }

      if (data['lastRoundResult'] != null) {
        final rawNetChanges = data['lastRoundResult']['netChanges'];
        Map<String, int> netChanges = {};
        if (rawNetChanges is Map) {
          rawNetChanges.forEach((k, v) {
            netChanges[k.toString()] = (v as num).toInt();
          });
        }
        
        lastRoundResult = RoundResult(
          totalPot: (data['lastRoundResult']['totalPot'] as num?)?.toInt() ?? 0,
          netChanges: netChanges
        );
      }

      // Sync local UI bet slider if minimum bet increased
      if (currentState == GameState.questionActive && prevState != GameState.questionActive) {
        selectedAnswerIndex = -1;
        currentBetAmount = currentMinBet;
        if (localPlayer.stack <= currentMinBet) {
          currentBetAmount = localPlayer.stack;
        }
      }

      // Play sounds on transition
      if (prevState != GameState.reveal && currentState == GameState.reveal) {
        AudioManager().playCash();
      }

      notifyListeners();
    };

    socketSvc.onTick = (time) {
      currentTimer = time;
      if (currentState == GameState.questionActive && currentTimer <= 3 && currentTimer > 0) {
        AudioManager().playTick();
      }
      notifyListeners();
    };

    socketSvc.onMatchEnded = (data) {
      debugPrint("Match ended event received");
      currentState = GameState.result;

      try {
        List<dynamic> resList = [];
        if (data is List) {
          resList = data;
        } else if (data is Map && data['players'] != null) {
          resList = data['players'] as List<dynamic>;
        }

        final parsed = resList.map((p) {
          if (p is Map) {
            return Player(
              id: p['id']?.toString() ?? "",
              userId: p['userId']?.toString() ?? "",
              username: p['username']?.toString() ?? "Unknown",
              stack: (p['stack'] as num?)?.toInt() ?? 0,
              isEliminated: p['isEliminated'] ?? false,
            );
          }
          return Player(id: "err", userId: "", username: "Error", stack: 0);
        }).toList();

        finalPlayers = parsed;
        players = parsed;
      } catch (e) {
        debugPrint("Error parsing match ended results: $e");
        // Use current players if parsing fails
        finalPlayers = players;
      }

      // Determine my placement (server sends list sorted by rank)
      int rank = finalPlayers.indexWhere((p) => p.username == localPlayer.username) + 1;
      if (rank == 0) rank = finalPlayers.length > 0 ? finalPlayers.length : 4; 

      final localInList = finalPlayers.firstWhere(
        (p) => p.username == localPlayer.username,
        orElse: () => localPlayer,
      );
      int coinsChange = localInList.stack - 100;

      _wasEliminatedLastFrame = false;
      justEliminated = false;

      if (onMatchEnded != null) {
        onMatchEnded!(rank, coinsChange);
      }
      notifyListeners();
    };

    socketSvc.onUserStats = (data) {
      userStats = UserStats.fromJson(data);
      notifyListeners();
    };
  }

  GameState _parseGameState(String stateStr) {
    switch (stateStr) {
      case 'questionActive': return GameState.questionActive;
      case 'reveal': return GameState.reveal;
      case 'result': return GameState.result;
      default: return GameState.waiting;
    }
  }

  void startNewMatch(Function(int placement, int pointsGained)? onEnd) {
    onMatchEnded = onEnd;
    currentState = GameState.waiting;
    currentQuestion = null;
    notifyListeners();

    SocketService().joinQueue(localPlayer.username, localPlayer.userId);
  }

  void selectAnswer(int index) {
    if (currentState != GameState.questionActive) return;
    selectedAnswerIndex = index;
    notifyListeners();
    
    // Send to server
    if (_roomId.isNotEmpty) {
      SocketService().selectAnswer(_roomId, index);
    }
  }

  void updateBet(double value) {
    if (currentState != GameState.questionActive) return;
    int amount = value.toInt();
    if (amount < currentMinBet && localPlayer.stack > currentMinBet) {
      amount = currentMinBet;
    }
    currentBetAmount = amount;
    notifyListeners();
    
    // Send to server
    if (_roomId.isNotEmpty) {
      SocketService().placeBet(_roomId, currentBetAmount);
    }
  }

  @override
  void dispose() {
    SocketService().dispose();
    super.dispose();
  }
}
