import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/geolixo_models.dart';
import '../services/geolixo_service.dart';
import '../services/auth_service.dart';
import '../theme.dart';

class EncounterScreen extends StatefulWidget {
  final Encounter encounter;

  const EncounterScreen({Key? key, required this.encounter}) : super(key: key);

  @override
  State<EncounterScreen> createState() => _EncounterScreenState();
}

class _EncounterScreenState extends State<EncounterScreen> {
  bool _resolved = false;
  String? _outcomeText;

  @override
  void initState() {
    super.initState();
  }


  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black.withOpacity(0.9),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header
              Text(
                widget.encounter.type == EncounterType.fight ? "HARC!" : "ESEMÉNY",
                style: GeolixoTheme.darkTheme.textTheme.labelLarge?.copyWith(
                  color: widget.encounter.type == EncounterType.fight ? GeolixoTheme.error : GeolixoTheme.accent,
                  fontSize: 16,
                  letterSpacing: 2,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              
              // Title & Desc
              Text(
                widget.encounter.title,
                style: GeolixoTheme.darkTheme.textTheme.displayLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Text(
                widget.encounter.description,
                style: GeolixoTheme.darkTheme.textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
              
              const Spacer(),

              const SizedBox(height: 30),

              // Outcome or Choices
              if (_resolved)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white10,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Column(
                    children: [
                      Text(
                        _outcomeText ?? "",
                        style: const TextStyle(fontSize: 16, color: Colors.white),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () => Navigator.pop(context),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.white24),
                        child: const Text("TOVÁBB"),
                      ),
                    ],
                  ),
                )
              else
                Column(
                  children: [
                    _buildOptionButton("TÁMADÁS (Erő)", Colors.redAccent, true),
                    const SizedBox(height: 12),
                    _buildOptionButton("KIJÁTSZÁS (Ügyesség)", Colors.teal, true),
                    const SizedBox(height: 12),
                    _buildOptionButton("ELFUTOK", Colors.blueGrey, false),
                  ],
                ),
                
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _resolveEncounter(bool success, String text) async {
    setState(() => _resolved = true);
    
    if (success) {
        // Call backend to get loot
        final service = context.read<GeolixoService>();
        final auth = context.read<AuthService>();
        
        if (auth.token != null) {
            final rewards = await service.resolveEncounter(auth.token!, widget.encounter.id, "success");
            
            if (rewards != null) {
                final xp = rewards['xp'];
                final items = (rewards['items'] as List).map((i) => Item.fromJson(i)).toList();
                
                String rewardText = "Sikerült! Jutalmad:\n+$xp XP";
                if (items.isNotEmpty) {
                    rewardText += "\n\nTárgyak:";
                    for (var item in items) {
                        rewardText += "\n- ${item.name}";
                    }
                }
                
                setState(() {
                    _outcomeText = rewardText;
                });
                return;
            }
        }
    }
    
    // Fallback or failure
    setState(() {
      _outcomeText = text;
    });
  }

  Widget _buildOptionButton(String text, Color color, bool isSuccess) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: () {
          _resolveEncounter(
            isSuccess, 
            isSuccess ? "Sikerült! (Loot töltése...)" : "Megmenekültél, de üres kézzel."
          );
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
        child: Text(text),
      ),
    );
  }
}
