
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/game_manager.dart';
import '../theme.dart';

class LeagueRoadScreen extends StatelessWidget {
  const LeagueRoadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<GameManager>(
        builder: (context, game, child) {
          final currentElo = game.userStats?.elo ?? 0;
          final milestones = _getMilestones();

          return Stack(
            children: [
              // 1. Vertical Road Graphic (Background)
              Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Color(0xFF161B33), Color(0xFF0D0D1A)],
                  ),
                ),
              ),
              
              // 2. Custom Scrollable List
              CustomScrollView(
                reverse: true, // Start from Bronze at the bottom
                slivers: [
                  SliverAppBar(
                    pinned: true,
                    expandedHeight: 120,
                    backgroundColor: Colors.transparent,
                    flexibleSpace: FlexibleSpaceBar(
                      title: Text(
                        "LEAGUE PROGRESSION",
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                          fontSize: 16,
                          letterSpacing: 2,
                          shadows: [Shadow(color: AppTheme.neonCyan.withOpacity(0.5), blurRadius: 10)],
                        ),
                      ),
                      centerTitle: true,
                    ),
                    leading: IconButton(
                      icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ),

                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final m = milestones[index];
                        final bool isAchieved = currentElo >= m.elo;
                        final bool isNext = !isAchieved && (index == 0 || currentElo >= milestones[index-1].elo);

                        return _buildMilestoneNode(m, isAchieved, isNext);
                      },
                      childCount: milestones.length,
                    ),
                  ),
                  
                  const SliverToBoxAdapter(child: SizedBox(height: 100)),
                ],
              ),
              
              // 3. Current Rank Floating Indicator
              Positioned(
                bottom: 30,
                left: 0, right: 0,
                child: Center(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    decoration: BoxDecoration(
                      color: AppTheme.neonCyan,
                      borderRadius: BorderRadius.circular(30),
                      boxShadow: [BoxShadow(color: AppTheme.neonCyan.withOpacity(0.4), blurRadius: 20)],
                    ),
                    child: Text(
                      "CURRENT: $currentElo ELO",
                      style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 16),
                    ),
                  ),
                ),
              ).animate().slideY(begin: 1, end: 0, duration: 800.ms, curve: Curves.elasticOut),
            ],
          );
        },
      ),
    );
  }

  Widget _buildMilestoneNode(Milestone m, bool isAchieved, bool isNext) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      height: 120,
      child: Row(
        children: [
          // ELO Number
          SizedBox(
            width: 60,
            child: Text(
              "${m.elo}",
              style: TextStyle(
                color: isAchieved ? AppTheme.neonCyan : Colors.white24,
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),
          
          // The Track & Dot
          Expanded(
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Vertical Line Segment
                Container(
                  width: 4,
                  height: 120,
                  color: isAchieved ? AppTheme.neonCyan.withOpacity(0.5) : Colors.white10,
                ),
                
                // Milestone Node
                Container(
                  width: isAchieved ? 40 : 30,
                  height: isAchieved ? 40 : 30,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isAchieved ? AppTheme.neonCyan : Colors.black,
                    border: Border.all(
                      color: isNext ? AppTheme.neonCyan : (isAchieved ? Colors.white : Colors.white10),
                      width: isNext ? 3 : 2,
                    ),
                    boxShadow: isAchieved ? [BoxShadow(color: AppTheme.neonCyan.withOpacity(0.5), blurRadius: 10)] : null,
                  ),
                  child: isAchieved 
                    ? const Icon(Icons.check, color: Colors.black, size: 20) 
                    : (isNext ? Icon(Icons.star_rounded, color: AppTheme.neonCyan, size: 16).animate(onPlay: (c) => c.repeat()).scale(end: const Offset(1.2, 1.2)) : null),
                ),
              ],
            ),
          ),
          
          // Milestone Info
          Expanded(
            flex: 3,
            child: Container(
              margin: const EdgeInsets.only(left: 20),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isAchieved ? Colors.white.withOpacity(0.05) : Colors.transparent,
                borderRadius: BorderRadius.circular(15),
                border: isAchieved ? Border.all(color: AppTheme.neonCyan.withOpacity(0.2)) : null,
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "${m.league.toUpperCase()} ${m.division}",
                    style: TextStyle(
                      color: isAchieved ? Colors.white : Colors.white38,
                      fontWeight: FontWeight.w900,
                      fontSize: 16,
                    ),
                  ),
                  if (m.reward != null)
                    Text(
                      "🎁 ${m.reward}",
                      style: const TextStyle(color: AppTheme.goldCoin, fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Milestone> _getMilestones() {
    return [
      Milestone(elo: 0, league: "Bronze", division: "III", reward: "Starter Kit"),
      Milestone(elo: 500, league: "Bronze", division: "II", reward: "100 Gold"),
      Milestone(elo: 1000, league: "Bronze", division: "I", reward: "Emoji Pack"),
      Milestone(elo: 1500, league: "Silver", division: "III", reward: "Silver Key"),
      Milestone(elo: 1666, league: "Silver", division: "II", reward: "250 Gold"),
      Milestone(elo: 1833, league: "Silver", division: "I", reward: "Skin: Recruit"),
      Milestone(elo: 2000, league: "Gold", division: "III", reward: "Gold Key"),
      Milestone(elo: 2166, league: "Gold", division: "II", reward: "500 Gold"),
      Milestone(elo: 2333, league: "Gold", division: "I", reward: "Trail: Flame"),
      Milestone(elo: 2500, league: "Platinum", division: "III", reward: "Plat Key"),
      Milestone(elo: 2666, league: "Platinum", division: "II", reward: "1000 Gold"),
      Milestone(elo: 2833, league: "Platinum", division: "I", reward: "Animation: Aura"),
      Milestone(elo: 3000, league: "Diamond", division: "I", reward: "Diamond Title"),
    ];
  }
}

class Milestone {
  final int elo;
  final String league;
  final String division;
  final String? reward;

  Milestone({required this.elo, required this.league, required this.division, this.reward});
}
