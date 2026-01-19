import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/story_engine.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 80),
            // Avatar
            Center(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.blueAccent, width: 3),
                      boxShadow: [
                        BoxShadow(color: Colors.blueAccent.withOpacity(0.3), blurRadius: 20, spreadRadius: 5),
                      ],
                    ),
                    child: const CircleAvatar(
                      backgroundColor: Color(0xFF1E293B),
                      child: Icon(Icons.person, size: 60, color: Colors.blueAccent),
                    ),
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: Consumer<StoryEngine>(
                      builder: (context, engine, _) {
                        int steps = engine.user?.steps ?? 0;
                        int level = (steps / 1000).floor() + 1;
                        return Container(
                          padding: const EdgeInsets.all(8),
                          decoration: const BoxDecoration(color: Colors.blueAccent, shape: BoxShape.circle),
                          child: Text("Lvl $level", style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                        );
                      }
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Consumer<StoryEngine>(
              builder: (context, engine, _) => Text(
                engine.user?.username ?? "Városi Felfedező",
                style: GoogleFonts.outfit(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ),
            const SizedBox(height: 40),
            
            // Stats Row
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Consumer<StoryEngine>(
                builder: (context, engine, _) => Row(
                  children: [
                    _buildStatItem("Km", "${((engine.user?.steps ?? 0) * 0.00075).toStringAsFixed(1)}"), // 0.75m per step
                    const SizedBox(width: 12),
                    _buildStatItem("Lépés", "${engine.user?.steps ?? 0}"),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 40),
            _buildSectionHeader("TELJESÍTMÉNYEK"),
            const SizedBox(height: 20),
            
            _buildAchievementList(),
            _buildLogoutButton(context),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          children: [
            Text(value, style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
            Text(label, style: GoogleFonts.outfit(fontSize: 12, color: Colors.white54)),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          Text(
            title,
            style: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2, color: Colors.blueAccent),
          ),
        ],
      ),
    );
  }

  Widget _buildAchievementList() {
    final achievements = [
      {"icon": Icons.map_outlined, "title": "Első lépések", "desc": "Teljesítsd az első utad."},
      {"icon": Icons.wb_sunny_outlined, "title": "Napsütötte séták", "desc": "Sétálj összesen 5 km-t."},
      {"icon": Icons.visibility_outlined, "title": "Éles szem", "desc": "Találj meg 10 rejtett nyomot."},
    ];

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        children: achievements.map((a) => Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Row(
            children: [
              Icon(a['icon'] as IconData, color: Colors.amber, size: 32),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(a['title'] as String, style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: Colors.white)),
                    Text(a['desc'] as String, style: GoogleFonts.outfit(fontSize: 12, color: Colors.white54)),
                  ],
                ),
              ),
            ],
          ),
        )).toList(),
      ),
    );
  }

  Widget _buildLogoutButton(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
      child: OutlinedButton.icon(
        onPressed: () => Provider.of<StoryEngine>(context, listen: false).logout(),
        icon: const Icon(Icons.logout, color: Colors.redAccent),
        label: const Text("KIJELENTKEZÉS", style: TextStyle(color: Colors.redAccent)),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: Colors.redAccent),
          minimumSize: const Size(double.infinity, 50),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }
}
