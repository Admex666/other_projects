import 'package:provider/provider.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/audio_manager.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import 'home_screen.dart';
import 'leaderboard_screen.dart';
import 'guild_screen.dart';
import 'profile_screen.dart';
import 'shop_screen.dart';
import 'auth_screen.dart';
import 'widgets/cyber_loader.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 2; // Home is index 2 in [Shop, Guild, Home, Rank]
  double _downloadProgress = 0;
  bool _isDownloading = false;
  String? _downloadError;

  final List<Widget> _screens = [
    const ShopScreen(),
    const GuildScreen(),
    const HomeScreen(),
    const LeaderboardScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        if (!game.isInitialized) {
          return const Scaffold(
            backgroundColor: AppTheme.backgroundDarkNavy,
            body: Center(child: CyberLoader(label: "BOOTING SYSTEM")),
          );
        }

        if (!game.isLoggedIn) {
          return const AuthScreen();
        }

        return Stack(
          children: [
            Scaffold(
              extendBody: true,
              body: Column(
                children: [
                  _buildGlobalTopBar(game),
                  Expanded(child: _screens[_currentIndex]),
                ],
              ),
              bottomNavigationBar: SafeArea(
                child: Container(
                  margin: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF151525).withOpacity(0.95),
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3), width: 2),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.neonCyan.withOpacity(0.2),
                        blurRadius: 20,
                        spreadRadius: 2,
                      )
                    ],
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildNavItem(Icons.shopping_bag_rounded, "SHOP", 0),
                      _buildNavItem(Icons.shield_rounded, "GUILD", 1),
                      _buildNavItem(Icons.home_rounded, "HOME", 2),
                      _buildNavItem(Icons.emoji_events_rounded, "RANK", 3),
                    ],
                  ),
                ),
              ),
            ),

            // --- CONNECTION LOST OVERLAY ---
            if (!game.isConnected)
              Positioned.fill(
                child: Container(
                  color: Colors.black.withOpacity(0.7),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.wifi_off_rounded, color: AppTheme.dangerRed, size: 80)
                            .animate(onPlay: (c) => c.repeat(reverse: true))
                            .scale(begin: const Offset(1, 1), end: const Offset(1.2, 1.2), duration: 1.seconds)
                            .shimmer(delay: 500.ms),
                        const SizedBox(height: 24),
                        const Text(
                          "CONNECTION LOST",
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 28, letterSpacing: 2),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          "Reconnecting to servers...",
                          style: TextStyle(color: Colors.white54, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                ).animate().fadeIn(),
              ),

            // --- UPDATE AVAILABLE OVERLAY ---
            if (game.updateInfo != null)
              Positioned.fill(
                child: Container(
                  color: Colors.black.withOpacity(0.85),
                  padding: const EdgeInsets.all(32),
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E1E2E),
                        borderRadius: BorderRadius.circular(30),
                        border: Border.all(color: AppTheme.neonCyan.withOpacity(0.5), width: 2),
                        boxShadow: [
                          BoxShadow(color: AppTheme.neonCyan.withOpacity(0.2), blurRadius: 40)
                        ],
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(color: AppTheme.neonCyan.withOpacity(0.1), shape: BoxShape.circle),
                            child: const Icon(Icons.system_update_rounded, color: AppTheme.neonCyan, size: 48),
                          ),
                          const SizedBox(height: 24),
                          const Text(
                            "SYSTEM UPDATE",
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 24, letterSpacing: 2),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            "A new version (${game.updateInfo!.latestVersion}) is available and ready for download.",
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.white70, fontSize: 14),
                          ),
                          const SizedBox(height: 32),
                          if (_isDownloading) ...[
                            ClipRRect(
                              borderRadius: BorderRadius.circular(10),
                              child: LinearProgressIndicator(
                                value: _downloadProgress,
                                backgroundColor: Colors.white12,
                                valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.neonCyan),
                                minHeight: 8,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              "${(_downloadProgress * 100).toInt()}% DOWNLOADED",
                              style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, fontSize: 10, letterSpacing: 1),
                            ),
                          ] else if (_downloadError != null) ...[
                            Text(_downloadError!, style: const TextStyle(color: AppTheme.dangerRed, fontSize: 12)),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: () => _startUpdate(game.updateInfo!.downloadUrl),
                              child: const Text("RETRY"),
                            ),
                          ] else
                            Row(
                              children: [
                                if (!game.updateInfo!.isMandatory)
                                  Expanded(
                                    child: TextButton(
                                      onPressed: () => setState(() => game.updateInfo = null),
                                      child: const Text("LATER", style: TextStyle(color: Colors.white38, fontWeight: FontWeight.bold)),
                                    ),
                                  ),
                                Expanded(
                                  flex: 2,
                                  child: ElevatedButton(
                                  onPressed: () {
                                    final url = game.updateInfo!.downloadUrl;
                                    if (url.toLowerCase().endsWith(".apk")) {
                                      _startUpdate(url);
                                    } else {
                                      // Fallback for general web pages (GitHub, Drive etc)
                                      launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
                                    }
                                  },
                                  style: ElevatedButton.styleFrom(
                                      backgroundColor: AppTheme.neonCyan,
                                      foregroundColor: Colors.black,
                                      padding: const EdgeInsets.symmetric(vertical: 16),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                                    ),
                                    child: const Text("DOWNLOAD NOW", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                                  ),
                                ),
                              ],
                            ),
                        ],
                      ),
                    ),
                  ),
                ).animate().fadeIn().scale(curve: Curves.easeOutBack, duration: 600.ms),
              ),
          ],
        );
      },
    );
  }

  Future<void> _startUpdate(String url) async {
    setState(() {
      _isDownloading = true;
      _downloadProgress = 0;
      _downloadError = null;
    });

    try {
      final tempDir = await getTemporaryDirectory();
      final String filePath = "${tempDir.path}/update.apk";
      
      final dio = Dio();
      await dio.download(
        url,
        filePath,
        onReceiveProgress: (received, total) {
          if (total != -1) {
            setState(() {
              _downloadProgress = received / total;
            });
          }
        },
      );

      // Trigger Install
      const platform = MethodChannel('xyz.knowcoin.app/updater');
      try {
        await platform.invokeMethod('installApk', {'path': filePath});
      } on PlatformException catch (e) {
        // Fallback to url_launcher if custom install fails
        debugPrint("Custom install failed, falling back: ${e.message}");
        final file = File(filePath);
        if (await file.exists()) {
          // Note: On many modern Androids, opening the file via url_launcher/intent works if FileProvider is setup
          // but MethodChannel is more reliable for direct APK installation trigger.
          launchUrl(Uri.parse(url)); 
        }
      }
    } catch (e) {
      setState(() {
        _isDownloading = false;
        _downloadError = "Download failed: $e";
      });
    }
  }

  Widget _buildGlobalTopBar(GameManager game) {
    return Container(
      padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top + 8, left: 24, right: 24, bottom: 16),
      decoration: BoxDecoration(
        color: AppTheme.backgroundDarkNavy,
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          _buildResourcePill(game.userStats?.gold.toString() ?? "0", Icons.toll_rounded, AppTheme.goldCoin),
          const SizedBox(width: 12),
          _buildResourcePill(game.userStats?.diamonds.toString() ?? "0", Icons.auto_awesome_rounded, AppTheme.purpleGlow),
        ],
      ),
    );
  }

  Widget _buildResourcePill(String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: color.withOpacity(0.3), width: 1.5),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 6),
          Text(
            value,
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(IconData icon, String label, int index) {
    bool isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () {
        if (_currentIndex != index) AudioManager().playClick();
        setState(() => _currentIndex = index);
      },
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.neonCyan.withOpacity(0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? AppTheme.neonCyan : Colors.white54,
              size: isSelected ? 26 : 24,
            ),
            if (isSelected)
              Padding(
                padding: const EdgeInsets.only(left: 8.0),
                child: Text(
                  label,
                  style: const TextStyle(color: AppTheme.neonCyan, fontWeight: FontWeight.bold, letterSpacing: 1),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
