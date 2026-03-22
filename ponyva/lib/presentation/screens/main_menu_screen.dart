import 'package:flutter/material.dart';
import '../../core/tokens.dart';
import 'match_screen.dart';
import 'deck_builder_screen.dart';

class MainMenuScreen extends StatelessWidget {
  const MainMenuScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Scaffold(
      body: Stack(
        children: [
          // Background Illustration Placeholder (Opacity 10%)
          Positioned.fill(
            child: Container(
              color: AppColors.background,
              child: Opacity(
                opacity: 0.1,
                child: Image.network(
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuBULXwYYqKwuD6aODbST8tAgs2eEMfnhTkOF_K7LUi7JfUX99oCGx1ATi5mY_Cd3vu4BiSAETRciDZopxF774J7CEBC7fcM4GIssPUK9ACvs4getENUrSzPfj_EaIXed2JIby7WEGrOb799JsH8RAvThSWAGOrNpnr5NgyEOTGfZFOvvcHcGMp_bEVkLVHD9a3UfSEEJRw68RTshn7yfAPpvV-xHZ_DiAF-HBzAnMQ3lwMyYbS73KzykWaSpF3t3Tgk5AT6kBbPJA',
                  fit: BoxFit.cover,
                ),
              ),
            ),
          ),
          
          // Content
          SafeArea(
            child: Column(
              children: [
                // Top Bar
                Padding(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 56,
                            height: 56,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              border: Border.all(color: AppColors.primary, width: 2),
                              image: const DecorationImage(
                                image: NetworkImage('https://lh3.googleusercontent.com/aida-public/AB6AXuANXtGJagaTNFqE3-ASqqy7N5QWiDqDqXbwthOm9976xyJAwO7cz2LNioYLuGGNPtYgUlTmjCXL7pPoXGCG4mmq5e1QSq0HgETqpz5Wduk_85nh8nud0bx3VPBuUGfO0Tk6sra8g3nkoj_o-LYR0CTCE9QE4koY18fVMpibm7FrFC1-YZ_sOlMqyaae-WBdihd2QbZ7Q9bQiFN8fKiZcP7jHKsLKTd0nVOiTOK4TxHt5dp3hfaelszioF4iZxwM7JkHkCScbDCe5g'),
                                fit: BoxFit.cover,
                              ),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.md),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'CSABA THE BOLD',
                                style: theme.textTheme.headlineSmall?.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                              Text(
                                'LEVEL 24',
                                style: theme.textTheme.labelSmall?.copyWith(
                                  color: AppColors.secondary,
                                  letterSpacing: 2,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      
                      // Currency / XP
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceContainerLow.withOpacity(0.6),
                          borderRadius: BorderRadius.circular(AppRadius.xl),
                          border: Border.all(color: AppColors.outlineVariant.withOpacity(0.3)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.generating_tokens, color: AppColors.tertiary, size: 20),
                            const SizedBox(width: 4),
                            Text(
                              '1,250',
                              style: theme.textTheme.labelLarge?.copyWith(color: AppColors.tertiary),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                
                const Spacer(),
                
                // Menu Buttons
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
                  child: Column(
                    children: [
                      _MenuButton(
                        title: 'PLAY',
                        subtitle: 'Jump into a quick match with opponents',
                        color: AppColors.primaryContainer,
                        icon: Icons.bolt,
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const MatchScreen()),
                          );
                        },
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _MenuButton(
                        title: 'DECK BUILDER',
                        subtitle: 'Refine your strategy and card combos',
                        color: AppColors.secondaryContainer,
                        icon: Icons.style,
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const DeckBuilderScreen()),
                          );
                        },
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _MenuButton(
                        title: 'COLLECTION',
                        subtitle: 'Browse 142 unique grimoire entries',
                        color: AppColors.tertiaryContainer,
                        icon: Icons.auto_stories,
                        onPressed: () {},
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _MenuButton(
                        title: 'SETTINGS',
                        subtitle: 'Adjust audio, account, and gameplay',
                        color: AppColors.surfaceContainerLow,
                        icon: Icons.settings,
                        onPressed: () {},
                      ),
                    ],
                  ),
                ),
                
                const Spacer(),
                
                // Footer
                Container(
                  padding: const EdgeInsets.fromLTRB(AppSpacing.xxl, AppSpacing.lg, AppSpacing.xxl, AppSpacing.xl),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLow.withOpacity(0.95),
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(AppRadius.xl * 1.5)),
                    border: Border.all(color: AppColors.outlineVariant.withOpacity(0.2)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'NEWS & SEASON INFO',
                            style: theme.textTheme.labelSmall?.copyWith(
                              color: AppColors.secondary,
                              letterSpacing: 2.5,
                            ),
                          ),
                          const Icon(Icons.notifications_active, color: AppColors.secondary, size: 16),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Text(
                        'The Great Chili Harvest',
                        style: theme.textTheme.titleLarge?.copyWith(
                          color: AppColors.onSurface,
                        ),
                      ),
                      Text(
                        'Collect limited edition card sets now.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: AppColors.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MenuButton extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color color;
  final IconData icon;
  final VoidCallback onPressed;

  const _MenuButton({
    required this.title,
    required this.subtitle,
    required this.color,
    required this.icon,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return InkWell(
      onTap: onPressed,
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              offset: const Offset(0, 4),
              blurRadius: 8,
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
              child: Icon(icon, color: Colors.white, size: 28),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w900,
                      fontSize: 20,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.8),
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
