import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../theme.dart';
import '../models/keldor_models.dart';

class CharacterScreen extends StatefulWidget {
  const CharacterScreen({Key? key}) : super(key: key);

  @override
  State<CharacterScreen> createState() => _CharacterScreenState();
}

class _CharacterScreenState extends State<CharacterScreen> {

  @override
  void initState() {
    super.initState();
    // Refresh character data on entering screen
    WidgetsBinding.instance.addPostFrameCallback((_) {
        final token = context.read<AuthService>().token;
        if (token != null) {
            context.read<KeldorService>().fetchUserCharacter(token);
        }
    });
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<KeldorService>();
    final char = service.activeCharacter;
    final activeQuests = service.activeQuests;

    if (char == null) {
      return const Scaffold(
        backgroundColor: KeldorTheme.background,
        body: Center(child: CircularProgressIndicator(color: KeldorTheme.primary)),
      );
    }

    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: KeldorTheme.background,
        appBar: AppBar(
          title: Text(char.name),
          backgroundColor: KeldorTheme.background,
          elevation: 0,
          centerTitle: true,
          bottom: const TabBar(
            indicatorColor: KeldorTheme.primary,
            labelColor: KeldorTheme.primary,
            unselectedLabelColor: Colors.white54,
            tabs: [
              Tab(text: "Profil", icon: Icon(Icons.person)),
              Tab(text: "Hátizsák", icon: Icon(Icons.backpack)),
              Tab(text: "Napló", icon: Icon(Icons.book)),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            // Tab 1: Profile (Stats)
            SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                    children: [
                        _buildProfileHeader(char),
                        const SizedBox(height: 24),
                        // Combat Stats
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                             color: KeldorTheme.surface,
                             borderRadius: BorderRadius.circular(12),
                             border: Border.all(color: Colors.white10),
                          ),
                          child: _buildCombatStats(char),
                        ),
                        const SizedBox(height: 24),
                        
                        _buildStatCard("Életerő", "${char.currentHp} / ${char.maxHp}", Icons.favorite),
                        const SizedBox(height: 8),
                        _buildStatCard("XP (Tapasztalat)", "${char.xp}", Icons.star), // Steps is still primary progression? Or XP?
                        const SizedBox(height: 8),
                        _buildStatCard("Heti Lépés", "${char.weeklySteps}", Icons.calendar_today),
                        const SizedBox(height: 24),
                        OutlinedButton.icon(
                            onPressed: () {
                                context.read<KeldorService>().clearActiveCharacter();
                            },
                            icon: const Icon(Icons.people, color: KeldorTheme.primary),
                            label: const Text("Karakterváltás / Új Karakter", style: TextStyle(color: KeldorTheme.primary)),
                            style: OutlinedButton.styleFrom(
                                side: const BorderSide(color: KeldorTheme.primary),
                                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12)
                            ),
                        ),
                    ],
                ),
            ),

            // Tab 2: Inventory
            SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: char.inventory.isEmpty 
                    ? _buildEmptyState("Üres a zsákod, vándor.") 
                    : GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 4, crossAxisSpacing: 8, mainAxisSpacing: 8),
                        itemCount: char.inventory.length,
                        itemBuilder: (ctx, index) {
                            final slot = char.inventory[index];
                            final rarityColor = _getRarityColor(slot.rarity);
                            
                            return InkWell(
                                onTap: () {
                                    showDialog(
                                        context: context, 
                                        builder: (ctx) => AlertDialog(
                                            backgroundColor: KeldorTheme.surface,
                                            title: Text(slot.name ?? "Ismeretlen Tárgy", style: TextStyle(color: rarityColor == Colors.white10 ? Colors.white : rarityColor)),
                                            content: Column(
                                                mainAxisSize: MainAxisSize.min,
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                    if (slot.iconCode != null) 
                                                        Center(child: Icon(
                                                            slot.iconCode == 'local_pharmacy' ? Icons.local_pharmacy : 
                                                            slot.iconCode == 'monetization_on' ? Icons.monetization_on :
                                                            slot.iconCode == 'security' ? Icons.security :
                                                            slot.iconCode == 'build' ? Icons.build : Icons.help_outline, 
                                                            size: 48, 
                                                            color: rarityColor == Colors.white10 ? KeldorTheme.primary : rarityColor
                                                        )),
                                                    const SizedBox(height: 8),
                                                    Center(child: Text(slot.rarity.toUpperCase(), style: TextStyle(color: rarityColor, fontSize: 10, letterSpacing: 1.5, fontWeight: FontWeight.bold))),
                                                    const SizedBox(height: 16),
                                                    Text(slot.description ?? "Nincs leírás.", style: const TextStyle(color: Colors.white70)),
                                                    const SizedBox(height: 16),
                                                    if (slot.stats != null && slot.stats!.isNotEmpty) ...[
                                                        const Text("Tulajdonságok:", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                                        const SizedBox(height: 4),
                                                        ...slot.stats!.entries.map((e) => Text("- ${e.key}: ${e.value}", style: const TextStyle(color: Colors.white60))),
                                                        const SizedBox(height: 8),
                                                    ],
                                                    if (slot.effects.isNotEmpty) ...[
                                                        const Text("Effektek:", style: TextStyle(color: Colors.amber, fontWeight: FontWeight.bold)),
                                                        const SizedBox(height: 4),
                                                         ...slot.effects.map((e) {
                                                             // effect is usually a Map {"type":..., "value":...}
                                                             final txt = e is Map ? (e['type'] ?? 'Unknown') : e.toString();
                                                             return Text("- $txt", style: const TextStyle(color: Colors.amberAccent));
                                                         }),
                                                    ]
                                                ],
                                            ),
                                            actions: [
                                                if (slot.stats != null && slot.stats!.containsKey('loot_table_id'))
                                                    TextButton(
                                                        onPressed: () {
                                                            Navigator.of(ctx).pop();
                                                            _openLootBox(slot);
                                                        },
                                                        child: const Text("KINYITÁS", style: TextStyle(color: Colors.amber, fontWeight: FontWeight.bold)),
                                                    ),
                                                
                                                if (slot.stats != null && slot.stats!.containsKey('hp_restore'))
                                                     TextButton(
                                                        onPressed: () {
                                                            Navigator.of(ctx).pop();
                                                             _useConsumable(slot);
                                                        },
                                                        child: const Text("HASZNÁLAT", style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                                                    ),

                                                if (slot.equipped)
                                                  TextButton(
                                                      onPressed: () async {
                                                          Navigator.pop(ctx);
                                                          final token = context.read<AuthService>().token;
                                                          if (token != null) {
                                                              await context.read<KeldorService>().unequipItem(token, slot.itemId);
                                                          }
                                                      },
                                                      child: const Text("Levétel", style: TextStyle(color: Colors.orangeAccent)),
                                                  )
                                                else
                                                  TextButton(
                                                      onPressed: () async {
                                                          Navigator.pop(ctx);
                                                          final token = context.read<AuthService>().token;
                                                          if (token != null) {
                                                              await context.read<KeldorService>().equipItem(token, slot.itemId);
                                                          }
                                                      },
                                                      child: const Text("Felvétel", style: TextStyle(color: Colors.greenAccent)),
                                                  ),
                                                TextButton(
                                                    onPressed: () async {
                                                        Navigator.pop(ctx);
                                                        final token = context.read<AuthService>().token;
                                                        if (token != null) {
                                                            await context.read<KeldorService>().removeItem(token, slot.itemId, 1);
                                                        }
                                                    },
                                                    child: const Text("Eldobás (1)", style: TextStyle(color: Colors.redAccent)),
                                                ),
                                                TextButton(
                                                    onPressed: () => Navigator.pop(ctx),
                                                    child: const Text("Bezárás", style: TextStyle(color: Colors.white54)),
                                                )
                                            ],
                                        )
                                    );
                                },
                                child: Container(
                                    decoration: BoxDecoration(
                                        color: KeldorTheme.surface,
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(
                                            color: slot.equipped ? Colors.green : (rarityColor == Colors.white10 ? Colors.white10 : rarityColor.withOpacity(0.5)), 
                                            width: slot.equipped ? 2 : 1
                                        ),
                                    ),
                                    child: Column(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                            Icon(
                                              slot.iconCode == 'local_pharmacy' ? Icons.local_pharmacy : 
                                              slot.iconCode == 'monetization_on' ? Icons.monetization_on : 
                                              slot.iconCode == 'security' ? Icons.security :
                                              slot.iconCode == 'build' ? Icons.build : Icons.circle, 
                                              color: slot.equipped ? Colors.green : (rarityColor == Colors.white10 ? Colors.white70 : rarityColor)
                                            ),
                                            const SizedBox(height: 4),
                                            Text("${slot.quantity}x", style: const TextStyle(color: Colors.white)),
                                        ],
                                    ),
                                ),
                            );
                        },
                    ),
            ),

            // Tab 3: Quests (Journal)
            ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: activeQuests.length,
                itemBuilder: (ctx, index) {
                    final uq = activeQuests[index];
                    final isCompleted = uq.status == QuestStatus.completed;
                    
                    return Card(
                        color: KeldorTheme.surface,
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                            leading: Icon(
                                isCompleted ? Icons.check_circle : Icons.swap_vertical_circle,
                                color: isCompleted ? Colors.green : KeldorTheme.primary,
                            ),
                            title: Text(
                                uq.questTitle ?? "Ismeretlen Küldetés",
                                style: TextStyle(color: isCompleted ? Colors.grey : Colors.white, fontWeight: FontWeight.bold),
                            ),
                            subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                    if (uq.questDescription != null)
                                        Text(uq.questDescription!, style: TextStyle(color: Colors.white70, fontSize: 12)),
                                    const SizedBox(height: 4),
                                    Text(
                                        "Státusz: ${uq.status.toString().split('.').last.toUpperCase()}",
                                        style: TextStyle(color: isCompleted ? Colors.green : KeldorTheme.primary, fontSize: 10)
                                    ),
                                ],
                            ),
                            trailing: isCompleted ? null : const Icon(Icons.chevron_right, color: Colors.white24),
                        ),
                    );
                },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState(String msg) {
      return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(12)),
          child: Text(msg, style: const TextStyle(color: Colors.white54), textAlign: TextAlign.center),
      );
  }

  Widget _buildProfileHeader(char) {
      return Column(children: [
            Container(
                width: 100, height: 100,
                decoration: BoxDecoration(
                  color: KeldorTheme.primary.withOpacity(0.1),
                  shape: BoxShape.circle,
                  border: Border.all(color: KeldorTheme.primary, width: 2),
                ),
                child: Icon(_getClassIcon(char.characterClass), size: 50, color: KeldorTheme.primary),
            ),
            const SizedBox(height: 16),
            Text(
              "Szint: ${char.level} | ${char.characterClass.toString().split('.').last.toUpperCase()}",
              style: KeldorTheme.darkTheme.textTheme.displayLarge?.copyWith(
                  color: Colors.white70, fontWeight: FontWeight.bold
              ),
            ),
      ]);
  }

  Widget _buildStatCard(String label, String value, IconData icon) {
    return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
            color: KeldorTheme.surface,
            borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
            children: [
                Icon(icon, color: Colors.white54),
                const SizedBox(width: 16),
                Text(label, style: const TextStyle(color: Colors.white70)),
                const Spacer(),
                Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
            ],
        ),
    );
  }

  IconData _getClassIcon(CharacterClass cType) {
    switch (cType) {
      case CharacterClass.vigilante: return Icons.shield;
      case CharacterClass.collector: return Icons.backpack;
      case CharacterClass.archivist: return Icons.menu_book;
      default: return Icons.person;
    }
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

  Widget _buildCombatStats(Character char) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildCompactStat("Erő", char.stats['strength'] ?? 1, Icons.fitness_center, Colors.redAccent),
        _buildCompactStat("Ügyess.", char.stats['agility'] ?? 1, Icons.flash_on, Colors.greenAccent),
        _buildCompactStat("Taktika", char.stats['tactics'] ?? 1, Icons.psychology, Colors.blueAccent),
      ],
    );
  }

  Widget _buildCompactStat(String label, int value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 4),
        Text("$value", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
        Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12)),
      ],
    );
  }

  void _useConsumable(InventorySlot slot) async {
       final token = context.read<AuthService>().token;
       if (token == null) return;
       
       final result = await context.read<KeldorService>().useItem(token, slot.itemId);
       if (result != null && result['success']) {
           ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message']), backgroundColor: Colors.green));
       } else {
           ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Nem sikerült használni."), backgroundColor: Colors.red));
       }
  }

  void _openLootBox(InventorySlot slot) async {
       final token = context.read<AuthService>().token;
       if (token == null) return;
       
       // Show Loading / Animation Dialog
       showDialog(
           context: context,
           barrierDismissible: false,
           builder: (ctx) => const Center(child: CircularProgressIndicator(color: Colors.amber)),
       );

       // Delay for effect
       await Future.delayed(const Duration(seconds: 2));
       if (!mounted) return;
       
       final result = await context.read<KeldorService>().useItem(token, slot.itemId);
       Navigator.of(context).pop(); // Close loader

       if (result != null && result['success']) {
            final drops = (result['drops'] as List<dynamic>?)?.join(", ") ?? "Semmi";
            showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                    backgroundColor: Colors.black87,
                    title: const Text("Kincset találtál!", style: TextStyle(color: Colors.amber)),
                    content: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                            const Icon(Icons.stars, color: Colors.amber, size: 64),
                            const SizedBox(height: 16),
                            Text("Tartalom: $drops", style: const TextStyle(color: Colors.white, fontSize: 16)),
                        ],
                    ),
                    actions: [
                        TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text("Király!"))
                    ],
                )
            );
       } else {
           ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Hiba a nyitáskor."), backgroundColor: Colors.red));
       }
  }
}
