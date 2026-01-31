import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../theme.dart';
import '../models/keldor_models.dart';
import 'package:google_fonts/google_fonts.dart';
import 'faction_selection_screen.dart';

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
            context.read<KeldorService>().fetchQuestHistory(token);
        }
    });
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<KeldorService>();
    final char = service.activeCharacter;
    final activeQuests = service.activeQuests;
    final questHistory = service.questHistory;

    // Calculate Weekly Steps from Quest History
    int questStepSum = 0;
    for (var h in questHistory) {
      questStepSum += (h['rewards_steps'] as num? ?? 0).toInt();
    }
    // Only use char.weeklySteps if it's greater (e.g. from Pedometer), otherwise assume Quest Steps are the main source for now
    // Or just sum them? User implies "most hibásan 0 van", suggesting the DB field is empty but history should have it.
    // Let's display the calculated sum for clarity.
    final displaySteps = questStepSum; 

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
          title: Text(char.name, style: GoogleFonts.outfit(color: Colors.greenAccent, fontWeight: FontWeight.bold, fontSize: 24)),
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
                        _buildStatCard("XP (Tapasztalat)", "${char.xp}", Icons.star),
                        const SizedBox(height: 8),
                        _buildStatCard("Heti Lépés (Küldetésekből)", "$displaySteps", Icons.calendar_today),
                        
                        const SizedBox(height: 24),
                        _buildQuestHistorySection(questHistory),
                        
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
// ... (Inventory and Journal tabs remain same) ...
            // Tab 2: Inventory
            SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        _buildLoadoutSection(context, char),
                        const SizedBox(height: 24),
                        const Divider(color: Colors.white12),
                        const SizedBox(height: 16),
                        Text("Hátizsák", style: GoogleFonts.outfit(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 16),
                        _buildBackpackSection(context, char),
                    ],
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
                            trailing: isCompleted 
                                ? const Icon(Icons.check, color: Colors.green) 
                                : Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                        IconButton(
                                            icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                                            onPressed: () async {
                                                final confirmed = await showDialog<bool>(
                                                    context: context,
                                                    builder: (context) => AlertDialog(
                                                        backgroundColor: KeldorTheme.surface,
                                                        title: const Text('Küldetés megszakítása?', style: TextStyle(color: Colors.white)),
                                                        content: Text('Biztosan feladod ezt a küldetést: "${uq.questTitle ?? "Küldetés"}"?', style: const TextStyle(color: Colors.white70)),
                                                        actions: [
                                                            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Mégsem')),
                                                            TextButton(
                                                                onPressed: () => Navigator.pop(context, true), 
                                                                child: const Text('Igen, feladom', style: TextStyle(color: Colors.red))
                                                            ),
                                                        ],
                                                    )
                                                );
                                                
                                                if (confirmed == true) {
                                                    final token = context.read<AuthService>().token;
                                                    if (token != null) {
                                                        await context.read<KeldorService>().abandonQuest(token, uq.id);
                                                        // setState will be triggered by notifyListeners in service if we used watch, or we might need local setState. 
                                                        // Since this is inside a Builder that might not rebuild automatically if logic is complex.
                                                        // But Consumer/watch usually handles it.
                                                    }
                                                }
                                            },
                                        ),
                                        // const Icon(Icons.chevron_right, color: Colors.white24),
                                    ],
                                ),
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

