import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/geolixo_service.dart';
import '../services/auth_service.dart';
import '../models/geolixo_models.dart';
import '../theme.dart';
import 'class_selection_screen.dart'; // Ensure this matches actual file

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
          await context.read<GeolixoService>().fetchUserCharacters(token);
      }
      if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<GeolixoService>();
    final characters = service.userCharacters;

    return Scaffold(
      backgroundColor: GeolixoTheme.background,
      appBar: AppBar(
        title: const Text("Válassz Karaktert"),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
            IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () => context.read<AuthService>().logout(),
            )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: GeolixoTheme.accent))
        : Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                    Expanded(
                        child: characters.isEmpty 
                        ? Center(child: Text("Még nincs karaktered.", style: GeolixoTheme.darkTheme.textTheme.bodyLarge))
                        : ListView.builder(
                            itemCount: characters.length,
                            itemBuilder: (ctx, index) {
                                final char = characters[index];
                                return Card(
                                    color: GeolixoTheme.surface,
                                    margin: const EdgeInsets.only(bottom: 16),
                                    child: InkWell(
                                        onTap: () {
                                            service.setActiveCharacter(char);
                                            // MainApp routing should handle the rest
                                        },
                                        child: Padding(
                                            padding: const EdgeInsets.all(16),
                                            child: Row(
                                                children: [
                                                    Container(
                                                        padding: const EdgeInsets.all(12),
                                                        decoration: BoxDecoration(
                                                            color: GeolixoTheme.accent.withOpacity(0.1),
                                                            shape: BoxShape.circle
                                                        ),
                                                        child: Icon(_getClassIcon(char.characterClass), color: GeolixoTheme.accent),
                                                    ),
                                                    const SizedBox(width: 16),
                                                    Column(
                                                        crossAxisAlignment: CrossAxisAlignment.start,
                                                        children: [
                                                            Text(char.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                                                            Text("Szint: ${char.level} | ${char.characterClass.toString().split('.').last.toUpperCase()}", 
                                                                 style: const TextStyle(color: Colors.white70)),
                                                        ],
                                                    ),
                                                    const Spacer(),
                                                    const Icon(Icons.chevron_right, color: Colors.white24)
                                                ],
                                            ),
                                        ),
                                    ),
                                );
                            },
                        ),
                    ),
                    ElevatedButton.icon(
                        onPressed: () async {
                            await Navigator.push(context, MaterialPageRoute(builder: (_) => const ClassSelectionScreen()));
                            if (mounted) _refreshCharacters();
                        }, 
                        icon: const Icon(Icons.add), 
                        label: const Text("ÚJ KARAKTER"),
                        style: ElevatedButton.styleFrom(
                            backgroundColor: GeolixoTheme.primary,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                    ),
                ],
            ),
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
