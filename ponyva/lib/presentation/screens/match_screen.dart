import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/tokens.dart';
import '../../domain/models/card_model.dart';
import '../../domain/models/player_model.dart';
import '../../domain/models/match_model.dart';
import '../../application/match_provider.dart';
import '../widgets/game_card.dart';

class MatchScreen extends ConsumerStatefulWidget {
  const MatchScreen({super.key});

  @override
  ConsumerState<MatchScreen> createState() => _MatchScreenState();
}

class _MatchScreenState extends ConsumerState<MatchScreen> {
  // Dummy Hand for interaction if the actual hand is empty
  final List<CardModel> dummyHand = [
    const CardModel(
      id: 'h1',
      name: 'The Cunning Fox',
      description: 'A sly creature of the woods.',
      type: CardType.character,
      rarity: CardRarity.rare,
      faction: Faction.folk,
      attack: 4,
      hp: 6,
      luck: 5,
      stability: 8,
      manaCost: 3,
      imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDjkBr4T543SoWv7BX2zEEqGQacdnNtzQwH5trtQsTG8OpifRDe3uekdiO4E8OSeRNqvdMgkf2N-QmanTP8jiBf4TAYOThepji_3y2_q3dokTKaUyXIRUDdPJ775gq-Xs8SPOsBsZQ23TrZNnvJwuJyVq9W2KqrP5OQExhP4s4kfoG5y4K5UWpaz0l7qCvfS3xYrpuqTG6n9DcxmVLQ_CtvnlmkTf48M12troOweVYAE_N4pC7EVqtuKBqnZikCA7B1FCeCqzXJ5A',
    ),
    const CardModel(
      id: 'h2',
      name: 'Spicy Karma',
      description: 'Luck favored the bold, once.',
      type: CardType.event,
      rarity: CardRarity.legendary,
      faction: Faction.punk,
      attack: 0,
      hp: 0,
      luck: 10,
      stability: 2,
      manaCost: 2,
      imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDE4J22HAsQtLKko1ndCc7lB-TfoVC_kuSgeO4JkNoVAM2Q6avh31PJ6NX3W--v83Dk9rPaAfFsAC8PsCvYF9DhUG2MKQXvk9aiCWs8AuMXYweLuGi48RIaLRKchGh_jWNfWhycis6jvdlRRJY7kgNIfLI4XITlhp1oQtqCCyhJH37jsNUOI8XIHh6bbTZ_t8k_DRjYOEFCipBmuvAFdNOx6URkitLulavh3rDJZ3UHVFy-dlL4Fwjvj_AnY1_0c_ti6spunu-0zA',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final match = ref.watch(matchControllerProvider);
    final controller = ref.read(matchControllerProvider.notifier);
    
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        children: [
          // Texture Overlay
          Positioned.fill(
            child: Opacity(
              opacity: 0.05,
              child: Image.network(
                'https://lh3.googleusercontent.com/aida-public/AB6AXuBehVABAc0tLk36vqbrsTCtsPUtL6CtFZGBsjtgsWloToyBfYpoBfNpSsXUOtzmNde516B4KCzuTjlrqcF7IAVTrSWCAHU2jBkvRrRtiGwMhqbLanAWnJlLRh5lxtIWLO-7Fo129lUaYAj3L5PiIrtHXhEtBaGYp_COO2yhPH-0ACAzZVPYwYBX7NcsMYQ6AjXwZ_N3w9AU3n5iKcYpvm1flTd4TPtvrg-45wB5TH7KfRzsd-LG8C_CstQTJLgJYcK09X-gmiodTg',
                fit: BoxFit.cover,
              ),
            ),
          ),
          
          SafeArea(
            child: Column(
              children: [
                // 1. Top HUD (Opponent Info)
                _buildOpponentHUD(theme, match.opponent),
                
                const Spacer(),
                
                // 2. Battle Board
                _buildBoard(theme, match),
                
                const Spacer(),
                
                // 3. Player Zone
                _buildPlayerHUD(theme, match.player),
                
                // 4. Hand
                _buildHand(match.playerHand.isEmpty ? dummyHand : match.playerHand, controller),
                
                // 5. Bottom Controls
                _buildBottomControls(theme, match, controller),
              ],
            ),
          ),
          
          // Action Log (Floating Right)
          _buildActionLog(theme, match.matchLog),
          
          // Turn Indicator (Top Left)
          Positioned(
            top: 16,
            left: 16,
            child: _buildTurnIndicator(theme, match),
          ),
        ],
      ),
    );
  }

  Widget _buildTurnIndicator(ThemeData theme, MatchModel match) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow.withOpacity(0.8),
        borderRadius: BorderRadius.circular(AppRadius.full),
        border: Border.all(color: AppColors.outlineVariant.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              color: AppColors.primaryContainer,
              shape: BoxShape.circle,
            ),
            child: const Center(
              child: Text(
                '15',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 12),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                match.isPlayerTurn ? 'YOUR TURN' : 'OPPONENT TURN',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: match.isPlayerTurn ? AppColors.primary : AppColors.outline,
                  letterSpacing: 2,
                ),
              ),
              Row(
                children: [
                  Container(width: 8, height: 8, decoration: BoxDecoration(color: match.isPlayerTurn ? AppColors.primary : AppColors.outlineVariant, shape: BoxShape.circle)),
                  const SizedBox(width: 4),
                  Container(width: 8, height: 8, decoration: BoxDecoration(color: !match.isPlayerTurn ? AppColors.primary : AppColors.outlineVariant, shape: BoxShape.circle)),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildOpponentHUD(ThemeData theme, PlayerModel opponent) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerHigh,
              borderRadius: BorderRadius.circular(AppRadius.md),
              border: Border.all(color: AppColors.primary.withOpacity(0.2), width: 2),
            ),
            child: const Icon(Icons.person, color: Colors.grey, size: 40),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      opponent.name.toUpperCase(),
                      style: theme.textTheme.labelSmall?.copyWith(color: AppColors.outline, letterSpacing: 1.5),
                    ),
                    Row(
                      children: [
                        const Icon(Icons.shield, color: AppColors.tertiary, size: 14),
                        const SizedBox(width: 4),
                        Text(opponent.hp.toString(), style: theme.textTheme.labelLarge),
                        const SizedBox(width: 12),
                        const Icon(Icons.auto_awesome, color: AppColors.secondary, size: 14),
                        const SizedBox(width: 4),
                        Text(opponent.stability.toString(), style: theme.textTheme.labelLarge),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.full),
                  child: LinearProgressIndicator(
                    value: opponent.hp / opponent.maxHp,
                    minHeight: 12,
                    backgroundColor: AppColors.surfaceContainerLow,
                    valueColor: const AlwaysStoppedAnimation(AppColors.primaryContainer),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBoard(ThemeData theme, MatchModel match) {
    return Container(
      height: 240,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        children: [
          // Opponent Board
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(3, (index) {
              final card = match.opponentBoard.length > index ? match.opponentBoard[index] : null;
              return Container(
                width: 90,
                height: 110,
                margin: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerLow.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(AppRadius.md),
                  border: Border.all(color: AppColors.outlineVariant.withOpacity(0.2)),
                ),
                child: card != null 
                  ? GameCard(card: card, isSmall: true)
                  : const SizedBox(),
              );
            }),
          ),
          const SizedBox(height: 8),
          // Player Board
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(3, (index) {
              final card = match.playerBoard.length > index ? match.playerBoard[index] : null;
              return Container(
                width: 90,
                height: 110,
                margin: const EdgeInsets.symmetric(horizontal: 4),
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerLow.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(AppRadius.md),
                  border: Border.all(color: AppColors.outlineVariant.withOpacity(0.2)),
                ),
                child: card != null 
                  ? GameCard(card: card, isSmall: true)
                  : Center(
                      child: Icon(Icons.add, color: AppColors.outlineVariant.withOpacity(0.1)),
                    ),
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayerHUD(ThemeData theme, PlayerModel player) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.favorite, color: AppColors.tertiary, size: 14),
                        const SizedBox(width: 4),
                        Text(player.hp.toString(), style: theme.textTheme.labelLarge),
                        const SizedBox(width: 12),
                        const Icon(Icons.psychology_alt, color: AppColors.secondary, size: 14),
                        const SizedBox(width: 4),
                        Text(player.stability.toString(), style: theme.textTheme.labelLarge),
                      ],
                    ),
                    Text(
                      player.name.toUpperCase(),
                      style: theme.textTheme.labelSmall?.copyWith(color: AppColors.secondary, letterSpacing: 1.5),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.full),
                  child: LinearProgressIndicator(
                    value: player.hp / player.maxHp,
                    minHeight: 12,
                    backgroundColor: AppColors.surfaceContainerLow,
                    valueColor: const AlwaysStoppedAnimation(AppColors.secondaryContainer),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerHigh,
              borderRadius: BorderRadius.circular(AppRadius.md),
              border: Border.all(color: AppColors.secondary.withOpacity(0.2), width: 2),
              image: player.avatarUrl != null ? DecorationImage(image: NetworkImage(player.avatarUrl!), fit: BoxFit.cover) : null,
            ),
            child: player.avatarUrl == null ? const Icon(Icons.face, color: AppColors.secondary, size: 40) : null,
          ),
        ],
      ),
    );
  }

  Widget _buildHand(List<CardModel> hand, MatchController controller) {
    return SizedBox(
      height: 180,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 8),
        itemCount: hand.length,
        itemBuilder: (context, index) {
          return Padding(
            padding: const EdgeInsets.only(right: 16.0),
            child: GameCard(
              card: hand[index],
              onTap: () => controller.playCard(hand[index]),
            ),
          );
        },
      ),
    );
  }

  Widget _buildBottomControls(ThemeData theme, MatchModel match, MatchController controller) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF221A15).withOpacity(0.95),
        border: const Border(top: BorderSide(color: AppColors.outlineVariant, width: 0.2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('ACTION POINTS', style: theme.textTheme.labelSmall?.copyWith(color: AppColors.outline)),
                  const SizedBox(height: 4),
                  Row(
                    children: List.generate(match.player.maxActionPoints, (index) {
                      return Padding(
                        padding: const EdgeInsets.only(right: 6.0),
                        child: CircleAvatar(
                          radius: 6,
                          backgroundColor: index < match.player.actionPoints ? AppColors.tertiary : AppColors.outlineVariant,
                        ),
                      );
                    }),
                  ),
                ],
              ),
              const SizedBox(width: 24),
              const VerticalDivider(color: Colors.white24, width: 1),
              const SizedBox(width: 24),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('MANA', style: theme.textTheme.labelSmall?.copyWith(color: AppColors.outline)),
                  const SizedBox(height: 4),
                  Text('${match.player.mana} / ${match.player.maxMana}', style: theme.textTheme.headlineSmall?.copyWith(color: AppColors.secondary, fontSize: 18)),
                ],
              ),
            ],
          ),
          ElevatedButton.icon(
            onPressed: () => controller.endTurn(),
            style: ElevatedButton.styleFrom(
              backgroundColor: match.isPlayerTurn ? AppColors.primaryContainer : AppColors.surfaceContainerLow,
              foregroundColor: match.isPlayerTurn ? AppColors.onPrimaryContainer : AppColors.outline,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppRadius.full)),
            ),
            icon: const Icon(Icons.bolt, size: 18),
            label: Text(match.isPlayerTurn ? 'END TURN' : 'WAITING...', style: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 2)),
          ),
        ],
      ),
    );
  }

  Widget _buildActionLog(ThemeData theme, List<String> log) {
    return Positioned(
      right: 16,
      top: 240,
      child: Container(
        width: 160,
        height: 120,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.surfaceContainerLow.withOpacity(0.8),
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.outlineVariant.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.history, color: AppColors.tertiary, size: 12),
                const SizedBox(width: 4),
                Text('ACTION LOG', style: theme.textTheme.labelSmall?.copyWith(color: AppColors.outline, fontSize: 8)),
              ],
            ),
            const Divider(color: Colors.white10),
            Expanded(
              child: ListView.builder(
                itemCount: log.length,
                reverse: true,
                itemBuilder: (context, index) {
                  final reversedIndex = log.length - 1 - index;
                  return _logEntry(log[reversedIndex], AppColors.primary);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _logEntry(String text, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(width: 2, height: 12, color: color.withOpacity(0.4)),
          const SizedBox(width: 6),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 9, color: AppColors.onSurfaceVariant))),
        ],
      ),
    );
  }
}
