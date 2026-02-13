import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../models/keldor_models.dart';
import '../theme.dart';
import '../widgets/keldor_item_tile.dart';

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

                            return KeldorItemTile.fromItem(
                                item,
                                trailing: ElevatedButton(
                                    onPressed: () => _buyItem(item),
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                                    child: Text("${item.value} P", style: const TextStyle(color: Colors.white)),
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
                            int sellPrice = (slot.value > 0 ? slot.value * 0.5 : 10).toInt(); // Fallback if 0

                            return KeldorItemTile.fromSlot(
                                slot,
                                trailing: ElevatedButton(
                                    onPressed: () => _sellItem(slot),
                                    style: ElevatedButton.styleFrom(backgroundColor: Colors.orangeAccent),
                                    child: Text("Eladás ($sellPrice P)", style: const TextStyle(color: Colors.black)),
                                ),
                            );
                        },
                    ),
                )
            ],
        );
    }

  // Remove `_getRarityColor` and `_buildItemIcon`


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
