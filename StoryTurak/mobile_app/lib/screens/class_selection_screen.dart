import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/geolixo_service.dart';
import 'explore_screen.dart';
import 'dart:convert';
import '../models/geolixo_models.dart';
import 'package:storyturak_mobile/theme.dart';

class ClassSelectionScreen extends StatelessWidget {
  const ClassSelectionScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Ki vagy te?",
                style: GeolixoTheme.darkTheme.textTheme.displayLarge,
              ),
              const SizedBox(height: 8),
              Text(
                "Válassz utat a város sötétjében.",
                style: GeolixoTheme.darkTheme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              Expanded(
                child: ListView(
                  children: const [
                    ClassCard(
                      title: "Őr / Katona",
                      description: "Frontális, stabil döntések. Nem hátrálsz meg.",
                      icon: Icons.shield,
                      classId: "soldier",
                    ),
                    ClassCard(
                      title: "Poéta",
                      description: "Megfigyelő. A szavak és jelek mestere.",
                      icon: Icons.edit_note,
                      classId: "poet",
                    ),
                    ClassCard(
                      title: "Vámszedő",
                      description: "Kockázat és haszon. Ismered a dörzsölt utakat.",
                      icon: Icons.attach_money,
                      classId: "tax_collector",
                    ),
                    ClassCard(
                      title: "Zarándok",
                      description: "Kitartás. A hosszú út a te igazi otthonod.",
                      icon: Icons.hiking,
                      classId: "pilgrim",
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ClassCard extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;
  final String classId; // "soldier", "poet", etc.

  const ClassCard({
    Key? key,
    required this.title,
    required this.description,
    required this.icon,
    required this.classId,
  }) : super(key: key);

  Future<void> _createCharacter(BuildContext context, String name) async {
    final token = context.read<AuthService>().token;
    if (token == null) return;

    try {
      final response = await http.post(
        Uri.parse('${GeolixoService.baseUrl}/characters/create?character_class=$classId&name=$name'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        // Success
        final data = json.decode(response.body);
        final newChar = Character.fromJson(data);
        
        if (context.mounted) {
            // Pop first to exit the screen safely
            Navigator.pop(context);
            // Then update state to trigger MainApp routing
            context.read<GeolixoService>().setActiveCharacter(newChar);
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
           SnackBar(content: Text("Hiba a karakter létrehozásakor: ${response.body}"))
        );
      }
    } catch (e) {
      print("Char creation error: $e");
    }
  }

  void _showNameDialog(BuildContext context) {
    final nameController = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: GeolixoTheme.surface,
        title: const Text("Nevezd el hősödet!", style: TextStyle(color: Colors.white)),
        content: TextField(
            controller: nameController,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(
                hintText: "Karakternév",
                hintStyle: TextStyle(color: Colors.white54)
            ),
        ),
        actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text("Mégse")
            ),
            TextButton(
                onPressed: () {
                    if (nameController.text.isNotEmpty) {
                        Navigator.pop(ctx);
                        _createCharacter(context, nameController.text);
                    }
                },
                child: const Text("Tovább", style: TextStyle(color: GeolixoTheme.accent))
            ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: GeolixoTheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _showNameDialog(context),
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: GeolixoTheme.accent, size: 32),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: GeolixoTheme.darkTheme.textTheme.displayMedium?.copyWith(fontSize: 18),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: GeolixoTheme.darkTheme.textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right, color: Colors.white54),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
