import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import '../models/game_data.dart';
import 'widgets/chunky_card.dart';
import 'widgets/chunky_button.dart';

class InventoryScreen extends StatelessWidget {
  const InventoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        final inventoryIds = game.userStats?.inventory ?? [];
        final ownedItems = game.shopCatalog.where((i) => inventoryIds.contains(i.id)).toList();

        return Scaffold(
          backgroundColor: AppTheme.backgroundDarkNavy,
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            title: const Text("MY INVENTORY", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2)),
          ),
          body: ownedItems.isEmpty
              ? _buildEmptyState()
              : ListView(
                  padding: const EdgeInsets.all(20),
                  children: [
                    _buildSection(context, "DOT SKINS", ownedItems.where((i) => i.type == 'skin').toList(), game),
                    const SizedBox(height: 24),
                    _buildSection(context, "TRAILS & FX", ownedItems.where((i) => i.type == 'trail').toList(), game),
                    const SizedBox(height: 24),
                    _buildSection(context, "LANDING ANIMATIONS", ownedItems.where((i) => i.type == 'animation').toList(), game),
                  ],
                ),
        );
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inventory_2_outlined, size: 80, color: Colors.white10),
          const SizedBox(height: 16),
          const Text("YOUR INVENTORY IS EMPTY", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title, List<ShopItem> items, GameManager game) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 1.5)),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 0.85,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
          ),
          itemCount: items.length,
          itemBuilder: (context, index) => _buildItemCard(items[index], game),
        ),
      ],
    );
  }

  Widget _buildItemCard(ShopItem item, GameManager game) {
    final bool equipped = (game.userStats?.equippedSkin == item.id) || 
                         (game.userStats?.equippedTrail == item.id) ||
                         (game.userStats?.equippedAnimation == item.id);

    return ChunkyCard(
      baseColor: const Color(0xFF1A1A33),
      shadowColor: Colors.black,
      borderColor: equipped ? AppTheme.neonCyan : Colors.white10,
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          Expanded(
            child: Center(
              child: Icon(
                item.type == 'skin' ? Icons.circle_outlined : Icons.auto_awesome, 
                color: equipped ? AppTheme.neonCyan : Colors.white24, 
                size: 40
              ),
            ),
          ),
          Text(item.name.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
          const SizedBox(height: 12),
          ChunkyButton(
            onTap: equipped ? null : () => game.equipItem(item.id),
            baseColor: equipped ? Colors.white10 : AppTheme.neonCyan.withOpacity(0.2),
            shadowColor: Colors.black,
            width: double.infinity,
            height: 32,
            padding: EdgeInsets.zero,
            child: Center(
              child: Text(
                equipped ? "EQUIPPED" : "EQUIP", 
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)
              )
            ),
          ),
        ],
      ),
    );
  }
}
