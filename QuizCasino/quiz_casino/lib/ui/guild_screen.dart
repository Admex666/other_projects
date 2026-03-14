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
  final TextEditingController _searchController = TextEditingController();
  bool _isBrowsing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GameManager>().fetchMyGuild();
      context.read<GameManager>().searchGuilds(null); // Initial discovery list
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        if (!game.isLoggedIn) return const Center(child: Text("Please login to see guilds"));

        if (game.userStats?.guildTag == null || _isBrowsing) {
          return _buildDiscoveryUI(context, game);
        }

        if (game.currentGuild == null) {
          return const Center(child: CircularProgressIndicator(color: AppTheme.neonCyan));
        }

        return _buildGuildInfoUI(context, game);
      },
    );
  }

  Widget _buildDiscoveryUI(BuildContext context, GameManager game) {
    return SafeArea(
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: Colors.white.withOpacity(0.05),
                      hintText: "Search guilds...",
                      hintStyle: const TextStyle(color: Colors.white38),
                      prefixIcon: const Icon(Icons.search, color: Colors.white38),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                    ),
                    onChanged: (val) => game.searchGuilds(val),
                  ),
                ),
                if (game.userStats?.guildTag != null) ...[
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () => setState(() => _isBrowsing = false),
                  ),
                ],
              ],
            ),
          ),
          if (game.userStats?.guildTag == null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: ChunkyButton(
                onTap: () => _showCreateGuildDialog(context, game),
                baseColor: AppTheme.neonCyan,
                shadowColor: Colors.teal.shade800,
                child: const Center(child: Text("CREATE NEW GUILD", style: TextStyle(fontWeight: FontWeight.bold))),
              ),
            ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: game.searchedGuilds.length,
              itemBuilder: (context, index) {
                final guild = game.searchedGuilds[index];
                return ChunkyCard(
                  baseColor: const Color(0xFF2A2A4A),
                  shadowColor: const Color(0xFF151525),
                  elevation: 2,
                  margin: const EdgeInsets.only(bottom: 12),
                  child: InkWell(
                    onTap: () => _showGuildInfoPopup(context, guild),
                    child: Row(
                      children: [
                      const Icon(Icons.shield, color: AppTheme.purpleGlow, size: 40),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(guild.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                            Text("[${guild.tag}]", style: const TextStyle(color: Colors.white54, fontSize: 12)),
                          ],
                        ),
                      ),
                      ChunkyButton(
                        onTap: () => game.requestToJoin(guild.tag),
                        width: 80,
                        height: 36,
                        baseColor: guild.isPublic ? AppTheme.successGreen : AppTheme.purpleGlow,
                        shadowColor: Colors.black,
                        child: Center(
                          child: Text(
                            guild.isPublic ? "JOIN" : "REQ",
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuildInfoUI(BuildContext context, GameManager game) {
    final guild = game.currentGuild!;
    final isLeader = guild.leaderUsername == game.userStats?.username;
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
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        "${guild.name.toUpperCase()} [${guild.tag}]",
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1),
                      ),
                      IconButton(
                        icon: const Icon(Icons.explore_outlined, color: AppTheme.neonCyan),
                        onPressed: () => setState(() => _isBrowsing = true),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildMiniStat("VAULT", "${guild.vaultGold} GOLD", AppTheme.goldCoin),
                      _buildMiniStat("MY SHARES", "$myShares ($sharePercent%)", AppTheme.neonCyan),
                    ],
                  ),
                  if (isLeader) ...[
                    const SizedBox(height: 16),
                    const Divider(color: Colors.white12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("PRIVACY: ", style: TextStyle(color: Colors.white54, fontWeight: FontWeight.bold, fontSize: 12)),
                        Text(guild.isPublic ? "OPEN (JOIN)" : "CLOSED (REQUEST)", 
                          style: TextStyle(color: guild.isPublic ? AppTheme.successGreen : AppTheme.purpleGlow, fontWeight: FontWeight.bold, fontSize: 12)
                        ),
                        Switch(
                          value: guild.isPublic,
                          activeColor: AppTheme.successGreen,
                          onChanged: (val) => game.updateGuildSettings(val),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (isLeader && guild.pendingRequests.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.only(left: 8.0, bottom: 12),
                    child: Text("PENDING REQUESTS", style: TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, letterSpacing: 1)),
                  ),
                  ...guild.pendingRequests.map((applicant) => ChunkyCard(
                    baseColor: AppTheme.purpleGlow.withOpacity(0.1),
                    shadowColor: Colors.black,
                    margin: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(applicant, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                        Row(
                          children: [
                            IconButton(
                              icon: const Icon(Icons.check_circle, color: AppTheme.successGreen),
                              onPressed: () => game.handleJoinRequest(applicant, true),
                            ),
                            IconButton(
                              icon: const Icon(Icons.cancel, color: Colors.redAccent),
                              onPressed: () => game.handleJoinRequest(applicant, false),
                            ),
                          ],
                        ),
                      ],
                    ),
                  )).toList(),
                  const SizedBox(height: 24),
                ],
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
                    child: InkWell(
                      onTap: () => _handleMemberTap(context, game, entry.key),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(entry.key, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                          Text("${entry.value} shares", style: const TextStyle(color: AppTheme.neonCyan, fontSize: 14, fontWeight: FontWeight.w900)),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
            child: ChunkyButton(
              onTap: () => isLeader ? _showDeleteGuildConfirm(context, game) : _showLeaveGuildConfirm(context, game),
              baseColor: isLeader ? AppTheme.dangerRed : Colors.white10,
              shadowColor: Colors.black,
              child: Center(
                child: Text(
                  isLeader ? "DISBAND GUILD" : "LEAVE GUILD",
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ),
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

  void _handleMemberTap(BuildContext context, GameManager game, String username) {
    game.fetchPlayerInfo(username);
    _showPlayerInfoPopup(context, game);
  }

  void _showGuildInfoPopup(BuildContext context, dynamic guild) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.transparent,
        child: ChunkyCard(
          baseColor: const Color(0xFF151525),
          shadowColor: Colors.black,
          borderColor: AppTheme.neonCyan,
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.shield, color: AppTheme.purpleGlow, size: 60),
              const SizedBox(height: 16),
              Text(guild.name.toUpperCase(), style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 1)),
              Text("[${guild.tag}]", style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              const Divider(color: Colors.white12),
              const SizedBox(height: 16),
              _buildPopupRow("LEADER", guild.leaderUsername),
              _buildPopupRow("VAULT", "${guild.vaultGold} GOLD"),
              _buildPopupRow("ACCESS", guild.isPublic ? "PUBLIC" : "REQUEST ONLY"),
              const SizedBox(height: 24),
              ChunkyButton(
                onTap: () => Navigator.pop(context),
                baseColor: Colors.white10,
                shadowColor: Colors.black,
                child: const Center(child: Text("CLOSE")),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showPlayerInfoPopup(BuildContext context, GameManager game) {
    showDialog(
      context: context,
      builder: (context) {
        return Consumer<GameManager>(
          builder: (context, game, _) {
            final profile = game.selectedPlayerProfile;
            return Dialog(
              backgroundColor: Colors.transparent,
              child: ChunkyCard(
                baseColor: const Color(0xFF151525),
                shadowColor: Colors.black,
                borderColor: AppTheme.purpleGlow,
                padding: const EdgeInsets.all(24),
                child: profile == null 
                  ? const SizedBox(height: 200, child: Center(child: CircularProgressIndicator(color: AppTheme.neonCyan)))
                  : Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.person, color: AppTheme.neonCyan, size: 60),
                        const SizedBox(height: 16),
                        Text(profile.username.toUpperCase(), style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 1)),
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppTheme.purpleGlow.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: AppTheme.purpleGlow, width: 1),
                          ),
                          child: Text(profile.league.toUpperCase(), style: const TextStyle(color: AppTheme.purpleGlow, fontWeight: FontWeight.bold, fontSize: 12)),
                        ),
                        const SizedBox(height: 24),
                        _buildPopupRow("ELO", "${profile.elo} pts"),
                        _buildPopupRow("VICTORIES", "${profile.victories}"),
                        _buildPopupRow("GAMES", "${profile.gamesPlayed}"),
                        _buildPopupRow("GOLD", "${profile.gold}"),
                        const SizedBox(height: 24),
                        if (game.currentGuild?.leaderUsername == game.userStats?.username && 
                            profile.username != game.userStats?.username) ...[
                          ChunkyButton(
                            onTap: () {
                              game.kickMember(profile.username);
                              Navigator.pop(context);
                            },
                            baseColor: AppTheme.dangerRed,
                            shadowColor: Colors.black,
                            child: const Center(child: Text("KICK MEMBER", style: TextStyle(fontWeight: FontWeight.bold))),
                          ),
                          const SizedBox(height: 12),
                        ],
                        ChunkyButton(
                          onTap: () => Navigator.pop(context),
                          baseColor: Colors.white10,
                          shadowColor: Colors.black,
                          child: const Center(child: Text("CLOSE")),
                        ),
                      ],
                    ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildPopupRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontWeight: FontWeight.bold, fontSize: 12)),
          Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  void _showLeaveGuildConfirm(BuildContext context, GameManager game) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF151525),
        title: const Text("LEAVE GUILD?", style: TextStyle(color: Colors.white)),
        content: const Text("Are you sure you want to leave this guild? Your shares will be lost.", style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("CANCEL")),
          TextButton(
            onPressed: () {
              game.leaveGuild();
              Navigator.pop(context);
            }, 
            child: const Text("LEAVE", style: TextStyle(color: AppTheme.dangerRed))
          ),
        ],
      ),
    );
  }

  void _showDeleteGuildConfirm(BuildContext context, GameManager game) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF151525),
        title: const Text("DISBAND GUILD?", style: TextStyle(color: AppTheme.dangerRed, fontWeight: FontWeight.bold)),
        content: const Text("This will PERMANENTLY delete the guild and remove all members. THIS CANNOT BE UNDONE.", style: TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("CANCEL")),
          TextButton(
            onPressed: () {
              game.deleteGuild();
              Navigator.pop(context);
            }, 
            child: const Text("DELETE", style: TextStyle(color: AppTheme.dangerRed))
          ),
        ],
      ),
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
