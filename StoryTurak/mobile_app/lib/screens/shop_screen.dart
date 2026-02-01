import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../models/keldor_models.dart';
import '../theme.dart';

class ShopScreen extends StatefulWidget {
  const ShopScreen({Key? key}) : super(key: key);

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Item> _merchantItems = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadMerchantItems();
  }

  Future<void> _loadMerchantItems() async {
    final token = context.read<AuthService>().token;
    if (token != null) {
      final items = await context.read<KeldorService>().fetchMerchantItems(token);
      if (mounted) {
        setState(() {
          _merchantItems = items;
          _isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final char = context.watch<KeldorService>().activeCharacter;

    return Scaffold(
      backgroundColor: KeldorTheme.background,
      appBar: AppBar(
        title: const Text("Kereskedő", style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        bottom: TabBar(
            controller: _tabController,
            indicatorColor: KeldorTheme.primary,
            labelColor: KeldorTheme.primary,
            unselectedLabelColor: Colors.white54,
            tabs: const [
                Tab(text: "VÁSÁRLÁS"),
                Tab(text: "ELADÁS"),
            ],
        ),
      ),
      body: char == null ? const Center(child: CircularProgressIndicator()) : TabBarView(
        controller: _tabController,
        children: [
            _buildBuyTab(char),
            _buildSellTab(char),
        ],
      ),
    );
  }

  Widget _buildBuyTab(Character char) {
      if (_isLoading) return const Center(child: CircularProgressIndicator());
      
      return Column(
          children: [
              _buildCurrencyHeader(char),
              Expanded(
                  child: ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _merchantItems.length,
                      itemBuilder: (ctx, index) {
                          final item = _merchantItems[index];
                          final rarityColor = _getRarityColor(item.rarity);
                          final isCommon = rarityColor == Colors.white10;

                          return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              decoration: BoxDecoration(
                                  color: isCommon ? KeldorTheme.surface : rarityColor.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: isCommon ? Colors.white12 : rarityColor.withOpacity(0.5)),
                              ),
                              child: ListTile(
                                  leading: _buildItemIcon(item.iconCode, isCommon ? Colors.white70 : rarityColor, 32),
                                  title: Text(item.name, style: TextStyle(color: isCommon ? Colors.white : rarityColor, fontWeight: FontWeight.bold)),
                                  subtitle: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                          Text(item.description, style: const TextStyle(color: Colors.white54, fontSize: 12)),
                                          const SizedBox(height: 4),
                                          Text(item.rarity.toUpperCase(), style: TextStyle(color: isCommon ? Colors.white24 : rarityColor, fontSize: 10, letterSpacing: 1.5, fontWeight: FontWeight.bold)),
                                      ],
                                  ),
                                  trailing: ElevatedButton(
                                      onPressed: () => _buyItem(item),
                                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                      child: Text("${item.value} P", style: const TextStyle(color: Colors.white)),
                                  ),
                              ),
                          );
                      },
                  ),
              )
          ],
      );
  }

  Widget _buildSellTab(Character char) {
      final sellable = char.inventory.where((i) => !i.equipped).toList();

      return Column(
          children: [
              _buildCurrencyHeader(char),
              Expanded(
                  child: sellable.isEmpty 
                    ? const Center(child: Text("Nincs eladható tárgyad.", style: TextStyle(color: Colors.white54)))
                    : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: sellable.length,
                      itemBuilder: (ctx, index) {
                          final slot = sellable[index];
                          final rarityColor = _getRarityColor(slot.rarity);
                          final isCommon = rarityColor == Colors.white10;
                          
                          int sellPrice = (slot.value > 0 ? slot.value * 0.5 : 10).toInt(); // Fallback if 0

                          return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              decoration: BoxDecoration(
                                  color: isCommon ? KeldorTheme.surface : rarityColor.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: isCommon ? Colors.white12 : rarityColor.withOpacity(0.5)),
                              ),
                              child: ListTile(
                                  leading: _buildItemIcon(slot.iconCode ?? 'circle', isCommon ? Colors.white70 : rarityColor, 32),
                                  title: Text(slot.name ?? "Ismeretlen", style: TextStyle(color: isCommon ? Colors.white : rarityColor, fontWeight: FontWeight.bold)),
                                  subtitle: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                          Text("${slot.quantity} db", style: const TextStyle(color: Colors.white54)),
                                          Text(slot.rarity.toUpperCase(), style: TextStyle(color: isCommon ? Colors.white24 : rarityColor, fontSize: 10, letterSpacing: 1.5, fontWeight: FontWeight.bold)),
                                      ],
                                  ),
                                  trailing: ElevatedButton(
                                      onPressed: () => _sellItem(slot),
                                      style: ElevatedButton.styleFrom(backgroundColor: Colors.orangeAccent),
                                      child: Text("Eladás ($sellPrice P)", style: const TextStyle(color: Colors.black)),
                                  ),
                              ),
                          );
                      },
                  ),
              )
          ],
      );
  }

  Color _getRarityColor(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'uncommon': return Colors.greenAccent;
      case 'rare': return Colors.blueAccent;
      case 'epic': return Colors.purpleAccent;
      case 'legendary': return Colors.orangeAccent;
      default: return Colors.white10;
    }
  }

  Widget _buildItemIcon(String code, Color color, double size) {
      IconData icon = Icons.circle;
       switch (code) {
          case 'local_pharmacy': icon = Icons.local_pharmacy; break;
          case 'monetization_on': icon = Icons.monetization_on; break;
          case 'security': icon = Icons.security; break;
          case 'build': icon = Icons.build; break;
          case 'architecture': icon = Icons.architecture; break;
          case 'explore': icon = Icons.explore; break;
          case 'offline_bolt': icon = Icons.offline_bolt; break;
          case 'confirmation_number': icon = Icons.confirmation_number; break;
          case 'cookie': icon = Icons.cookie; break;
          case 'help_outline': icon = Icons.help_outline; break;
      }
      return Icon(icon, color: color, size: size);
  }

  Widget _buildCurrencyHeader(Character char) {
      return Container(
          padding: const EdgeInsets.all(16),
          color: Colors.black26,
          child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                  const Icon(Icons.monetization_on, color: Colors.amber),
                  const SizedBox(width: 8),
                  Text("Egyenleg: ${char.currency} Pengő", style: const TextStyle(color: Colors.amber, fontSize: 18, fontWeight: FontWeight.bold)),
              ],
          ),
      );
  }

  void _buyItem(Item item) async {
       final token = context.read<AuthService>().token;
       if (token == null) return;
       
       bool success = await context.read<KeldorService>().buyItem(token, item.id, 1);
       if (success) {
           ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Sikeres vásárlás: ${item.name}!"), backgroundColor: Colors.green));
           // Currency updates automatically via fetchUserCharacter in Service
       } else {
           ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Sikertelen vásárlás! Nincs elég pénzed?"), backgroundColor: Colors.red));
       }
  }

  void _sellItem(InventorySlot slot) async {
       final token = context.read<AuthService>().token;
       if (token == null) return;

       bool success = await context.read<KeldorService>().sellItem(token, slot.itemId, 1);
       if (success) {
           ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Eladtad: ${slot.name}!"), backgroundColor: Colors.green));
       } else {
           ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Hiba az eladáskor!"), backgroundColor: Colors.red));
       }
  }
}
