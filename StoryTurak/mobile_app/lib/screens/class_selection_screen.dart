import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart';
import '../services/auth_service.dart';
import '../services/keldor_service.dart';
import '../services/api_service.dart';
import 'explore_screen.dart';
import 'dart:convert';
import '../models/keldor_models.dart';
import '../theme.dart';

class ClassSelectionScreen extends StatelessWidget {
  const ClassSelectionScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KeldorTheme.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Ki vagy te?",
                style: KeldorTheme.darkTheme.textTheme.displayLarge?.copyWith(
                  color: KeldorTheme.primary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                "Válassz utat Keldor sötétjében.",
                style: KeldorTheme.darkTheme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              Expanded(
                child: ListView(
                  children: const [
                    ClassCard(
                      title: "Vigyázó", // Vigilante
                      description: "Fegyveres harcos, aki nem hátrál meg az árnyaktól.",
                      icon: Icons.shield,
                      classId: "vigilante",
                    ),
                    ClassCard(
                      title: "Gyűjtő", // Collector
                      description: "Fürge kincsvadász, aki minden zugot ismer.",
                      icon: Icons.backpack,
                      classId: "collector",
                    ),
                    ClassCard(
                      title: "Krónikás", // Archivist
                      description: "Bölcs tudós, aki a történelem titkait kutatja.",
                      icon: Icons.menu_book,
                      classId: "archivist",
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
      // Get current location for tutorial quest spawn
      double? userLat;
      double? userLon;
      try {
        final position = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.medium,
          timeLimit: const Duration(seconds: 5),
        );
        userLat = position.latitude;
        userLon = position.longitude;
        debugPrint("📍 Got location for character creation: $userLat, $userLon");
      } catch (e) {
        debugPrint("⚠️ Failed to get location for character creation, using defaults: $e");
        // Use Budapest center as fallback
        userLat = 47.4979;
        userLon = 19.0402;
      }

      final baseUrl = await ApiService().getBaseUrl();
      final response = await http.post(
        Uri.parse('$baseUrl/characters/create?character_class=$classId&name=$name&lat=$userLat&lon=$userLon'),
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
            context.read<KeldorService>().setActiveCharacter(newChar);
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
        backgroundColor: KeldorTheme.surface,
        title: const Text("Nevezd el hősödet!", style: TextStyle(color: Colors.white)),
        content: TextField(
            controller: nameController,
            autofocus: true,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(
                hintText: "Karakternév",
                hintStyle: TextStyle(color: Colors.white54),
                enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white24)),
                focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: KeldorTheme.primary)),
            ),
        ),
        actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text("Mégse", style: TextStyle(color: Colors.white54))
            ),
            ElevatedButton(
                onPressed: () {
                    if (nameController.text.isNotEmpty) {
                        Navigator.pop(ctx);
                        _createCharacter(context, nameController.text);
                    }
                },
                style: ElevatedButton.styleFrom(backgroundColor: KeldorTheme.primary, foregroundColor: KeldorTheme.background),
                child: const Text("Kezdés")
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
        color: KeldorTheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _showNameDialog(context),
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: KeldorTheme.primary.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: KeldorTheme.primary, size: 32),
                ),
                const SizedBox(width: 20),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: KeldorTheme.darkTheme.textTheme.displayMedium?.copyWith(fontSize: 18, color: Colors.white),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: KeldorTheme.darkTheme.textTheme.bodyMedium,
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
