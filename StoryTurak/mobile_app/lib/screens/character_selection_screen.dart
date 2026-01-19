import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../models/keldor_models.dart';
import '../theme.dart';
import 'class_selection_screen.dart'; 

class CharacterSelectionScreen extends StatefulWidget {
  const CharacterSelectionScreen({Key? key}) : super(key: key);

  @override
  State<CharacterSelectionScreen> createState() => _CharacterSelectionScreenState();
}

class _CharacterSelectionScreenState extends State<CharacterSelectionScreen> {
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _refreshCharacters();
  }

  Future<void> _refreshCharacters() async {
      setState(() => _isLoading = true);
      final token = context.read<AuthService>().token;
      if (token != null) {
          await context.read<KeldorService>().fetchUserCharacters(token);
      }
      if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<KeldorService>();
    final characters = service.userCharacters;

    return Scaffold(
      backgroundColor: KeldorTheme.background,
      appBar: AppBar(
        title: Image.asset('assets/keldor_logo_notext.png', height: 32),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
            IconButton(
                icon: const Icon(Icons.logout, color: Colors.white54),
                onPressed: () => context.read<AuthService>().logout(),
            )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: KeldorTheme.primary))
        : Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                    Text(
                      "Válassz Hőst",
                      style: KeldorTheme.darkTheme.textTheme.displayMedium?.copyWith(
                        color: KeldorTheme.primary,
                        letterSpacing: 2,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    Expanded(
                        child: characters.isEmpty 
                        ? Center(child: Text("Még nincs karaktered.", style: KeldorTheme.darkTheme.textTheme.bodyLarge))
                        : ListView.builder(
                            itemCount: characters.length,
                            itemBuilder: (ctx, index) {
                                final char = characters[index];
                                return Container(
                                    margin: const EdgeInsets.only(bottom: 16),
                                    decoration: BoxDecoration(
                                      color: KeldorTheme.surface,
                                      borderRadius: BorderRadius.circular(12),
                                      border: Border.all(color: Colors.white10),
                                    ),
                                    child: Material(
                                      color: Colors.transparent,
                                      child: InkWell(
                                          onTap: () {
                                              service.setActiveCharacter(char);
                                          },
                                          borderRadius: BorderRadius.circular(12),
                                          child: Padding(
                                              padding: const EdgeInsets.all(20),
                                              child: Row(
                                                  children: [
                                                      Container(
                                                          padding: const EdgeInsets.all(12),
                                                          decoration: BoxDecoration(
                                                              color: KeldorTheme.primary.withOpacity(0.05),
                                                              shape: BoxShape.circle
                                                          ),
                                                          child: Icon(_getClassIcon(char.characterClass), color: KeldorTheme.primary),
                                                      ),
                                                      const SizedBox(width: 20),
                                                      Expanded(
                                                        child: Column(
                                                            crossAxisAlignment: CrossAxisAlignment.start,
                                                            children: [
                                                                Text(char.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                                                                const SizedBox(height: 4),
                                                                Text("SZINT: ${char.level} | ${char.characterClass.toString().split('.').last.toUpperCase()}", 
                                                                     style: TextStyle(color: KeldorTheme.primary.withOpacity(0.7), fontSize: 12, letterSpacing: 1)),
                                                            ],
                                                        ),
                                                      ),
                                                      const Icon(Icons.chevron_right, color: Colors.white24)
                                                  ],
                                              ),
                                          ),
                                      ),
                                    ),
                                );
                            },
                        ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                        onPressed: () async {
                            await Navigator.push(context, MaterialPageRoute(builder: (_) => const ClassSelectionScreen()));
                            if (mounted) _refreshCharacters();
                        }, 
                        icon: const Icon(Icons.add), 
                        label: const Text("ÚJ HŐS LÉTREHOZÁSA"),
                        style: ElevatedButton.styleFrom(
                            backgroundColor: KeldorTheme.primary,
                            foregroundColor: KeldorTheme.background,
                            padding: const EdgeInsets.symmetric(vertical: 20),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                    ),
                ],
            ),
        ),
    );
  }

  IconData _getClassIcon(CharacterClass cType) {
    switch (cType) {
      case CharacterClass.archivist: return Icons.auto_stories;
      case CharacterClass.vigilante: return Icons.security;
      case CharacterClass.collector: return Icons.backpack;
      default: return Icons.person;
    }
  }
}
