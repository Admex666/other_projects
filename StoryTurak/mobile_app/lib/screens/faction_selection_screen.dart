import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/keldor_service.dart';
import '../theme.dart';

class FactionSelectionScreen extends StatefulWidget {
  const FactionSelectionScreen({Key? key}) : super(key: key);

  @override
  State<FactionSelectionScreen> createState() => _FactionSelectionScreenState();
}

class _FactionSelectionScreenState extends State<FactionSelectionScreen> {
  String? _selectedFaction;
  bool _isLoading = false;

  final List<Map<String, dynamic>> _factions = [
    {
      "id": "transformer",
      "name": "Átalakítók",
      "description": "A várost egy logikus, mágikus gépezetté akarják formálni. A rend és a fejlődés hívei.",
      "color": Colors.cyan,
      "icon": Icons.build_circle_outlined
    },
    {
      "id": "chronicler",
      "name": "Krónikások",
      "description": "A múlt őrzői. Védelmezik a történelmet és az emlékeket az Ürességgel szemben.",
      "color": Colors.amber,
      "icon": Icons.history_edu
    },
    {
      "id": "forgotten",
      "name": "Elfeledettek",
      "description": "Az árnyak gyermekei. Káoszban és entrópában lelnek békére.",
      "color": Colors.purple,
      "icon": Icons.visibility_off
    }
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KeldorTheme.background,
      appBar: AppBar(
        title: Text("Válassz Frakciót", style: GoogleFonts.cinzel(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: const SizedBox.shrink(), // No Back button, must choose
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(
                "A döntésed végleges. Válassz bölcsen, melyik oldalon állsz a Város jövőjéért folytatott harcban.",
                textAlign: TextAlign.center,
                style: GoogleFonts.merriweather(color: Colors.white70, fontSize: 14),
              ),
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                itemCount: _factions.length,
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemBuilder: (context, index) {
                  final faction = _factions[index];
                  final isSelected = _selectedFaction == faction['id'];
                  return GestureDetector(
                    onTap: () {
                      setState(() {
                         _selectedFaction = faction['id'];
                      });
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: isSelected 
                            ? faction['color'].withOpacity(0.2) 
                            : Colors.white.withOpacity(0.05),
                        border: Border.all(
                            color: isSelected ? faction['color'] : Colors.white24,
                            width: isSelected ? 2 : 1
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: isSelected ? [
                           BoxShadow(color: faction['color'].withOpacity(0.3), blurRadius: 15)
                        ] : [],
                      ),
                      child: Row(
                        children: [
                           Icon(faction['icon'], size: 40, color: faction['color']),
                           const SizedBox(width: 16),
                           Expanded(
                               child: Column(
                                   crossAxisAlignment: CrossAxisAlignment.start,
                                   children: [
                                       Text(
                                           faction['name'], 
                                           style: GoogleFonts.cinzel(
                                               fontSize: 20, 
                                               color: faction['color'], 
                                               fontWeight: FontWeight.bold
                                           )
                                       ),
                                       const SizedBox(height: 8),
                                       Text(
                                           faction['description'],
                                           style: const TextStyle(color: Colors.white70, fontSize: 12),
                                       ),
                                   ],
                               ),
                           ),
                           if (isSelected) 
                               Icon(Icons.check_circle, color: faction['color'])
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            Padding(
                padding: const EdgeInsets.all(20),
                child: SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                        onPressed: _selectedFaction != null && !_isLoading ? _joinFaction : null,
                        style: ElevatedButton.styleFrom(
                            backgroundColor: _selectedFaction != null 
                                ? _factions.firstWhere((f) => f['id'] == _selectedFaction)['color'] 
                                : Colors.grey,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: _isLoading 
                            ? const CircularProgressIndicator(color: Colors.white)
                            : Text("CSATLAKOZÁS", style: GoogleFonts.cinzel(fontWeight: FontWeight.bold, color: Colors.black, fontSize: 18)),
                    ),
                ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _joinFaction() async {
      if (_selectedFaction == null) return;
      
      setState(() => _isLoading = true);
      
      final token = context.read<AuthService>().token;
      if (token != null) {
          bool success = await context.read<KeldorService>().setFaction(token, _selectedFaction!);
          if (success) {
               if (mounted) {
                   Navigator.of(context).pop(); // Return to previous screen (Profile or wherever triggered)
                   ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Üdvözöl a Frakció!"), backgroundColor: Colors.green));
               }
          } else {
               if (mounted) {
                   ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Hiba a csatlakozáskor!"), backgroundColor: Colors.red));
               }
          }
      }
      
      if (mounted) setState(() => _isLoading = false);
  }
}
