import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../models/game_data.dart';
import '../theme.dart';
import 'match_result_screen.dart';
import 'widgets/chunky_button.dart';
import 'widgets/matchmaking_overlay.dart';

class MatchScreen extends StatefulWidget {
  const MatchScreen({super.key});

  @override
  State<MatchScreen> createState() => _MatchScreenState();
}

class _MatchScreenState extends State<MatchScreen> {
  bool _didNavigateResult = false;

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

              // Navigate to result screen when match ends
              if (game.currentState == GameState.result && !_didNavigateResult) {
                _didNavigateResult = true;
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  if (!mounted) return;
                  final fp = game.finalPlayers;
                  
                  int rank = 4;
                  int chipsRemaining = game.localPlayer.stack;
                  final myName = game.userStats?.username ?? game.localPlayer.username;

                  if (fp.isNotEmpty) {
                    final idx = fp.indexWhere((p) => p.username == myName);
                    if (idx >= 0) {
                      rank = idx + 1;
                      chipsRemaining = fp[idx].stack;
                    } else {
                      // Fallback if not found in list (shouldn't happen)
                      rank = game.localPlayer.isEliminated ? fp.length : 1;
                      chipsRemaining = game.localPlayer.stack;
                    }
                  } else {
                    // fp is empty
                    rank = game.localPlayer.isEliminated ? 4 : 1;
                    chipsRemaining = game.localPlayer.stack;
                  }

                  debugPrint('DEBUG: Match Ended. MyName: $myName, Calculated Rank: $rank, ChipsRemaining: $chipsRemaining');

                  Navigator.of(context).pushReplacement(
                    MaterialPageRoute(
                      builder: (_) => MatchResultScreen(
                        placement: rank,
                        chipsRemaining: chipsRemaining,
                      ),
                    ),
                  );
                });
                return const Center(child: CircularProgressIndicator());
              }

              if (game.currentState == GameState.result) {
                return const Center(child: CircularProgressIndicator());
              }

              // Show "Eliminated" popup the moment it happens
              if (game.justEliminated) {
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  game.clearJustEliminated();
                  _showEliminatedDialog(context, game);
                });
              }

              final question = game.currentQuestion;

              if (question == null) {
                return const MatchmakingOverlay();
              }

              return Column(
                children: [
                  // --- TOP: TIMER & QUESTION ---
                  _buildQuestionHeader(game, question, isQuestionState),

                  const SizedBox(height: 16),

                  // --- PLAYERS BAR ---
                  _buildPlayerTracker(game, isRevealState),

                  if (isRevealState && game.lastRoundResult != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(
                        'POT: ${game.lastRoundResult!.totalPot}',
                        style: const TextStyle(
                          color: AppTheme.goldCoin,
                          fontSize: 24,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2,
                        ),
                      ).animate(key: ValueKey(game.currentRound))
                       .scale(curve: Curves.elasticOut, duration: 800.ms)
                       .shimmer(duration: 2.seconds),
                    ),

                  const SizedBox(height: 16),

                  // --- ANSWERS ---
                  Expanded(
                    child: ListView.separated(
                      physics: const BouncingScrollPhysics(),
                      itemCount: question.answers.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (context, index) {
                        return _buildAnswerButton(
                          context, game, index, question.answers[index],
                          isRevealState, question.correctAnswerIndex,
                        ).animate().slideX(
                          begin: 0.5, end: 0,
                          delay: (100 * index).ms,
                          duration: 400.ms,
                          curve: Curves.easeOutQuad,
                        ).fadeIn();
                      },
                    ),
                  ),

                  const SizedBox(height: 10),
                  // --- BET PANEL ---
                  _buildBetPanel(context, game, isQuestionState, isRevealState)
                      .animate()
                      .slideY(begin: 0.5, end: 0, duration: 600.ms, curve: Curves.easeOutQuad)
                      .fadeIn(),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  // ─── Eliminated Dialog ────────────────────────────────────────────────────
  void _showEliminatedDialog(BuildContext context, GameManager game) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          padding: const EdgeInsets.all(28),
          decoration: BoxDecoration(
            color: const Color(0xFF1A0A1A),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: AppTheme.dangerRed, width: 2),
            boxShadow: [
              BoxShadow(
                color: AppTheme.dangerRed.withOpacity(0.3),
                blurRadius: 30,
                spreadRadius: 5,
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('💀', style: TextStyle(fontSize: 52)),
              const SizedBox(height: 12),
              const Text(
                'ELIMINATED',
                style: TextStyle(
                  color: AppTheme.dangerRed,
                  fontSize: 30,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 4,
                ),
              ).animate().scale(curve: Curves.elasticOut, duration: 800.ms),
              const SizedBox(height: 8),
              const Text(
                'Your stack ran out.',
                style: TextStyle(color: Colors.white54, fontSize: 14),
              ),
              const SizedBox(height: 28),
              // Spectate button
              ChunkyButton(
                onTap: () => Navigator.of(ctx).pop(), // Close dialog, stay on MatchScreen
                baseColor: const Color(0xFF2A2A4A),
                shadowColor: Colors.black87,
                elevation: 4,
                borderRadius: 16,
                padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.remove_red_eye_rounded, color: Colors.white70),
                    SizedBox(width: 8),
                    Text(
                      'SPECTATE',
                      style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w900, fontSize: 16),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              // Main screen button
              ChunkyButton(
                onTap: () {
                  Navigator.of(ctx).pop(); // Close dialog
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
                baseColor: AppTheme.dangerRed,
                shadowColor: const Color(0xFF8B0000),
                elevation: 4,
                borderRadius: 16,
                padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.home_rounded, color: Colors.white),
                    SizedBox(width: 8),
                    Text(
                      'MAIN MENU',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ).animate().scale(begin: const Offset(0.8, 0.8), curve: Curves.easeOutBack, duration: 400.ms).fadeIn(),
      ),
    );
  }

  // ─── Question Header ──────────────────────────────────────────────────────
  Widget _buildQuestionHeader(GameManager game, Question question, bool isQuestionState) {
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
                border: Border.all(color: AppTheme.dangerRed),
              ),
              child: const Text(
                '🚨 ELIMINATIONS & ALL-INS ENABLED! 🚨',
                style: TextStyle(color: AppTheme.dangerRed, fontWeight: FontWeight.bold, fontSize: 13),
                textAlign: TextAlign.center,
              ),
            ).animate(onPlay: (c) => c.repeat(reverse: true)).shimmer(color: Colors.white, duration: 1000.ms),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                game.currentState == GameState.reveal ? 'RESULT' : 'PLACE BET',
                style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.bold),
              ),
              Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    height: 40, width: 40,
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
            'ROUND ${game.currentRound} / ${game.maxRounds}',
            style: const TextStyle(color: AppTheme.purpleGlow, fontWeight: FontWeight.bold, letterSpacing: 2),
          ).animate().shimmer(color: Colors.white, duration: 2000.ms),
          const SizedBox(height: 12),
          Text(
            question.questionText,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
            textAlign: TextAlign.center,
          ).animate(key: ValueKey(question.questionText)).slideY(begin: -0.2, end: 0, duration: 400.ms).fadeIn(),
        ],
      ),
    ).animate().scale(curve: Curves.easeOutBack, duration: 500.ms).fadeIn();
  }

  // ─── Player Tracker (Number Line) ──────────────────────────────────────────
  Widget _buildPlayerTracker(GameManager game, bool isRevealState) {
    final activePlayers = game.players.where((p) => !p.isEliminated).toList()
      ..sort((a, b) => b.stack.compareTo(a.stack));

    if (game.players.isEmpty) return const SizedBox.shrink();

    // Bounds for the number line
    double maxStack = game.players.fold(100.0, (m, p) => m > p.stack ? m : p.stack.toDouble());
    maxStack = (maxStack * 1.2).clamp(100.0, 2000.0);

    // Elimination logic
    final int toEliminate = game.currentRound <= game.shieldRounds
        ? 0
        : (activePlayers.length * 0.2).ceil();

    double thresholdStack = 0;
    if (toEliminate > 0 && activePlayers.length > toEliminate) {
      // The lowest "safe" player defines the boundary
      thresholdStack = activePlayers[activePlayers.length - toEliminate - 1].stack.toDouble();
    } else if (toEliminate > 0 && activePlayers.length == toEliminate) {
        // Everyone is in danger? Unlikely but fallback
        thresholdStack = activePlayers.first.stack.toDouble();
    }

    return Container(
      height: 100,
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        color: AppTheme.panelGlassColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final width = constraints.maxWidth;
          
          return Stack(
            clipBehavior: Clip.none,
            children: [
              // --- Background Axis ---
              Center(
                child: Container(
                  height: 4,
                  width: width,
                  decoration: BoxDecoration(
                    color: Colors.white10,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // --- Players (Dots) ---
              ...game.players.asMap().entries.map((entry) {
                final idx = entry.key;
                final p = entry.value;
                final bool isLocal = p.id == game.localPlayer.id;
                final bool isEliminated = p.isEliminated;

                int rank = 0;
                bool isKieso = false;
                if (!isEliminated) {
                  rank = activePlayers.indexWhere((ap) => ap.id == p.id) + 1;
                  isKieso = game.currentRound > game.shieldRounds && rank > activePlayers.length - toEliminate;
                }

                // Position on line
                final double targetX = (p.stack / maxStack) * width;
                
                // Visual properties
                Color dotColor = Colors.white;
                if (isKieso) dotColor = AppTheme.dangerRed;
                else if (isLocal) dotColor = AppTheme.goldCoin;

                // Alternate labels above/below using index
                final bool labelAbove = idx % 2 == 0;

                // Net change for this player
                int netChange = 0;
                if (isRevealState && game.lastRoundResult != null) {
                  netChange = game.lastRoundResult!.netChanges[p.id] ?? 0;
                }

                return AnimatedPositioned(
                  key: ValueKey(p.id),
                  duration: const Duration(milliseconds: 1000),
                  curve: Curves.easeOutBack,
                  left: targetX.clamp(0.0, width) - 15,
                  top: 30, // Adjusted for smaller dots
                  child: Opacity(
                    opacity: isEliminated ? 0.3 : 1.0,
                    child: Stack(
                      clipBehavior: Clip.none,
                      alignment: Alignment.center,
                      children: [
                        // Label container
                        Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (labelAbove) _buildPlayerLabel(p, isLocal, true),
                            
                            // Dot
                            Stack(
                              alignment: Alignment.center,
                              children: [
                                  _buildDotSkin(p.equippedSkin, dotColor, isLocal, isKieso),
                                ),
                              ],
                            ),

                            if (!labelAbove) _buildPlayerLabel(p, isLocal, false),
                          ],
                        ),

                        // --- PARTICLE / TRAIL EFFECT ---
                        if (p.equippedTrail != "none" && !isEliminated)
                          Positioned(
                             child: TrailEffect(type: p.equippedTrail, color: dotColor),
                          ),

                        // --- LANDING ANIMATION ---
                        if (isRevealState && !isEliminated && netChange > 0)
                          Positioned(
                            child: LandingAnimation(type: p.equippedAnimation),
                          ),

                        // --- FLOAT WIN/LOSS TEXT ---
                        if (netChange != 0 && isRevealState)
                          Positioned(
                            top: -40,
                            child: Text(
                              netChange > 0 ? '+$netChange' : '$netChange',
                              style: TextStyle(
                                color: netChange > 0 ? AppTheme.successGreen : AppTheme.dangerRed,
                                fontWeight: FontWeight.w900,
                                fontSize: 16,
                                shadows: [
                                  Shadow(color: Colors.black.withOpacity(0.8), blurRadius: 4, offset: const Offset(0, 2)),
                                ],
                              ),
                            ).animate()
                             .slideY(begin: 0.2, end: -0.2, duration: 1.seconds, curve: Curves.easeOutQuint)
                             .fadeIn(duration: 400.ms),
                          ),
                      ],
                    ),
                  ),
                );
              }),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPlayerLabel(Player p, bool isLocal, bool isAbove) {
    return Padding(
      padding: EdgeInsets.only(bottom: isAbove ? 2 : 0, top: isAbove ? 0 : 2),
      child: Column(
        children: [
          Text(
            isLocal ? 'YOU' : p.username,
            style: TextStyle(
              color: isLocal ? AppTheme.goldCoin : Colors.white60,
              fontSize: 8,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            p.isEliminated ? 'OUT' : '${p.stack}',
            style: TextStyle(
              color: p.isEliminated ? AppTheme.dangerRed : Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }

  // ─── Answer Button ────────────────────────────────────────────────────────
  Widget _buildAnswerButton(
    BuildContext context, GameManager game, int index, String text,
    bool isRevealState, int correctIndex,
  ) {
    final isSelected = game.selectedAnswerIndex == index;
    final isCorrect = index == correctIndex;

    Color baseColor;
    Color shadowColor;
    Color textColor = Colors.white;

    if (isRevealState) {
      // ALWAYS show correct answer green, wrong selected = red, others = neutral
      if (isCorrect) {
        baseColor = AppTheme.successGreen;
        shadowColor = const Color(0xFF1C7A2F);
        textColor = Colors.black;
      } else if (isSelected) {
        // Player picked the wrong one
        baseColor = AppTheme.dangerRed;
        shadowColor = const Color(0xFF8B0000);
      } else {
        baseColor = const Color(0xFF1E1E3A);
        shadowColor = const Color(0xFF101028);
        textColor = Colors.white38;
      }
    } else if (isSelected) {
      baseColor = AppTheme.neonCyan;
      shadowColor = const Color(0xFF009989);
      textColor = Colors.black;
    } else {
      baseColor = const Color(0xFF2A2A4A);
      shadowColor = const Color(0xFF151525);
    }

    return ChunkyButton(
      onTap: (isRevealState || game.localPlayer.isEliminated) ? null : () => game.selectAnswer(index),
      baseColor: baseColor,
      shadowColor: shadowColor,
      isSelected: isSelected && !isRevealState,
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

  // ─── Bet Panel ────────────────────────────────────────────────────────────
  Widget _buildBetPanel(BuildContext context, GameManager game, bool isQuestionState, bool isRevealState) {
    int minBet = game.currentMinBet;
    final limitMultiplier = game.currentRound <= game.shieldRounds ? 0.4 : 1.0;
    int maxBet = (game.localPlayer.stack * limitMultiplier).floor();

    final isForcedAllIn = game.localPlayer.stack <= minBet;
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
      opacity: (isQuestionState && !game.localPlayer.isEliminated) ? 1.0 : 0.5,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: AppTheme.backgroundDarkNavy,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppTheme.purpleGlow.withOpacity(0.5), width: 2),
        ),
        child: IgnorePointer(
          ignoring: !isQuestionState || game.localPlayer.isEliminated,
          child: Column(
            children: [
              if (game.localPlayer.isEliminated)
                const Padding(
                  padding: EdgeInsets.only(bottom: 8.0),
                  child: Text(
                    'ELIMINATED - SPECTATING',
                    style: TextStyle(color: AppTheme.dangerRed, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    isForcedAllIn ? 'ALL-IN!' : 'CURRENT BET (MIN $minBet)',
                    style: TextStyle(
                      color: isForcedAllIn ? AppTheme.dangerRed : Colors.white54,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    '${sliderVal.toInt()}',
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
                    onChanged: (isForcedAllIn || minBet >= maxBet || game.localPlayer.isEliminated)
                        ? null
                        : (val) => game.updateBet(val),
                  ),
                ),
              ),
              const Divider(color: Colors.white10, height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('YOUR STACK', style: TextStyle(color: Colors.white54, fontSize: 12)),
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 400),
                    transitionBuilder: (Widget child, Animation<double> animation) {
                      return ScaleTransition(scale: animation, child: child);
                    },
                    child: Text(
                      '${game.localPlayer.stack}',
                      key: ValueKey<int>(game.localPlayer.stack),
                      style: const TextStyle(color: AppTheme.goldCoin, fontSize: 28, fontWeight: FontWeight.w900),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  Widget _buildDotSkin(String skinId, Color color, bool isLocal, bool isKieso) {
    double size = 16.0;
    if (isLocal) size = 20.0;

    switch (skinId) {
      case 'skin_neon_ring':
        return Container(
          width: size, height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: color, width: 3),
            boxShadow: [
              BoxShadow(color: color.withOpacity(0.5), blurRadius: 4, spreadRadius: 1),
            ],
          ),
        );
      case 'skin_star':
        return Icon(Icons.star_rounded, color: color, size: size + 4);
      case 'skin_diamond_3d':
        return Icon(Icons.diamond_rounded, color: color, size: size + 4);
      default:
        return Container(
          width: size - 2, height: size - 2,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.black, width: 1.5),
            boxShadow: [
              if (isLocal) BoxShadow(color: AppTheme.goldCoin.withOpacity(0.6), blurRadius: 8, spreadRadius: 1),
              if (isKieso) BoxShadow(color: AppTheme.dangerRed.withOpacity(0.6), blurRadius: 8, spreadRadius: 1),
            ],
          ),
        );
    }
  }
}

class LandingAnimation extends StatelessWidget {
  final String type;

  const LandingAnimation({super.key, required this.type});

  @override
  Widget build(BuildContext context) {
    if (type == 'anim_confetti') {
      return Stack(
        alignment: Alignment.center,
        children: List.generate(12, (i) {
          final random = (i * 30).toDouble();
          return Container(
            width: 4, height: 4,
            color: Colors.primaries[i % Colors.primaries.length],
          ).animate(onPlay: (c) => c.repeat())
           .move(begin: Offset.zero, end: Offset(
             (i % 2 == 0 ? 1 : -1) * (15 + i % 5 * 10).toDouble(),
             - (20 + i % 3 * 10).toDouble()
           ), duration: 1.seconds)
           .fadeOut();
        }),
      );
    }
    if (type == 'anim_lightning') {
      return Container(
        width: 60, height: 60,
        decoration: BoxDecoration(
          color: Colors.blueAccent.withOpacity(0.2),
          shape: BoxShape.circle,
        ),
      ).animate(onPlay: (c) => c.repeat())
       .scale(begin: const Offset(0.5, 0.5), end: const Offset(1.5, 1.5), duration: 400.ms)
       .shimmer(color: Colors.white, duration: 400.ms)
       .fadeOut(delay: 200.ms);
    }
    return const SizedBox.shrink();
  }
}

class TrailEffect extends StatelessWidget {
  final String type;
  final Color color;

  const TrailEffect({super.key, required this.type, required this.color});

  @override
  Widget build(BuildContext context) {
    if (type == 'trail_fire') {
      return Container()
        .animate(onPlay: (c) => c.repeat())
        .custom(
          duration: 500.ms,
          builder: (context, value, child) => Container(
            width: 30, height: 30,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [color.withOpacity(0.5), Colors.transparent],
              ),
            ),
          ),
        )
        .fadeOut(delay: 200.ms);
    } 
    if (type == 'trail_ghost') {
      return Container()
        .animate(onPlay: (c) => c.repeat())
        .scale(begin: const Offset(1,1), end: const Offset(2,2), duration: 1.seconds)
        .fadeOut(duration: 1.seconds);
    }
    return const SizedBox.shrink();
  }
}
