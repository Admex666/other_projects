import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'widgets/chunky_card.dart';
import 'widgets/chunky_button.dart';

class GuildScreen extends StatefulWidget {
  const GuildScreen({super.key});

  @override
  State<GuildScreen> createState() => _GuildScreenState();
}

class _GuildScreenState extends State<GuildScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _tagController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GameManager>().fetchMyGuild();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        if (game.isLoggedIn && game.userStats?.guildTag == null) {
          return _buildNoGuildUI(context, game);
        }

        if (game.currentGuild == null) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.neonCyan));
        }

        return _buildGuildInfoUI(context, game);
      },
    );
  }

  Widget _buildNoGuildUI(BuildContext context, GameManager game) {
    return SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.shield_rounded, size: 80, color: AppTheme.purpleGlow)
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scaleXY(end: 1.1, duration: 1000.ms),
              const SizedBox(height: 24),
              const Text(
                "YOU ARE NOT IN A GUILD",
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2),
              ),
              const SizedBox(height: 12),
              const Text(
                "Join an existing guild or create your own Joint Stock Company to earn dividends!",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white54, fontSize: 16),
              ),
              const SizedBox(height: 48),
              SizedBox(
                width: double.infinity,
                child: ChunkyButton(
                  onTap: () => _showCreateGuildDialog(context, game),
                  baseColor: AppTheme.neonCyan,
                  shadowColor: Colors.teal.shade800,
                  child: const Center(child: Text("CREATE GUILD", style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1))),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ChunkyButton(
                  onTap: () {}, // Implementation later
                  baseColor: Colors.white10,
                  shadowColor: Colors.black,
                  child: const Center(child: Text("JOIN GUILD", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1))),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGuildInfoUI(BuildContext context, GameManager game) {
    final guild = game.currentGuild!;
    final myShares = guild.shares[game.userStats?.username] ?? 0;
    final sharePercent = (myShares / guild.totalShares * 100).toStringAsFixed(1);

    return SafeArea(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: ChunkyCard(
              baseColor: const Color(0xFF151525).withOpacity(0.9),
              shadowColor: Colors.black,
              borderColor: AppTheme.purpleGlow,
              elevation: 4.0,
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Text(
                    "${guild.name.toUpperCase()} [${guild.tag}]",
                    style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 2),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildMiniStat("VAULT", "${guild.vaultGold} GOLD", AppTheme.goldCoin),
                      _buildMiniStat("MY SHARES", "$myShares ($sharePercent%)", AppTheme.neonCyan),
                    ],
                  ),
                ],
              ),
            ),
          ).animate().slideY(begin: -0.2, end: 0, duration: 400.ms, curve: Curves.easeOutBack).fadeIn(),
          
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Padding(
                  padding: EdgeInsets.only(left: 8.0, bottom: 12),
                  child: Text("SHAREHOLDERS", style: TextStyle(color: Colors.white54, fontWeight: FontWeight.bold, letterSpacing: 1)),
                ),
                ...guild.shares.entries.map((entry) {
                  final isMe = entry.key == game.userStats?.username;
                  return ChunkyCard(
                    baseColor: isMe ? Colors.white.withOpacity(0.05) : const Color(0xFF2A2A4A),
                    shadowColor: const Color(0xFF151525),
                    elevation: 2.0,
                    margin: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(entry.key, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                        Text("${entry.value} shares", style: const TextStyle(color: AppTheme.neonCyan, fontSize: 14, fontWeight: FontWeight.w900)),
                      ],
                    ),
                  );
                }).toList(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniStat(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.w900)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
      ],
    );
  }

  void _showCreateGuildDialog(BuildContext context, GameManager game) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF151525),
        title: const Text("CREATE NEW GUILD", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _nameController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: "Guild Name", labelStyle: TextStyle(color: Colors.white54)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _tagController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(labelText: "Tag (2-4 letters)", labelStyle: TextStyle(color: Colors.white54)),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("CANCEL", style: TextStyle(color: Colors.white38))),
          TextButton(
            onPressed: () {
              if (_nameController.text.isNotEmpty && _tagController.text.isNotEmpty) {
                game.createGuild(_nameController.text, _tagController.text);
                Navigator.pop(context);
              }
            },
            child: const Text("CREATE", style: TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}
