import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/game_manager.dart';
import '../theme.dart';
import '../models/game_data.dart';
import 'shop_screen.dart';
import 'widgets/chunky_card.dart';
import 'widgets/chunky_button.dart';
import 'widgets/cyber_loader.dart';
import 'widgets/coin_vfx.dart';
import 'chest_opening_dialog.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({super.key});

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GameManager>().fetchShopCatalog();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GameManager>(
      builder: (context, game, child) {
        // --- PURCHASE RESULT HANDLING ---
        if (game.lastPurchaseResult != null) {
          final res = game.lastPurchaseResult!;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (res['success'] == true) {
              if (res['rewards'] != null) {
                // Show Chest Animation
                showDialog(
                  context: context,
                  barrierDismissible: false,
                  builder: (_) => ChestOpeningDialog(rewards: res['rewards']),
                );
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("PURCHASE SUCCESSFUL!")),
                );
              }
            } else {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(res['message'] ?? "PURCHASE FAILED")),
              );
            }
            game.clearPurchaseResult();
          });
        }

        return Scaffold(
          backgroundColor: AppTheme.backgroundDarkNavy,
          body: CustomScrollView(
            slivers: [
              _buildAppBar(game),
              if (game.isShopLoading)
                const SliverFillRemaining(
                  child: Center(child: CyberLoader(label: "SYNCING CATALOG")),
                )
              else ...[
                _buildSectionHeader("DAILY CHESTS"),
                _buildChestsSection(game),
                _buildSectionHeader("DOT SKINS"),
                _buildSkinsSection(game),
                _buildSectionHeader("TRAILS & FX"),
                _buildTrailsSection(game),
                _buildSectionHeader("LANDING ANIMATIONS"),
                _buildAnimationsSection(game),
                const SliverToBoxAdapter(child: SizedBox(height: 100)),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildAppBar(GameManager game) {
    return const SliverAppBar(
      backgroundColor: Colors.transparent,
      floating: true,
      pinned: false,
      title: Text("SHOP", style: TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 24)),
    );
  }

  Widget _buildSectionHeader(String title) {
    return SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 12),
        child: Text(title, style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.w900, letterSpacing: 1.5, fontSize: 12)),
      ),
    );
  }

  Widget _buildChestsSection(GameManager game) {
    final chests = game.shopCatalog.where((i) => i.type == 'chest').toList();
    return SliverToBoxAdapter(
      child: SizedBox(
        height: 220,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          itemCount: chests.length,
          itemBuilder: (context, index) {
            return _buildChestCard(chests[index], game);
          },
        ),
      ),
    );
  }

  Widget _buildChestCard(ShopItem item, GameManager game) {
    return Container(
      width: 170,
      margin: const EdgeInsets.symmetric(horizontal: 6),
      child: ChunkyCard(
        baseColor: const Color(0xFF1E1E3C),
        shadowColor: Colors.black,
        borderColor: AppTheme.goldCoin.withOpacity(0.4),
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Icon(Icons.inventory_2, color: AppTheme.goldCoin, size: 70),
            const SizedBox(height: 12),
            Text(
              item.name.toUpperCase(), 
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 1, color: Colors.white70),
              textAlign: TextAlign.center,
            ),
            const Spacer(),
            _buildBuyButton(item, game),
          ],
        ),
      ),
    );
  }

  Widget _buildSkinsSection(GameManager game) {
    final skins = game.shopCatalog.where((i) => i.type == 'skin').toList();
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.8,
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) => _buildSkinCard(skins[index], game),
          childCount: skins.length,
        ),
      ),
    );
  }

  Widget _buildTrailsSection(GameManager game) {
    final trails = game.shopCatalog.where((i) => i.type == 'trail').toList();
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.8,
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) => _buildSkinCard(trails[index], game),
          childCount: trails.length,
        ),
      ),
    );
  }

  Widget _buildAnimationsSection(GameManager game) {
    final anims = game.shopCatalog.where((i) => i.type == 'animation').toList();
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.8,
          mainAxisSpacing: 8,
          crossAxisSpacing: 8,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) => _buildSkinCard(anims[index], game),
          childCount: anims.length,
        ),
      ),
    );
  }

  Widget _buildSkinCard(ShopItem item, GameManager game) {
    final bool owned = game.userStats?.inventory.contains(item.id) ?? false;
    final bool equipped = (game.userStats?.equippedSkin == item.id) || 
                         (game.userStats?.equippedTrail == item.id) ||
                         (game.userStats?.equippedAnimation == item.id);
    
    return ChunkyCard(
      baseColor: const Color(0xFF1A1A33),
      shadowColor: Colors.black,
      borderColor: equipped ? AppTheme.neonCyan : AppTheme.purpleGlow.withOpacity(0.2),
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          Expanded(
            child: Center(
              child: Icon(
                item.type == 'skin' ? Icons.circle_outlined : Icons.auto_awesome, 
                color: item.rarity == 'legendary' ? Colors.orange : AppTheme.neonCyan, 
                size: 40
              ),
            ),
          ),
          const SizedBox(height: 8),
          // The following variables (sliderVal, minBet, maxBet) are not defined in the provided context.
          // Assuming they would be defined elsewhere or are placeholders for a different context.
          // For the purpose of this edit, they are included as requested.
          // CyberSlider(
          //   value: sliderVal,
          //   min: minBet.toDouble(),
          //   max: maxBet.toDouble(),
          //   divisions: (maxBet - minBet) > 0 ? (maxBet - minBet) : 1,
          //   onChanged: (val) => game.setBetAmount(val.round()),
          // ),
          // const SizedBox(height: 12),
          Text(item.name.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 12),
          if (owned)
            ChunkyButton(
              onTap: equipped ? null : () => game.equipItem(item.id),
              baseColor: equipped ? Colors.white10 : AppTheme.neonCyan.withOpacity(0.2),
              shadowColor: Colors.black,
              width: double.infinity,
              height: 36,
              padding: EdgeInsets.zero,
              child: Center(child: Text(equipped ? "EQUIPPED" : "EQUIP", style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold))),
            )
          else
            _buildBuyButton(item, game),
        ],
      ),
    );
  }

  Widget _buildBuyButton(ShopItem item, GameManager game) {
    final Color color = item.currency == 'gold' ? AppTheme.goldCoin : AppTheme.purpleGlow;
    return ChunkyButton(
      onTap: () => _showPurchaseDialog(context, item, game),
      baseColor: color.withOpacity(0.2),
      shadowColor: Colors.black,
      width: double.infinity,
      height: 36,
      borderColor: color,
      padding: EdgeInsets.zero,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(item.currency == 'gold' ? Icons.monetization_on : Icons.diamond, color: color, size: 12),
          const SizedBox(width: 4),
          Text(item.price.toString(), style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 12)),
        ],
      ),
    );
  }

  void _showPurchaseDialog(BuildContext context, ShopItem item, GameManager game) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF151525),
        title: Text("BUY ${item.name.toUpperCase()}?", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900)),
        content: Text("Are you sure you want to spend ${item.price} ${item.currency}?", style: const TextStyle(color: Colors.white70)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("CANCEL", style: TextStyle(color: Colors.white38))),
          TextButton(
            onPressed: () {
              // Trigger Coin VFX before closing
              CoinVFX.show(
                context: context, 
                source: Offset(MediaQuery.of(context).size.width / 2, MediaQuery.of(context).size.height / 2),
                target: const Offset(300, 40), // Towards Top Bar
              );
              game.purchaseItem(item.id);
              Navigator.pop(context);
            },
            child: Text("PURCHASE", style: TextStyle(color: item.currency == 'gold' ? AppTheme.goldCoin : AppTheme.purpleGlow, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}
