import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../theme.dart';
import 'widgets/chunky_card.dart';

class LeaderboardScreen extends StatelessWidget {
  const LeaderboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: SafeArea(
        child: Column(
          children: [
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Text("LEADERBOARDS", style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 2)),
            ),
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xFF151525).withOpacity(0.8),
                borderRadius: BorderRadius.circular(30),
                boxShadow: const [BoxShadow(color: Colors.black26, offset: Offset(0, 4), blurRadius: 4)],
              ),
              child: TabBar(
                indicator: BoxDecoration(
                  color: AppTheme.neonCyan,
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(color: AppTheme.neonCyan.withOpacity(0.4), blurRadius: 10, offset: const Offset(0, 2))
                  ]
                ),
                indicatorSize: TabBarIndicatorSize.tab,
                dividerColor: Colors.transparent,
                labelColor: Colors.black,
                labelStyle: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 1),
                unselectedLabelColor: Colors.white54,
                tabs: const [
                  Tab(text: "DAILY"),
                  Tab(text: "WEEKLY"),
                  Tab(text: "SEASON"),
                ],
              ),
            ),
            Expanded(
              child: TabBarView(
                children: [
                  _buildList("DAILY"),
                  _buildList("WEEKLY"),
                  _buildList("SEASON"),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildList(String type) {
    // Mock data
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 20,
      itemBuilder: (context, index) {
        final rank = index + 1;
        Color rankColor = Colors.white;
        if (rank == 1) rankColor = AppTheme.goldCoin;
        if (rank == 2) rankColor = Colors.grey[400]!;
        if (rank == 3) rankColor = const Color(0xFFCD7F32); // Bronze

        return ChunkyCard(
          baseColor: const Color(0xFF2A2A4A),
          shadowColor: const Color(0xFF151525),
          borderColor: rank <= 3 ? rankColor : Colors.transparent,
          elevation: 4.0,
          child: Row(
            children: [
              SizedBox(
                width: 40,
                child: Text("#$rank", style: TextStyle(color: rankColor, fontWeight: FontWeight.bold, fontSize: 18)),
              ),
              const Expanded(child: Text("Player_Name", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold))),
              Text("${(20 - index) * 1500} pts", style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.w900)),
            ],
          ),
        ).animate().slideY(begin: 0.2, end: 0, delay: (20 * index).ms, duration: 400.ms, curve: Curves.easeOut).fadeIn();
      },
    );
  }
}
