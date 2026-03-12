import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../models/game_data.dart';
import '../theme.dart';
import 'widgets/chunky_button.dart';

class MatchScreen extends StatelessWidget {
  const MatchScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
          child: Consumer<GameManager>(
            builder: (context, game, child) {
              final isQuestionState = game.currentState == GameState.questionActive;
              final isRevealState = game.currentState == GameState.reveal;
              final question = game.roundController.currentQuestion;

              if (question == null) {
                return const Center(child: CircularProgressIndicator());
              }

              return Column(
                children: [
                  // --- TOP: TIMER & QUESTION ---
                  _buildQuestionHeader(game, question, isQuestionState),
                  
                  const SizedBox(height: 20),
                  
                  // --- ELIMINATIONS / PLAYERS ---
                  _buildPlayerTracker(game, isRevealState),

                  if (isRevealState && game.lastRoundResult != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: Text("POT: ${game.lastRoundResult!.totalPot}", style: const TextStyle(color: AppTheme.goldCoin, fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 2))
                          .animate(key: ValueKey(game.currentRound)).scale(curve: Curves.elasticOut, duration: 800.ms).shimmer(duration: 2.seconds),
                    ),

                  const SizedBox(height: 20),

                  // --- MIDDLE: ANSWERS ---
                  Expanded(
                    child: ListView.separated(
                      physics: const BouncingScrollPhysics(),
                      itemCount: question.answers.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        return _buildAnswerButton(context, game, index, question.answers[index], isRevealState, question.correctAnswerIndex)
                            .animate().slideX(begin: 0.5, end: 0, delay: (100 * index).ms, duration: 400.ms, curve: Curves.easeOutQuad).fadeIn();
                      },
                    ),
                  ),

                  const SizedBox(height: 12),
                  // --- BOTTOM: BET SLIDER & STACK ---
                  _buildBetPanel(context, game, isQuestionState, isRevealState)
                      .animate().slideY(begin: 0.5, end: 0, duration: 600.ms, curve: Curves.easeOutQuad).fadeIn(),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildQuestionHeader(GameManager game, Question question, bool isQuestionState) {
    // Determine timer color
    Color timerColor = AppTheme.neonCyan;
    if (isQuestionState && game.currentTimer <= 3) {
      timerColor = AppTheme.dangerRed;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.panelGlassColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          if (game.currentRound >= 3 && game.currentRound <= 4 && isQuestionState)
            Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: BoxDecoration(
                color: AppTheme.dangerRed.withOpacity(0.2),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.dangerRed)
              ),
              child: const Text(
                "🚨 ELIMINATIONS & ALL-INS ENABLED! 🚨",
                style: TextStyle(color: AppTheme.dangerRed, fontWeight: FontWeight.bold, fontSize: 13),
                textAlign: TextAlign.center,
              ),
            ).animate(onPlay: (c) => c.repeat(reverse: true)).shimmer(color: Colors.white, duration: 1000.ms),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                game.currentState == GameState.reveal ? "RESULT" : "PLACE BET",
                style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.bold),
              ),
              Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    height: 40,
                    width: 40,
                    child: CircularProgressIndicator(
                      value: game.currentTimer / (isQuestionState ? game.questionDurationSec : game.revealDurationSec),
                      color: timerColor,
                      backgroundColor: Colors.white10,
                      strokeWidth: 4,
                    ),
                  ),
                  Text(
                    '${game.currentTimer}',
                    style: TextStyle(color: timerColor, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ],
          ),
          Text(
            "ROUND ${game.currentRound} / ${game.maxRounds}",
            style: const TextStyle(color: AppTheme.purpleGlow, fontWeight: FontWeight.bold, letterSpacing: 2),
          ).animate().shimmer(color: Colors.white, duration: 2000.ms),
          const SizedBox(height: 12),
          Text(
            question.questionText,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
            textAlign: TextAlign.center,
          ).animate(key: ValueKey(question.questionText)).slideY(begin: -0.2, end: 0, duration: 400.ms).fadeIn(),
        ],
      ),
    ).animate().scale(curve: Curves.easeOutBack, duration: 500.ms).fadeIn();
  }

  Widget _buildPlayerTracker(GameManager game, bool isRevealState) {
    List<Player> activePlayers = game.players.where((p) => !p.isEliminated).toList();
    activePlayers.sort((a,b) => b.stack.compareTo(a.stack));
    int toEliminate = game.currentRound <= game.shieldRounds ? 0 : (activePlayers.length * 0.2).ceil();

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: game.players.map((p) {
        bool isLocal = p.id == game.localPlayer.id;

        int rank = 0;
        bool isKieso = false;
        bool isVeszelyben = false;
        if (!p.isEliminated) {
          rank = activePlayers.indexWhere((ap) => ap.id == p.id) + 1;
          isKieso = game.currentRound > game.shieldRounds && rank > activePlayers.length - toEliminate;
          isVeszelyben = game.currentRound > game.shieldRounds && rank == activePlayers.length - toEliminate;
        }

        Color stackColor = Colors.white;
        if (isKieso) stackColor = AppTheme.dangerRed;
        else if (isVeszelyben) stackColor = AppTheme.goldCoin;

        int netChange = 0;
        if (isRevealState && game.lastRoundResult != null) {
          netChange = game.lastRoundResult!.netChanges[p.id] ?? 0;
        }

        return Opacity(
          opacity: p.isEliminated ? 0.3 : 1.0,
          child: Column(
            children: [
              if (rank > 0)
                Text("#$rank", style: TextStyle(color: stackColor, fontSize: 13, fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              Stack(
                clipBehavior: Clip.none,
                alignment: Alignment.center,
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: isKieso ? AppTheme.dangerRed : (isLocal ? AppTheme.goldCoin : AppTheme.panelGlassColor),
                    child: Icon(p.isEliminated ? Icons.close : Icons.person, size: 20, color: isKieso ? Colors.white : (isLocal ? Colors.black : Colors.white)),
                  ),
                  if (netChange != 0 && isRevealState)
                    Positioned(
                      top: netChange > 0 ? -25 : null,
                      bottom: netChange < 0 ? -25 : null,
                      child: Text(
                        netChange > 0 ? "+$netChange" : "$netChange",
                        style: TextStyle(
                            color: netChange > 0 ? AppTheme.successGreen : AppTheme.dangerRed,
                            fontWeight: FontWeight.w900,
                            fontSize: 16,
                            shadows: const [Shadow(color: Colors.black, blurRadius: 4)]
                        ),
                      ).animate().slideY(begin: netChange > 0 ? 1.0 : -1.0, end: netChange > 0 ? -0.5 : 0.5, duration: 2.seconds).fadeOut(delay: 1500.ms),
                    ),
                ]
              ),
              const SizedBox(height: 4),
              Text(
                p.isEliminated ? "OUT" : "${p.stack}",
                style: TextStyle(
                  fontSize: 14,
                  color: p.isEliminated ? AppTheme.dangerRed : stackColor,
                  fontWeight: FontWeight.bold,
                ),
              )
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildAnswerButton(BuildContext context, GameManager game, int index, String text, bool isRevealState, int correctIndex) {
    final isSelected = game.selectedAnswerIndex == index;
    
    // Determine Color based on state
    Color baseColor = const Color(0xFF2A2A4A); // Solid chunky dark element
    Color shadowColor = const Color(0xFF151525);
    Color? borderColor;
    Color textColor = Colors.white;
    
    if (isRevealState) {
      if (index == correctIndex) {
        baseColor = AppTheme.successGreen;
        shadowColor = const Color(0xFF1C9E31);
        textColor = Colors.black;
      } else if (isSelected && index != correctIndex) {
        baseColor = AppTheme.dangerRed;
        shadowColor = const Color(0xFF9E1C1C);
      }
    } else if (isSelected) {
      baseColor = AppTheme.neonCyan;
      shadowColor = const Color(0xFF009989);
      textColor = Colors.black;
    }

    return ChunkyButton(
      onTap: () => game.selectAnswer(index),
      baseColor: baseColor,
      shadowColor: shadowColor,
      isSelected: isSelected && !isRevealState,
      borderColor: borderColor,
      elevation: isRevealState ? 2.0 : 6.0,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      child: Center(
        child: Text(
          text,
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: textColor),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  Widget _buildBetPanel(BuildContext context, GameManager game, bool isQuestionState, bool isRevealState) {
    int minBet = game.currentMinBet;
    double limitMultiplier = game.currentRound <= game.shieldRounds ? 0.4 : 1.0;
    int maxBet = (game.localPlayer.stack * limitMultiplier).floor();
    
    bool isForcedAllIn = game.localPlayer.stack <= minBet;
    if (isForcedAllIn) {
      maxBet = game.localPlayer.stack;
      minBet = game.localPlayer.stack;
    } else {
      if (maxBet < minBet) maxBet = minBet;
    }
    
    double sliderVal = game.currentBetAmount.toDouble();
    if (sliderVal < minBet) sliderVal = minBet.toDouble();
    if (sliderVal > maxBet) sliderVal = maxBet.toDouble();

    return AnimatedOpacity(
      duration: const Duration(milliseconds: 300),
      opacity: isQuestionState ? 1.0 : 0.5,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: AppTheme.backgroundDarkNavy,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppTheme.purpleGlow.withOpacity(0.5), width: 2),
        ),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(isForcedAllIn ? "ALL-IN!" : "CURRENT BET (MIN $minBet)", style: TextStyle(color: isForcedAllIn ? AppTheme.dangerRed : Colors.white54, fontSize: 12, fontWeight: FontWeight.bold)),
                Text(
                  "${sliderVal.toInt()}",
                  style: const TextStyle(color: AppTheme.neonCyan, fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            IgnorePointer(
              ignoring: !isQuestionState || isForcedAllIn || minBet >= maxBet,
              child: Opacity(
                opacity: isForcedAllIn ? 0.5 : 1.0,
                child: Slider(
                  value: sliderVal,
                  min: minBet.toDouble(),
                  max: maxBet > minBet ? maxBet.toDouble() : minBet.toDouble() + 1,
                  divisions: maxBet > minBet ? (maxBet - minBet) : 1,
                  onChanged: (isForcedAllIn || minBet >= maxBet) ? null : (val) => game.updateBet(val),
                ),
              ),
            ),
            const Divider(color: Colors.white10, height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("YOUR STACK", style: TextStyle(color: Colors.white54, fontSize: 12)),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 400),
                  transitionBuilder: (Widget child, Animation<double> animation) {
                    return ScaleTransition(scale: animation, child: child);
                  },
                  child: Text(
                    "${game.localPlayer.stack}",
                    key: ValueKey<int>(game.localPlayer.stack),
                    style: const TextStyle(color: AppTheme.goldCoin, fontSize: 28, fontWeight: FontWeight.w900),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
