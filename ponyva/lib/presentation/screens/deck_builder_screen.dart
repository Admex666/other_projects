import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/tokens.dart';
import '../../domain/models/card_model.dart';
import '../../application/deck_provider.dart';
import '../widgets/game_card.dart';

class DeckBuilderScreen extends ConsumerStatefulWidget {
  const DeckBuilderScreen({super.key});

  @override
  ConsumerState<DeckBuilderScreen> createState() => _DeckBuilderScreenState();
}

class _DeckBuilderScreenState extends ConsumerState<DeckBuilderScreen> {

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final currentDeck = ref.watch(deckControllerProvider);
    final collection = ref.watch(cardCollectionProvider);
    final notifier = ref.read(deckControllerProvider.notifier);
    
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('GRIMOIRE DECK BUILDER', style: theme.textTheme.headlineSmall),
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.primary),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          TextButton(
            onPressed: () {},
            child: Text('FORGE', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w900)),
          ),
        ],
      ),
      body: Column(
        children: [
          // Deck Stats Bar
          _buildStatsBar(theme, currentDeck),
          
          // Current Deck (Horizontal)
          _buildCurrentDeckSection(theme, currentDeck, notifier),
          
          const Divider(color: AppColors.outlineVariant, height: 1),
          
          // Search & Filters
          _buildFilterBar(theme),
          
          // Collection Grid
          Expanded(
            child: _buildCollectionGrid(collection, notifier),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsBar(ThemeData theme, List<CardModel> currentDeck) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: AppColors.surfaceContainerLow.withOpacity(0.5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _statItem('CARDS', '${currentDeck.length}/30', AppColors.primary),
          _statItem('AVG MANA', '3.2', AppColors.tertiary),
          _statItem('WIN RATE', '68%', AppColors.secondary),
        ],
      ),
    );
  }

  Widget _statItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: AppColors.outline)),
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: color)),
      ],
    );
  }

  Widget _buildCurrentDeckSection(ThemeData theme, List<CardModel> currentDeck, DeckController controller) {
    return Container(
      height: 140,
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: currentDeck.isEmpty
          ? Center(child: Text('DRAG CARDS HERE', style: theme.textTheme.labelSmall?.copyWith(color: AppColors.outlineVariant)))
          : ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: currentDeck.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: GameCard(
                    card: currentDeck[index],
                    isSmall: true,
                    onTap: () => controller.removeCard(currentDeck[index].id),
                  ),
                );
              },
            ),
    );
  }

  Widget _buildFilterBar(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          TextField(
            decoration: InputDecoration(
              hintText: 'Search Card Lore...',
              prefixIcon: const Icon(Icons.search, color: AppColors.outline),
              filled: true,
              fillColor: AppColors.surfaceContainerLow,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(AppRadius.md), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _filterChip('All Factions', true),
                _filterChip('Betyár', false),
                _filterChip('Sárkány', false),
                _filterChip('Characters', false),
                _filterChip('Events', false),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label, bool isSelected) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isSelected ? AppColors.primaryContainer : AppColors.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(AppRadius.full),
        border: Border.all(color: isSelected ? AppColors.primary : AppColors.outlineVariant.withOpacity(0.3)),
      ),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: isSelected ? AppColors.onPrimaryContainer : AppColors.onSurface,
        ),
      ),
    );
  }

  Widget _buildCollectionGrid(List<CardModel> collection, DeckController controller) {
    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 0.7,
        crossAxisSpacing: 16,
        mainAxisSpacing: 16,
      ),
      itemCount: collection.length,
      itemBuilder: (context, index) {
        return GameCard(
          card: collection[index],
          onTap: () => controller.addCard(collection[index]),
        );
      },
    );
  }
}
