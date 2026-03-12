import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:html_unescape/html_unescape.dart';

import '../models/game_data.dart';
import 'round_controller.dart';
import 'audio_manager.dart';

class GameManager extends ChangeNotifier {
  final RoundController roundController = RoundController();

  GameState currentState = GameState.waiting;
  List<Player> players = [];
  late Player localPlayer;
  
  // Match Rules
  int currentRound = 1;
  final int maxRounds = 7;
  final int shieldRounds = 2; // No elimination in round 1 and 2
  int get currentMinBet => currentRound <= shieldRounds ? 10 : (currentRound - shieldRounds) * 10 + 10;
  Function(int placement, int pointsGained)? onMatchEnded;

  // Timer settings
  final int questionDurationSec = 15;
  final int revealDurationSec = 5;
  int currentTimer = 0;
  Timer? _ticker;
  
  RoundResult? lastRoundResult;

  // Questions
  List<Question> _fetchedQuestions = [];
  int _currentQuestionIndex = 0;

  // UI State
  int selectedAnswerIndex = -1;
  int currentBetAmount = 10;

  GameManager() {
    _initializeMockData();
    _initGame();
  }

  Future<void> _initGame() async {
    await _fetchTriviaQuestions();
    _changeState(GameState.questionActive);
  }

  Future<void> _fetchTriviaQuestions() async {
    try {
      final response = await http.get(Uri.parse('https://opentdb.com/api.php?amount=10'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final results = data['results'] as List;
        final unescape = HtmlUnescape();

        List<Question> newQuestions = [];
        for (var item in results) {
          String qText = unescape.convert(item['question']);
          String correct = unescape.convert(item['correct_answer']);
          List<String> incorrects = (item['incorrect_answers'] as List).map((e) => unescape.convert(e.toString())).toList();

          List<String> allAnswers = List.from(incorrects)..add(correct);
          allAnswers.shuffle(Random());
          
          int correctIndex = allAnswers.indexOf(correct);

          newQuestions.add(Question(
            questionText: qText,
            answers: allAnswers,
            correctAnswerIndex: correctIndex,
          ));
        }
        
        if (newQuestions.isNotEmpty) {
          _fetchedQuestions = newQuestions;
          return;
        }
      }
    } catch (e) {
      debugPrint("Error fetching trivia: $e");
    }

    // Fallback if network fails
    _fetchedQuestions = [
      Question(questionText: "Which planet is known as the Red Planet?", answers: ["Earth", "Mars", "Jupiter", "Venus"], correctAnswerIndex: 1),
      Question(questionText: "What is the capital of France?", answers: ["Berlin", "Madrid", "Paris", "Rome"], correctAnswerIndex: 2),
      Question(questionText: "What is 5 + 7?", answers: ["10", "11", "12", "13"], correctAnswerIndex: 2)
    ];
  }

  void _initializeMockData() {
    players.clear();
    localPlayer = Player(id: "p_local", username: "You", stack: 100);
    players.add(localPlayer);
    players.add(Player(id: "p_bot1", username: "Bot Anna", stack: 100));
    players.add(Player(id: "p_bot2", username: "Bot Ben", stack: 100));
    players.add(Player(id: "p_bot3", username: "Bot Kai", stack: 100));
  }

  void startNewMatch(Function(int placement, int pointsGained) onEnd) async {
    onMatchEnded = onEnd;
    _initializeMockData();
    currentRound = 1;
    _currentQuestionIndex = 0;
    currentState = GameState.waiting;
    roundController.clearQuestion();
    notifyListeners();

    await _fetchTriviaQuestions();
    _changeState(GameState.questionActive);
  }

  void _changeState(GameState newState) {
    currentState = newState;
    _ticker?.cancel();

    if (currentState == GameState.questionActive) {
      if (_currentQuestionIndex >= _fetchedQuestions.length) {
        _currentQuestionIndex = 0;
      }
      final q = _fetchedQuestions[_currentQuestionIndex++];
      roundController.startRound(q);
      _simulateBotBets(q);
      
      selectedAnswerIndex = -1;
      currentBetAmount = currentMinBet;
      if (localPlayer.stack <= currentMinBet) {
        currentBetAmount = localPlayer.stack;
      }
      currentTimer = questionDurationSec;
      
      _ticker = Timer.periodic(const Duration(seconds: 1), _tick);
    } 
    else if (currentState == GameState.reveal) {
      // Register local player bet automatically when time runs out
      roundController.registerBet(Bet(
        playerId: localPlayer.id,
        amount: currentBetAmount,
        answerIndex: selectedAnswerIndex,
      ));

      lastRoundResult = roundController.processRoundResults(players);
      currentTimer = revealDurationSec;
      _ticker = Timer.periodic(const Duration(seconds: 1), _tick);
      
      AudioManager().playCash();
    }

    notifyListeners();
  }

  void _tick(Timer timer) {
    if (currentTimer > 0) {
      currentTimer--;
      if (currentState == GameState.questionActive && currentTimer <= 3 && currentTimer > 0) {
        AudioManager().playTick();
      }
      notifyListeners();
    } else {
      timer.cancel();
      if (currentState == GameState.questionActive) {
        _changeState(GameState.reveal);
      } else if (currentState == GameState.reveal) {
        _handleRoundEnd();
      }
    }
  }

  void _handleRoundEnd() {
    _processEliminations();

    // Check if match is over (Local player eliminated OR reached max rounds)
    if (localPlayer.isEliminated) {
      _endMatch();
      return;
    }

    // Check if player is the last one standing
    int activePlayers = players.where((p) => !p.isEliminated).length;
    if (activePlayers <= 1) {
      _endMatch();
      return;
    }

    if (currentRound >= maxRounds) {
      _endMatch();
      return;
    }

    // Next round
    currentRound++;
    _changeState(GameState.questionActive);
  }

  void _processEliminations() {
    if (currentRound <= shieldRounds) return; // No eliminations

    // Anyone with <= 0 stack is eliminated
    for (var player in players) {
      if (player.stack <= 0) {
        player.isEliminated = true;
      }
    }

    // Eliminate bottom 20% (for 4 players, that's 1 player)
    int activePlayers = players.where((p) => !p.isEliminated).length;
    if (activePlayers > 1) {
      int toEliminate = (activePlayers * 0.2).ceil();
      if (toEliminate > 0) {
        var activeList = players.where((p) => !p.isEliminated).toList();
        activeList.sort((a, b) => a.stack.compareTo(b.stack));
        
        for (int i = 0; i < toEliminate; i++) {
          activeList[i].isEliminated = true;
        }
      }
    }
  }

  void _endMatch() {
    currentState = GameState.result;
    
    // Sort final players by stack (including eliminated ones but preferring alive)
    players.sort((a, b) {
      if (a.isEliminated && !b.isEliminated) return 1;
      if (!a.isEliminated && b.isEliminated) return -1;
      return b.stack.compareTo(a.stack);
    });

    int placement = players.indexWhere((p) => p.id == localPlayer.id) + 1;
    int pointsGained = (players.length - placement + 1) * 100 - 150; // simple mock calc

    if (placement == 1) {
      AudioManager().playWin();
    } else {
      AudioManager().playLose();
    }

    if (onMatchEnded != null) {
      onMatchEnded!(placement, pointsGained);
    }
    notifyListeners();
  }

  void selectAnswer(int index) {
    if (currentState != GameState.questionActive) return;
    selectedAnswerIndex = index;
    notifyListeners();
  }

  void updateBet(double value) {
    if (currentState != GameState.questionActive) return;
    int amount = value.toInt();
    if (amount < currentMinBet && localPlayer.stack > currentMinBet) {
      amount = currentMinBet;
    }
    currentBetAmount = amount;
    notifyListeners();
  }

  void _simulateBotBets(Question q) {
    final rand = Random();
    for (var player in players) {
      if (player.id == localPlayer.id || player.isEliminated) continue;

      double limitMultiplier = currentRound <= shieldRounds ? 0.4 : 1.0;
      int maxBet = min((player.stack * limitMultiplier).floor(), player.stack);
      
      int botBet;
      if (player.stack <= currentMinBet) {
        botBet = player.stack; // Forced all-in due to min bet
      } else {
        if (maxBet < currentMinBet) {
          maxBet = currentMinBet;
        }
        botBet = maxBet > currentMinBet ? rand.nextInt(maxBet - currentMinBet) + currentMinBet : maxBet;
      }
      
      // 60% chance to be right
      bool isCorrect = rand.nextDouble() > 0.4;
      int answerIndex = isCorrect ? q.correctAnswerIndex : ((q.correctAnswerIndex + 1) % 4);

      roundController.registerBet(Bet(
        playerId: player.id,
        amount: botBet,
        answerIndex: answerIndex,
      ));
    }
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }
}
