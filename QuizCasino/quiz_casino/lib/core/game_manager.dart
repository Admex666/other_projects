import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'socket_service.dart';
import 'constants.dart';
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
  String? currentRoomId;

  // Leaderboard State
  List<UserStats> leaderboardPlayers = [];
  bool isLeaderboardLoading = false;
  String currentLeaderboardLeague = "bronze";

  // Guild State
  Guild? currentGuild;
  bool isGuildLoading = false;
  List<Guild> searchedGuilds = [];
  
  // Shop State
  List<ShopItem> shopCatalog = [];
  bool isShopLoading = false;

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
  UserStats? selectedPlayerProfile;
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

    SocketService().init(AppConstants.serverUrl);
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

    socket.onLeaderboardUpdate = (league, players) {
      currentLeaderboardLeague = league;
      leaderboardPlayers = players;
      isLeaderboardLoading = false;
      notifyListeners();
    };

    socket.socket.on('guild_update', (data) {
      currentGuild = Guild.fromJson(data);
      isGuildLoading = false;
      notifyListeners();
    });

    socket.socket.on('guild_search_results', (data) {
      searchedGuilds = (data as List).map((g) => Guild.fromJson(g)).toList();
      isGuildLoading = false;
      notifyListeners();
    });

    socket.socket.on('join_request_sent', (data) {
      isGuildLoading = false;
      // We could show a toast here via a specialized event or state
      notifyListeners();
    });

    socket.onPlayerInfo = (stats) {
      selectedPlayerProfile = stats;
      notifyListeners();
    };

    socket.onShopCatalog = (data) {
      shopCatalog = data.map((i) => ShopItem.fromJson(i)).toList();
      isShopLoading = false;
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
    // Removed the (selectedAnswerIndex != null) check to allow switching answers
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
    
    // If we've already selected an answer, update the bet on server too
    if (selectedAnswerIndex != null && currentState == GameState.questionActive) {
      final roomId = _getRoomIdFromState();
      if (roomId != null) {
        SocketService().placeBet(roomId, currentBetAmount);
      }
    }
    
    notifyListeners();
  }

  void fetchLeaderboard(String league) {
    isLeaderboardLoading = true;
    currentLeaderboardLeague = league;
    notifyListeners();
    SocketService().getLeaderboard(league);
  }

  void fetchMyGuild() {
    if (_userStats?.guildTag != null) {
      isGuildLoading = true;
      notifyListeners();
      SocketService().getGuild(_userStats!.guildTag!);
    }
  }

  void createGuild(String name, String tag) {
    if (_userStats == null) return;
    isGuildLoading = true;
    notifyListeners();
    SocketService().createGuild(_userStats!.username, name, tag);
  }

  void searchGuilds(String? query) {
    isGuildLoading = true;
    notifyListeners();
    SocketService().searchGuilds(query);
  }

  void requestToJoin(String guildTag) {
    if (_userStats == null) return;
    isGuildLoading = true;
    notifyListeners();
    SocketService().requestToJoin(_userStats!.username, guildTag);
  }

  void handleJoinRequest(String applicantUsername, bool accept) {
    if (_userStats == null || currentGuild == null) return;
    SocketService().handleJoinRequest(
      _userStats!.username,
      currentGuild!.tag,
      applicantUsername,
      accept,
    );
  }

  void updateGuildSettings(bool isPublic) {
    if (_userStats == null || currentGuild == null) return;
    SocketService().updateGuildSettings(
      _userStats!.username,
      currentGuild!.tag,
      isPublic,
    );
  }

  void fetchPlayerInfo(String username) {
    selectedPlayerProfile = null; // Clear old one
    notifyListeners();
    SocketService().getPlayerInfo(username);
  }

  void leaveGuild() {
    if (_userStats == null || currentGuild == null) return;
    SocketService().leaveGuild(_userStats!.username, currentGuild!.tag);
  }

  void kickMember(String targetUsername) {
    if (_userStats == null || currentGuild == null) return;
    SocketService().kickMember(_userStats!.username, currentGuild!.tag, targetUsername);
  }

  void deleteGuild() {
    if (_userStats == null || currentGuild == null) return;
    SocketService().deleteGuild(_userStats!.username, currentGuild!.tag);
  }

  void fetchShopCatalog() {
    isShopLoading = true;
    notifyListeners();
    SocketService().getShopCatalog();
  }

  void purchaseItem(String itemId) {
    if (_userStats == null) return;
    SocketService().purchaseItem(_userStats!.username, itemId);
  }

  void equipItem(String itemId) {
    if (_userStats == null) return;
    SocketService().equipItem(_userStats!.username, itemId);
  }

  String? _getRoomIdFromState() {
    return currentRoomId ?? "current";
  }

  void _parseState(Map<String, dynamic> data) {
    // Backend sends 'currentState' as a number (enum index) or string
    // Let's handle both or check how it's serialized. 
    // Usually NestJS/Socket.io sends numbers for enums unless decorated.
    final dynamic rawState = data['currentState'] ?? data['state'];
    
    // Convert to GameState enum
    if (rawState is int) {
      if (rawState >= 0 && rawState < GameState.values.length) {
        currentState = GameState.values[rawState];
      }
    } else if (rawState is String) {
      switch (rawState) {
        case 'waiting': currentState = GameState.waiting; break;
        case 'questionActive': currentState = GameState.questionActive; break;
        case 'reveal': currentState = GameState.reveal; break;
        case 'result': currentState = GameState.result; break;
      }
    }

    currentRound = data['currentRound'] ?? 1;
    maxRounds = data['maxRounds'] ?? 7;
    shieldRounds = data['shieldRounds'] ?? 2;
    currentMinBet = data['currentMinBet'] ?? data['minBet'] ?? 10;
    questionDurationSec = data['questionDuration'] ?? 15;
    revealDurationSec = data['revealDuration'] ?? 5;
    currentTimer = data['currentTimer'] ?? 0;

    if (currentState == GameState.questionActive && selectedAnswerIndex == null) {
      // Don't overwrite if we already have a bet amount (slider input)
    }

    if (currentState == GameState.waiting) {
       selectedAnswerIndex = null;
    }

    currentRoomId = data['roomId'];

    if (data['currentQuestion'] != null || data['question'] != null) {
      final qData = data['currentQuestion'] ?? data['question'];
      final newQuestionText = qData['questionText'] ?? qData['text'];
      
      // If question changed, reset selection
      if (currentQuestion?.questionText != newQuestionText) {
        selectedAnswerIndex = null;
        currentBetAmount = currentMinBet;
      }

      currentQuestion = Question(
        questionText: newQuestionText,
        answers: List<String>.from(qData['answers']),
        correctAnswerIndex: qData['correctAnswerIndex'] ?? qData['correctIndex'],
      );
    }

    if (data['players'] != null) {
      final wasEliminated = localPlayer.isEliminated;
      players = (data['players'] as List).map((p) => Player(
        id: p['id'],
        userId: p['userId'] ?? p['id'], // Fallback to p.id if userId missing
        username: p['username'] ?? "Player",
        stack: p['stack'],
        isEliminated: p['isEliminated'],
        equippedSkin: p['equippedSkin'] ?? "default",
        equippedTrail: p['equippedTrail'] ?? "none",
        equippedAnimation: p['equippedAnimation'] ?? "none",
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

  void _parseMatchEnd(dynamic data) {
    currentState = GameState.result;
    List<dynamic> playerList = [];
    if (data is List) {
      playerList = data;
    } else if (data is Map && data['players'] != null) {
      playerList = data['players'];
    }

    finalPlayers = playerList.map((p) => Player(
      id: p['id'],
      userId: p['userId'] ?? p['id'],
      username: p['username'] ?? "Player",
      stack: p['stack'],
      isEliminated: p['isEliminated'],
    )).toList();
  }
}
