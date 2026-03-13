import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'socket_service.dart';
import '../models/game_data.dart';

class GameManager with ChangeNotifier {
  // Game State
  GameState currentState = GameState.waiting;
  Question? currentQuestion;
  int tickCount = 0;
  List<Player> players = [];
  Player? _winner;
  RoundResult? lastRoundResult;
  bool justEliminated = false;
  List<Player> finalPlayers = [];

  // Game specific state
  int currentRound = 1;
  int maxRounds = 10;
  int shieldRounds = 3;
  int? selectedAnswerIndex;
  int currentMinBet = 10;
  int currentBetAmount = 10;
  int currentTimer = 0;
  int questionDurationSec = 15;
  int revealDurationSec = 5;

  // User State
  UserStats? _userStats;
  bool _isInitialized = false;
  bool _isLoggedIn = false;
  bool _isAuthLoading = false;
  String? _authError;

  GameManager() {
    _init();
  }

  bool get isInitialized => _isInitialized;
  bool get isLoggedIn => _isLoggedIn;
  UserStats? get userStats => _userStats;
  String? get authError => _authError;
  bool get isAuthLoading => _isAuthLoading;

  // Local device player representation
  Player get localPlayer {
    final p = players.firstWhere(
      (p) => p.username == _userStats?.username,
      orElse: () => Player(
        id: "local",
        userId: _userStats?.username ?? "Guest",
        username: _userStats?.username ?? "Guest",
        stack: 100,
      ),
    );
    return p;
  }

  bool get isMatchmaking => currentState == GameState.waiting && currentQuestion == null;

  Future<void> _init() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUsername = prefs.getString('saved_username');
    final savedPassword = prefs.getString('saved_password');

    SocketService().init("https://quiz-casino.onrender.com");
    _setupSockets();

    if (savedUsername != null && savedPassword != null) {
      // Try auto-login
      SocketService().login(savedUsername, savedPassword);
    } else {
      _isInitialized = true;
      notifyListeners();
    }
  }

  void _setupSockets() {
    final socket = SocketService();
    
    socket.onAuthSuccess((stats) async {
      debugPrint('DEBUG: Received auth_success for ${stats.username}');
      _userStats = stats;
      _isLoggedIn = true;
      _isInitialized = true;
      _isAuthLoading = false;
      _authError = null;
      notifyListeners();
    });

    socket.onAuthError((error) {
      debugPrint('DEBUG: Received auth_error: $error');
      _authError = error;
      _isInitialized = true;
      _isAuthLoading = false;
      notifyListeners();
    });

    socket.onUserStats((stats) {
      _userStats = stats;
      notifyListeners();
    });

    socket.onMatchFound = (data) {
      currentState = GameState.waiting;
      currentQuestion = null;
      notifyListeners();
    };

    socket.onStateUpdate = (data) {
      _parseState(data);
      notifyListeners();
    };

    socket.onTick = (count) {
      tickCount = count;
      currentTimer = count; // Ensure currentTimer is updated
      notifyListeners();
    };

    socket.onMatchEnded = (data) {
      _parseMatchEnd(data);
      notifyListeners();
    };
  }

  void login(String username, String password) async {
    _authError = null;
    _isAuthLoading = true;
    notifyListeners();
    SocketService().login(username, password);
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('saved_username', username);
    await prefs.setString('saved_password', password);
  }

  void register(String username, String password) async {
    _authError = null;
    _isAuthLoading = true;
    notifyListeners();
    SocketService().register(username, password);
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('saved_username', username);
    await prefs.setString('saved_password', password);
  }

  void logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('saved_username');
    await prefs.remove('saved_password');
    _isLoggedIn = false;
    _userStats = null;
    notifyListeners();
  }

  void startNewMatch([int? betAmount]) {
    if (_userStats == null) return;
    currentState = GameState.waiting;
    currentQuestion = null;
    players = [];
    _winner = null;
    lastRoundResult = null;
    justEliminated = false;
    finalPlayers = [];
    currentRound = 1;
    selectedAnswerIndex = null;
    
    SocketService().joinQueue(_userStats!.username, _userStats!.username);
  }

  void cancelMatchmaking() {
    SocketService().leaveQueue();
  }

  void placeBet(int amount) {
    final roomId = _getRoomIdFromState();
    if (roomId != null) {
      SocketService().placeBet(roomId, amount);
    }
  }

  void selectAnswer(int index) {
    if (selectedAnswerIndex != null) return; // Only allow one selection per round
    
    final roomId = _getRoomIdFromState();
    if (roomId != null) {
      selectedAnswerIndex = index;
      SocketService().selectAnswer(roomId, index);
      // Automatically place the current bet amount when answer is selected
      SocketService().placeBet(roomId, currentBetAmount);
      notifyListeners();
    }
  }

  void clearJustEliminated() {
    justEliminated = false;
    notifyListeners();
  }

  void updateBet(double value) {
    currentBetAmount = value.toInt();
    notifyListeners();
  }

  String? _getRoomIdFromState() {
    // This is a bit of a hack since we don't store roomId directly in state yet
    // but the server knows which room the client is in.
    return "current"; // The server logic handles "current" for the socket's active room
  }

  void _parseState(Map<String, dynamic> data) {
    final stateStr = data['state'];
    switch (stateStr) {
      case 'waiting': currentState = GameState.waiting; break;
      case 'questionActive': currentState = GameState.questionActive; break;
      case 'reveal': currentState = GameState.reveal; break;
      case 'result': currentState = GameState.result; break;
    }

    currentRound = data['currentRound'] ?? 1;
    maxRounds = data['maxRounds'] ?? 10;
    shieldRounds = data['shieldRounds'] ?? 3;
    currentMinBet = data['minBet'] ?? 10;
    questionDurationSec = data['questionDuration'] ?? 15;
    revealDurationSec = data['revealDuration'] ?? 5;

    if (currentState == GameState.questionActive && selectedAnswerIndex == null) {
      currentBetAmount = currentMinBet;
    }

    if (currentState == GameState.waiting) {
       selectedAnswerIndex = null;
    }

    if (data['question'] != null) {
      final qData = data['question'];
      currentQuestion = Question(
        questionText: qData['text'],
        answers: List<String>.from(qData['answers']),
        correctAnswerIndex: qData['correctIndex'],
      );
    }

    if (data['players'] != null) {
      final wasEliminated = localPlayer.isEliminated;
      players = (data['players'] as List).map((p) => Player(
        id: p['id'],
        userId: p['userId'],
        username: p['username'],
        stack: p['stack'],
        isEliminated: p['isEliminated'],
      )).toList();
      
      if (!wasEliminated && localPlayer.isEliminated) {
        justEliminated = true;
      }
    }

    if (data['lastRoundResult'] != null) {
      final res = data['lastRoundResult'];
      lastRoundResult = RoundResult(
        totalPot: res['totalPot'],
        netChanges: Map<String, int>.from(res['netChanges']),
      );
    }
  }

  void _parseMatchEnd(Map<String, dynamic> data) {
    currentState = GameState.result;
    if (data['players'] != null) {
      finalPlayers = (data['players'] as List).map((p) => Player(
        id: p['id'],
        userId: p['userId'],
        username: p['username'],
        stack: p['stack'],
        isEliminated: p['isEliminated'],
      )).toList();
    }
  }
}
