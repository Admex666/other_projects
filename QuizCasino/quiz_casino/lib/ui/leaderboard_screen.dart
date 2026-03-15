import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'widgets/chunky_card.dart';
import 'widgets/cyber_loader.dart';

class LeaderboardScreen extends StatefulWidget {
  const LeaderboardScreen({super.key});

  @override
  State<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends State<LeaderboardScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<String> leagues = ['bronze', 'silver', 'gold', 'platinum', 'diamond'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: leagues.length, vsync: this);
    
    // Initial fetch for the user's current league or bronze
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final game = context.read<GameManager>();
      final initialLeague = game.userStats?.league ?? 'bronze';
      final index = leagues.indexOf(initialLeague.toLowerCase());
      if (index >= 0) {
        _tabController.index = index;
        game.fetchLeaderboard(leagues[index]);
      } else {
        game.fetchLeaderboard('bronze');
      }
    });

    _tabController.addListener(() {
      if (!_tabController.indexIsChanging) {
        context.read<GameManager>().fetchLeaderboard(leagues[_tabController.index]);
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        final bool isUnranked = game.userStats?.league.toLowerCase() == 'unranked';

        return SafeArea(
          child: Column(
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 24, 16, 8),
                child: Text(
                  "LEAGUE RANKINGS",
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 2,
                    color: Colors.white,
                  ),
                ),
              ),
              
              if (!isUnranked)
                // League Selector
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  height: 50,
                  decoration: BoxDecoration(
                    color: const Color(0xFF151525).withOpacity(0.8),
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    isScrollable: true,
                    indicator: BoxDecoration(
                      color: AppTheme.neonCyan,
                      borderRadius: BorderRadius.circular(25),
                      boxShadow: [
                        BoxShadow(color: AppTheme.neonCyan.withOpacity(0.4), blurRadius: 10)
                      ]
                    ),
                    indicatorSize: TabBarIndicatorSize.tab,
                    dividerColor: Colors.transparent,
                    labelColor: Colors.black,
                    labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13),
                    unselectedLabelColor: Colors.white38,
                    tabs: leagues.map((l) => Tab(text: l.toUpperCase() + "  ")).toList(),
                  ),
                ),

              Expanded(
                child: game.isLeaderboardLoading
                    ? const Center(child: CircularProgressIndicator(color: AppTheme.neonCyan))
                    : isUnranked 
                        ? _buildPlacementUI(game)
                        : _buildLeaderboardList(game),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildPlacementUI(GameManager game) {
    final int played = game.userStats?.placementMatches ?? 0;
    final int total = 5;
    final int remaining = (total - played).clamp(0, total);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.lock_outline_rounded, size: 100, color: AppTheme.neonCyan)
                .animate(onPlay: (c) => c.repeat(reverse: true))
                .scale(begin: const Offset(1, 1), end: const Offset(1.1, 1.1), duration: 1.seconds),
            const SizedBox(height: 32),
            const Text(
              "LEAGUE LOCKED",
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1),
            ),
            const SizedBox(height: 16),
            Text(
              "Play $remaining more matches to get your initial rank!",
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, color: Colors.white70, height: 1.5),
            ),
            const SizedBox(height: 48),
            
            // Progress Bar
            Stack(
              children: [
                Container(
                  height: 16,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.white12),
                  ),
                ),
                LayoutBuilder(
                  builder: (context, constraints) {
                    return AnimatedContainer(
                      duration: 1.seconds,
                      curve: Curves.easeOutCubic,
                      height: 16,
                      width: constraints.maxWidth * (played / total),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF00E5FF), AppTheme.neonCyan],
                        ),
                        borderRadius: BorderRadius.circular(8),
                        boxShadow: [
                          BoxShadow(color: AppTheme.neonCyan.withOpacity(0.5), blurRadius: 12),
                        ],
                      ),
                    );
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("PROGRESS", style: TextStyle(color: Colors.white38, fontWeight: FontWeight.bold, fontSize: 12)),
                Text(
                  "$played / $total MATCHES",
                  style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.w900, fontSize: 14),
                ),
              ],
            ),
          ],
        ).animate().fadeIn(duration: 800.ms).slideY(begin: 0.1, end: 0),
      ),
    );
  }

  Widget _buildLeaderboardList(GameManager game) {
    if (game.leaderboardPlayers.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.emoji_events_outlined, size: 64, color: Colors.white.withOpacity(0.1)),
            const SizedBox(height: 16),
            const Text("NO PLAYERS IN THIS LEAGUE YET", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.bold)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: game.leaderboardPlayers.length,
      itemBuilder: (context, index) {
        final player = game.leaderboardPlayers[index];
        final rank = index + 1;
        final isMe = player.username == game.userStats?.username;
        
        Color rankColor = Colors.white;
        if (rank == 1) rankColor = AppTheme.goldCoin;
        if (rank == 2) rankColor = Colors.grey[300]!;
        if (rank == 3) rankColor = const Color(0xFFCD7F32);

        return ChunkyCard(
          baseColor: isMe ? AppTheme.neonCyan.withOpacity(0.1) : const Color(0xFF1A1A2E),
          shadowColor: Colors.black,
          borderColor: isMe ? AppTheme.neonCyan : (rank <= 3 ? rankColor.withOpacity(0.5) : Colors.white10),
          elevation: isMe ? 8.0 : 2.0,
          margin: const EdgeInsets.only(bottom: 12),
          child: Row(
            children: [
              SizedBox(
                width: 45,
                child: Text(
                  "#$rank",
                  style: TextStyle(
                    color: rankColor,
                    fontWeight: FontWeight.w900,
                    fontSize: rank <= 3 ? 20 : 16,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      player.username,
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: isMe ? FontWeight.w900 : FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      "ELO: ${player.elo}",
                      style: TextStyle(color: Colors.white54, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    "${player.weeklyTotal}",
                    style: const TextStyle(
                      color: AppTheme.neonCyan,
                      fontWeight: FontWeight.w900,
                      fontSize: 22,
                    ),
                  ),
                  const Text("WEEKLY PTS", style: TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold)),
                ],
              ),
            ],
          ),
        ).animate().slideY(begin: 0.2, end: 0, delay: (50 * index).ms, duration: 400.ms, curve: Curves.easeOutQuad).fadeIn();
      },
    );
  }
}
