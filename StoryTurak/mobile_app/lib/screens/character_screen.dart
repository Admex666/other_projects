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
                        const SizedBox(height: 32),
                        _buildStatCard("Életerő", "${char.currentHp} / ${char.maxHp}", Icons.favorite),
                        const SizedBox(height: 8),
                        _buildStatCard("Tapasztalat", "${char.xp} XP", Icons.star),
                        const SizedBox(height: 24),
                        OutlinedButton.icon(
                            onPressed: () {
                                context.read<KeldorService>().clearActiveCharacter();
                                // MainApp will switch to Selection Screen
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
                            return InkWell(
                                onTap: () {
                                    showDialog(
                                        context: context, 
                                        builder: (ctx) => AlertDialog(
                                            backgroundColor: KeldorTheme.surface,
                                            title: Text(slot.name ?? "Ismeretlen Tárgy", style: const TextStyle(color: Colors.white)),
                                            content: Column(
                                                mainAxisSize: MainAxisSize.min,
                                                crossAxisAlignment: CrossAxisAlignment.start,
                                                children: [
                                                    if (slot.iconCode != null) 
                                                        Center(child: Icon(
                                                            slot.iconCode == 'local_pharmacy' ? Icons.local_pharmacy : 
                                                            slot.iconCode == 'monetization_on' ? Icons.monetization_on : Icons.help_outline, 
                                                            size: 48, 
                                                            color: KeldorTheme.primary
                                                        )),
                                                    const SizedBox(height: 16),
                                                    Text(slot.description ?? "Nincs leírás.", style: const TextStyle(color: Colors.white70)),
                                                    const SizedBox(height: 16),
                                                    if (slot.stats != null && slot.stats!.isNotEmpty) ...[
                                                        const Text("Tulajdonságok:", style: TextStyle(color: KeldorTheme.primary, fontWeight: FontWeight.bold)),
                                                        const SizedBox(height: 8),
                                                        ...slot.stats!.entries.map((e) => Text("- ${e.key}: ${e.value}", style: const TextStyle(color: Colors.white60))),
                                                    ]
                                                ],
                                            ),
                                            actions: [
                                                TextButton(
                                                    onPressed: () => Navigator.pop(ctx),
                                                    child: const Text("Bezárás", style: TextStyle(color: Colors.blueAccent)),
                                                )
                                            ],
                                        )
                                    );
                                },
                                child: Container(
                                    decoration: BoxDecoration(
                                        color: KeldorTheme.surface,
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(color: Colors.white10),
                                    ),
                                    child: Column(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                            Icon(
                                              slot.iconCode == 'local_pharmacy' ? Icons.local_pharmacy : 
                                              slot.iconCode == 'monetization_on' ? Icons.monetization_on : Icons.circle, 
                                              color: Colors.white70
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
      case CharacterClass.soldier: return Icons.shield;
      case CharacterClass.poet: return Icons.edit_note;
      case CharacterClass.tax_collector: return Icons.attach_money;
      case CharacterClass.pilgrim: return Icons.hiking;
    }
  }
}