// ... (in _buildProfileHeader)

  Widget _buildProfileHeader(char) {
      Color factionColor = Colors.grey;
      IconData factionIcon = Icons.help_outline;
      String factionName = "Független";
      
      if (char.faction != null && char.faction != 'none') {
          switch (char.faction!) {
              case 'transformer':
                  factionColor = Colors.cyan;
                  factionIcon = Icons.build_circle_outlined;
                  factionName = "Átalakító";
                  break;
              case 'chronicler':
                  factionColor = Colors.amber;
                  factionIcon = Icons.history_edu;
                  factionName = "Krónikás";
                  break;
              case 'forgotten':
                  factionColor = Colors.purple;
                  factionIcon = Icons.visibility_off;
                  factionName = "Elfeledett";
                  break;
          }
      }

      return Column(children: [
            Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                    Container(
                        width: 80, height: 80,
                        decoration: BoxDecoration(
                          color: KeldorTheme.primary.withOpacity(0.1),
                          shape: BoxShape.circle,
                          border: Border.all(color: KeldorTheme.primary, width: 2),
                        ),
                        child: Icon(_getClassIcon(char.characterClass), size: 40, color: KeldorTheme.primary),
                    ),
                    const SizedBox(width: 16),
                    // Faction Badge
                    GestureDetector(
                        onTap: (char.faction == null || char.faction == 'none') 
                            ? () {
                                Navigator.push(context, MaterialPageRoute(builder: (_) => const FactionSelectionScreen()));
                            }
                            : null,
                        child: Container(
                            width: 80, height: 80,
                            decoration: BoxDecoration(
                              color: factionColor.withOpacity(0.1),
                              shape: BoxShape.circle,
                              border: Border.all(color: factionColor, width: 2),
                              boxShadow: [
                                  if (char.faction == null || char.faction == 'none')
                                    BoxShadow(color: KeldorTheme.primary.withOpacity(0.5), blurRadius: 10) // Pulse hint
                              ]
                            ),
                            child: Icon(factionIcon, size: 40, color: factionColor),
                        ),
                    ),
                ],
            ),
            const SizedBox(height: 16),
            Text(
              "Szint: ${char.level} | ${char.characterClass.toString().split('.').last.toUpperCase()}",
              style: KeldorTheme.darkTheme.textTheme.displayLarge?.copyWith(
                  color: Colors.white70, fontWeight: FontWeight.bold, fontSize: 16
              ),
            ),
            const SizedBox(height: 4),
            Text(
              factionName.toUpperCase(),
              style: GoogleFonts.cinzel(
                  color: factionColor, fontWeight: FontWeight.bold, fontSize: 18, letterSpacing: 2
              ),
            ),
            if (char.faction == null || char.faction == 'none')
                 Padding(
                   padding: const EdgeInsets.only(top: 8.0),
                   child: Text("(Kattints a jelvényre a választáshoz)", style: TextStyle(color: KeldorTheme.primary.withOpacity(0.7), fontSize: 10)),
                 )
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

  Map<String, int> _calculateBonuses(Character char) {
      // ... (keep existing)
      int str = 0;
      int agi = 0;
      int tac = 0;
      
      for (var slot in char.inventory) {
          if (slot.equipped) {
              for (var effect in slot.effects) {
                  if (effect is Map) {
                      if (effect['type'] == 'stat_bonus') {
                          int val = (effect['value'] as num).toInt();
                          String? target = effect['target_stat'];
                          if (target == 'strength') str += val;
                          if (target == 'agility') agi += val;
                          if (target == 'tactics') tac += val;
                      }
                  }
              }
          }
      }
      return {'strength': str, 'agility': agi, 'tactics': tac};
  }

  Widget _buildLoadoutSection(BuildContext context, Character char) {
      final equippedItems = char.inventory.where((i) => i.equipped).toList();
      
      return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
              color: const Color(0xFF1E293B), // Slate 800
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.blueAccent.withOpacity(0.3)),
          ),
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                  Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                          Text("Felszerelés (Loadout)", style: GoogleFonts.outfit(color: Colors.blueAccent, fontWeight: FontWeight.bold)),
                          Text("${equippedItems.length} / 3", style: TextStyle(color: equippedItems.length == 3 ? Colors.redAccent : Colors.white54)),
                      ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: List.generate(3, (index) {
                          if (index < equippedItems.length) {
                              return _buildInventoryItem(context, equippedItems[index], true);
                          } else {
                              return _buildEmptySlot();
                          }
                      }),
                  )
              ],
          )
      );
  }

  Widget _buildBackpackSection(BuildContext context, Character char) {
      final backpackItems = char.inventory.where((i) => !i.equipped).toList();
      
      if (backpackItems.isEmpty) {
          return const Center(child: Text("Üres a zsákod.", style: TextStyle(color: Colors.white24)));
      }
      
      return GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 4, crossAxisSpacing: 8, mainAxisSpacing: 8),
            itemCount: backpackItems.length,
            itemBuilder: (ctx, index) {
                return _buildInventoryItem(context, backpackItems[index], false);
            }
      );
  }

  Widget _buildEmptySlot() {
      return Container(
          width: 60, height: 60,
          decoration: BoxDecoration(
              color: Colors.black26,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white10),
          ),
          child: const Icon(Icons.add, color: Colors.white10),
      );
  }

  Widget _buildInventoryItem(BuildContext context, InventorySlot slot, bool isLoadout) {
      final rarityColor = _getRarityColor(slot.rarity);
      return InkWell(
          onTap: () => _showItemDialog(context, slot),
          child: Container(
                width: isLoadout ? 70 : null,
                height: isLoadout ? 70 : null,
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
                          color: slot.equipped ? Colors.green : (rarityColor == Colors.white10 ? Colors.white70 : rarityColor),
                          size: isLoadout ? 32 : 24,
                        ),
                        if (!isLoadout) ...[
                            const SizedBox(height: 4),
                            Text("${slot.quantity}x", style: const TextStyle(color: Colors.white, fontSize: 10)),
                        ]
                    ],
                ),
            ),
      );
  }

  void _showItemDialog(BuildContext context, InventorySlot slot) {
       final rarityColor = _getRarityColor(slot.rarity);
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
                          child: const Text("Felvétel (Equip)", style: TextStyle(color: Colors.greenAccent)),
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
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Bezárás"))
                ]
            )
        );
  }

  Widget _buildCombatStats(Character char) {
    final bonuses = _calculateBonuses(char);

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildCompactStat("Erő", char.stats['strength'] ?? 1, bonuses['strength'] ?? 0, Icons.fitness_center, Colors.redAccent),
        _buildCompactStat("Ügyess.", char.stats['agility'] ?? 1, bonuses['agility'] ?? 0, Icons.flash_on, Colors.greenAccent),
        _buildCompactStat("Taktika", char.stats['tactics'] ?? 1, bonuses['tactics'] ?? 0, Icons.psychology, Colors.blueAccent),
      ],
    );
  }

  Widget _buildCompactStat(String label, int base, int bonus, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 4),
        Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
                Text("$base", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                if (bonus > 0)
                    Text(" (+$bonus)", style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 14)),
            ]
        ),
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
  Widget _buildQuestHistorySection(List<Map<String, dynamic>> history) {
      if (history.isEmpty) return const SizedBox.shrink();

      return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
              color: KeldorTheme.surface.withOpacity(0.5),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white10)
          ),
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                   Builder(
                      builder: (ctx) => GestureDetector(
                          onTap: () {
                              DefaultTabController.of(ctx)?.animateTo(2);
                          },
                          child: Row(children: const [
                              Icon(Icons.history, color: Colors.amber, size: 20),
                              SizedBox(width: 8),
                              Text("Küldetés Előzmények", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                              Spacer(),
                              Icon(Icons.arrow_forward, color: Colors.white24, size: 16),
                          ]),
                       ),
                   ),
                  const SizedBox(height: 12),
                  ...history.map((h) {
                      final title = h['title'] ?? 'Névtelen';
                      final steps = h['rewards_steps'] ?? 0;
// ... (rest is same)
                      String dateStr = "";
                      if (h['completed_at'] != null) {
                          try {
                              final dt = DateTime.parse(h['completed_at'].toString());
                              dateStr = "${dt.month}.${dt.day}.";
                          } catch (_) {}
                      }
                      
                      return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                              children: [
                                  Text(dateStr, style: const TextStyle(color: Colors.white54, fontSize: 12)),
                                  const SizedBox(width: 8),
                                  Expanded(child: Text(title, style: const TextStyle(color: Colors.white70))),
                                  Text("+$steps lépés", style: const TextStyle(color: Colors.greenAccent, fontSize: 12)),
                              ],
                          ),
                      );
                  }).toList()
              ],
          ),
      );
  }
}
