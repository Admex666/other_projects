import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/keldor_models.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../theme.dart';

class EncounterScreen extends StatefulWidget {
  final Encounter encounter;

  const EncounterScreen({Key? key, required this.encounter}) : super(key: key);

  @override
  State<EncounterScreen> createState() => _EncounterScreenState();
}

class _EncounterScreenState extends State<EncounterScreen> {
  String? _currentNodeId;
  bool _isTransitioning = false;
  final TextEditingController _inputController = TextEditingController();
  String? _errorMessage;
  List<String>? _currentOrder;
  bool _isFinishing = false;

  @override
  void initState() {
    super.initState();
    _currentNodeId = widget.encounter.startNodeId ?? 
        (widget.encounter.nodes?.isNotEmpty == true ? widget.encounter.nodes!.keys.first : null);
    _initializeNodeState();
  }

  void _initializeNodeState() {
    final node = _currentNode;
    if (node?.type == EncounterNodeType.order && node?.options != null) {
      _currentOrder = List<String>.from(node!.options!);
    } else {
      _currentOrder = null;
    }
  }

  EncounterNode? get _currentNode {
    if (_currentNodeId == null || widget.encounter.nodes == null) return null;
    return widget.encounter.nodes![_currentNodeId];
  }

  @override
  Widget build(BuildContext context) {
    final node = _currentNode;

    return Scaffold(
      backgroundColor: Colors.black.withOpacity(0.95),
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 500),
          child: node == null ? _buildNoNodeError() : _buildNodeContent(node),
        ),
      ),
    );
  }

  Widget _buildNodeContent(EncounterNode node) {
    return Container(
      key: ValueKey(node.id),
      padding: const EdgeInsets.all(24.0),
      child: Column(
        children: [
          const SizedBox(height: 20),
          // Heading / Type Indicator
          _buildTypeIndicator(node),
          const SizedBox(height: 40),
          
          // Image or Placeholder
          _buildNodeMedia(node),
          
          const SizedBox(height: 40),
          
          // Content and Action Area in a single scrollable view
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  Text(
                    node.text,
                    style: KeldorTheme.darkTheme.textTheme.bodyMedium?.copyWith(
                      height: 1.6,
                      fontSize: 18,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),
                  
                  // Action Area (Choices, Input, Order, etc.) now follows text naturally
                  _buildActionArea(node),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildTypeIndicator(EncounterNode node) {
      String label = "ESEMÉNY";
      Color color = KeldorTheme.primary;
      
      switch(node.type) {
          case EncounterNodeType.fight:
              label = "HARC!";
              color = KeldorTheme.error;
              if (node.enemyClass != null) {
                  label += " (${node.enemyClass!.toUpperCase()})";
              }
              break;
          case EncounterNodeType.choice:
              label = "DÖNTÉS";
              color = Colors.blueAccent;
              break;
          case EncounterNodeType.input:
              label = "REJTVÉNY";
              color = Colors.amber;
              break;
          default:
              break;
      }

      return Text(
        label,
        style: KeldorTheme.darkTheme.textTheme.labelLarge?.copyWith(
          color: color,
          fontSize: 14,
          letterSpacing: 4,
        ),
        textAlign: TextAlign.center,
      );
  }

  Widget _buildInputArea(EncounterNode node) {
    return Column(
      children: [
        TextField(
          controller: _inputController,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: "Írd be a választ...",
            hintStyle: const TextStyle(color: Colors.white38),
            errorText: _errorMessage,
            enabledBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: Colors.white24),
            ),
            focusedBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: KeldorTheme.primary),
            ),
          ),
          onChanged: (_) {
            if (_errorMessage != null) {
              setState(() => _errorMessage = null);
            }
          },
        ),
        const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => _validateInput(node),
              child: Text(node.buttonText ?? "ELLENŐRZÉS"),
            ),
          ),
      ],
    );
  }

  Widget _buildOrderArea(EncounterNode node) {
    if (_currentOrder == null) return const SizedBox.shrink();

    return Column(
      children: [
        Container(
          height: 250,
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(12),
          ),
          child: ReorderableListView(
            shrinkWrap: true,
            buildDefaultDragHandles: true,
            onReorder: (oldIndex, newIndex) {
              setState(() {
                if (newIndex > oldIndex) newIndex -= 1;
                final item = _currentOrder!.removeAt(oldIndex);
                _currentOrder!.insert(newIndex, item);
              });
            },
            children: _currentOrder!.asMap().entries.map((entry) {
              return ListTile(
                key: ValueKey("order_${entry.key}"),
                leading: const Icon(Icons.drag_handle, color: Colors.white38),
                title: Text(entry.value, style: const TextStyle(color: Colors.white)),
                tileColor: Colors.transparent,
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: () => _validateOrder(node),
            child: Text(node.buttonText ?? "ELLENŐRZÉS"),
          ),
        ),
      ],
    );
  }

  void _validateOrder(EncounterNode node) {
    if (_currentOrder == null) return;
    
    final current = _currentOrder!.join(", ").trim().toLowerCase();
    final correct = node.correctAnswer?.trim().toLowerCase();

    if (current == correct) {
      _goToNode(node.successNodeId ?? node.nextNodeId);
    } else {
      if (node.failureNodeId != null) {
        _goToNode(node.failureNodeId);
      } else {
        setState(() {
          _errorMessage = "Helytelen sorrend. Próbáld újra!";
        });
      }
    }
  }

  void _validateInput(EncounterNode node) {
    final input = _inputController.text.trim().toLowerCase();
    
    if (input.isEmpty) {
      setState(() {
        _errorMessage = "Kérlek, írj be egy választ!";
      });
      return;
    }

    bool isCorrect = false;
    if (node.validAnswers != null && node.validAnswers!.isNotEmpty) {
      isCorrect = node.validAnswers!.any((ans) => ans.trim().toLowerCase() == input);
    } else {
      final correct = node.correctAnswer?.trim().toLowerCase();
      isCorrect = (input == correct);
    }

    if (isCorrect) {
      _goToNode(node.successNodeId ?? node.nextNodeId);
    } else {
      if (node.failureNodeId != null) {
        _goToNode(node.failureNodeId);
      } else {
        setState(() {
          _errorMessage = "Helytelen válasz. Próbáld újra!";
        });
      }
    }
  }

  Widget _buildNodeMedia(EncounterNode node) {
      if (node.image != null) {
          return ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.asset(
                node.image!,
                height: 200,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _buildFallbackIcon(node),
            ),
          );
      }
      return _buildFallbackIcon(node);
  }

  Widget _buildFallbackIcon(EncounterNode node) {
      IconData icon = Icons.auto_stories;
      Color color = KeldorTheme.primary;
      if (node.type == EncounterNodeType.fight) {
          icon = Icons.security;
          color = KeldorTheme.error;
      }
      return Icon(icon, size: 80, color: color.withOpacity(0.8));
  }

  Widget _buildActionArea(EncounterNode node) {
      if (_isTransitioning) {
          return const Center(child: CircularProgressIndicator(color: KeldorTheme.primary));
      }

      if (node.type == EncounterNodeType.choice && node.choices != null) {
          return Column(
              children: node.choices!.map((c) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: SizedBox(
                      width: double.infinity,
                      child: OutlinedButton(
                          onPressed: () => _goToNode(c.nextNodeId),
                          style: OutlinedButton.styleFrom(
                              side: const BorderSide(color: Colors.white24),
                              padding: const EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: Text(c.text, style: const TextStyle(color: Colors.white)),
                      ),
                  ),
              )).toList(),
          );
      }

      if (node.type == EncounterNodeType.input) {
          return _buildInputArea(node);
      }

      if (node.type == EncounterNodeType.order) {
          return _buildOrderArea(node);
      }

      if (node.type == EncounterNodeType.fight) {
          return Column(
              children: [
                   if (node.enemyHp != null)
                      Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Text("Ellenség Életereje: ${node.enemyHp}", style: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
                      ),
                   Row(
                       mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                       children: [
                           _buildCombatButton("TÁMADÁS", Icons.gavel, Colors.red, () => _resolveFightAction(node, "attack")),
                           _buildCombatButton("CSEL", Icons.visibility_off, Colors.blue, () => _resolveFightAction(node, "trick")),
                           _buildCombatButton("ELEMZÉS", Icons.search, Colors.amber, () => _resolveFightAction(node, "analyze")),
                       ],
                   ),
                   /*
                   const SizedBox(height: 16),
                   OutlinedButton.icon(
                       onPressed: () => _openCombatInventory(node),
                       icon: const Icon(Icons.backpack, color: Colors.white70),
                       label: const Text("Tárgy Használata", style: TextStyle(color: Colors.white)),
                   )
                   */
              ],
          );
      }

      if (node.type == EncounterNodeType.input || node.type == EncounterNodeType.order) {
          return const SizedBox.shrink();
      }

      // Generic Narrative Next or End
      return SizedBox(
          width: double.infinity,
          child: ElevatedButton(
              onPressed: () {
                  if (node.nextNodeId != null) {
                      _goToNode(node.nextNodeId!);
                  } else {
                      _finishEncounter();
                  }
              },
              child: Text(node.buttonText ?? (node.nextNodeId != null ? "TOVÁBB" : "BEFEJEZÉS")),
          ),
      );
  }

  void _goToNode(String? nodeId) {
      if (nodeId == null) {
          _finishEncounter();
          return;
      }
      setState(() {
          _isTransitioning = true;
      });
      Future.delayed(const Duration(milliseconds: 300), () {
          if (mounted) {
              setState(() {
                  _currentNodeId = nodeId;
                  _isTransitioning = false;
                  _inputController.clear();
                  _errorMessage = null;
                  _initializeNodeState();
              });
          }
      });
  }

  Widget _buildCombatButton(String label, IconData icon, Color color, VoidCallback onPressed) {
      return Column(
          children: [
              InkWell(
                  onTap: onPressed,
                  child: Container(
                      width: 60, height: 60,
                      decoration: BoxDecoration(color: color.withOpacity(0.2), shape: BoxShape.circle, border: Border.all(color: color)),
                      child: Icon(icon, color: color, size: 30),
                  ),
              ),
              const SizedBox(height: 8),
              Text(label, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold))
          ],
      );
  }

  Future<void> _resolveFightAction(EncounterNode node, String action) async {
      setState(() => _isTransitioning = true);
      
      // Determine Player Stance
      String playerStance = "strength";
      if (action == "trick") playerStance = "agility";
      if (action == "analyze") playerStance = "tactics";

      // Determine Enemy Stance (Simplistic Logic for now)
      // Ideally this should be random or predefined in node metadata
      String enemyStance = "strength";
      if (node.enemyClass == "collector") enemyStance = "agility";
      if (node.enemyClass == "archivist") enemyStance = "tactics";
      
      // Power default
      int enemyPower = node.enemyHp ?? 10;

      final token = context.read<AuthService>().token;
      if (token == null) {
          setState(() => _isTransitioning = false);
          return;
      }

      final resultData = await context.read<KeldorService>().predictCombat(token, playerStance, enemyStance, enemyPower);

      if (resultData == null) {
         ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Hiba a harc során!"), backgroundColor: Colors.red));
         setState(() => _isTransitioning = false);
         return;
      }

      final result = resultData['result']; // win, loss, draw
      final log = resultData['log'] as List<dynamic>? ?? [];
      String feedback = log.isNotEmpty ? log.last : "Harc vége.";

      // Parse log better if possible, for now just show result
      if (result == "win") {
          feedback = "GYŐZELEM! ${feedback}";
      } else if (result == "draw") {
          feedback = "DÖNTETLEN. ${feedback}";
      } else {
          feedback = "VERESÉG. ${feedback}";
      }

      await Future.delayed(const Duration(milliseconds: 800)); // Suspense

      if (!mounted) return;

      if (result == "win") {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(feedback), backgroundColor: Colors.green));
          _finishEncounter(); // Success
      } else if (result == "draw") {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(feedback), backgroundColor: Colors.orange));
          // Draw -> Stay in combat? Or counts as win for now?
          // Let's say allow retry?
          setState(() => _isTransitioning = false);
      } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(feedback), backgroundColor: Colors.red));
           if (node.failureNodeId != null) {
              _goToNode(node.failureNodeId);
           } else {
              setState(() => _isTransitioning = false);
           }
      }
  }
  
  void _openCombatInventory(EncounterNode node) {
       // Show dialog with consumable items
       // If item used matches weakness -> Win
       showDialog(context: context, builder: (ctx) => AlertDialog(
           backgroundColor: KeldorTheme.surface,
           title: const Text("Tárgy Használata", style: TextStyle(color: Colors.white)),
           content: const Text("Jelenleg nincs használható harci tárgyad.", style: TextStyle(color: Colors.white54)),
           actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Bezárás"))],
       ));
  }

  void _finishEncounter() async {
      if (_isFinishing) return;
      
      setState(() {
          _isFinishing = true;
          _isTransitioning = true;
      });

      final token = context.read<AuthService>().token;
      if (token != null) {
          try {
              final result = await context.read<KeldorService>().resolveEncounter(token, widget.encounter.id, "success");
              
              if (mounted && result != null && result['new_status'] == 'completed') {
                  await showDialog(
                      context: context,
                      barrierDismissible: false,
                      builder: (ctx) => AlertDialog(
                          backgroundColor: KeldorTheme.surface,
                          shape: RoundedRectangleBorder(
                              side: const BorderSide(color: Colors.amber, width: 2),
                              borderRadius: BorderRadius.circular(20),
                          ),
                          title: Column(
                              children: [
                                  const Icon(Icons.emoji_events, color: Colors.amber, size: 48),
                                  const SizedBox(height: 16),
                                  Text("KÜLDETÉS TELJESÍTVE!", style: GoogleFonts.cinzel(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 22)),
                              ],
                          ),
                          content: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                   Text("Sikeresen teljesítetted a feladatot!", style: GoogleFonts.outfit(color: Colors.white70)),
                                   const SizedBox(height: 20),
                                   if (result['rewards'] != null) ...[
                                       Row(
                                           mainAxisAlignment: MainAxisAlignment.center,
                                           children: [
                                               const Icon(Icons.directions_walk, color: KeldorTheme.primary, size: 20),
                                               const SizedBox(width: 8),
                                               Text("+${result['rewards']['steps']} Lépés", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                           ],
                                       ),
                                       // Show items if any
                                       if (result['rewards']['items'] != null && (result['rewards']['items'] as List).isNotEmpty)
                                           ...((result['rewards']['items'] as List).map((item) => Padding(
                                               padding: const EdgeInsets.only(top: 8),
                                               child: Row(
                                                   mainAxisAlignment: MainAxisAlignment.center,
                                                   children: [
                                                       const Icon(Icons.inventory_2, color: Colors.amber, size: 20),
                                                       const SizedBox(width: 8),
                                                       Text("+1 ${item['name']}", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                                   ],
                                               ),
                                           ))),
                                   ]
                              ],
                          ),
                          actions: [
                              SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                      style: ElevatedButton.styleFrom(backgroundColor: Colors.amber),
                                      onPressed: () => Navigator.pop(ctx),
                                      child: const Text("JUTALOM ÁTVÉTELE", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                                  ),
                              )
                          ],
                      ),
                  );
              }

          } catch (e) {
              print("Error resolving encounter: $e");
          }
      }
      
      if (mounted) {
          Navigator.pop(context);
      }
  }

  Widget _buildNoNodeError() {
      return Center(
          child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                  const Icon(Icons.error_outline, color: Colors.red, size: 64),
                  const SizedBox(height: 16),
                  const Text("Hiba: Jelenet nem található", style: TextStyle(color: Colors.white)),
                  const SizedBox(height: 24),
                  ElevatedButton(onPressed: () => Navigator.pop(context), child: const Text("VISSZA")),
              ],
          ),
      );
  }

  @override
  void dispose() {
    _inputController.dispose();
    super.dispose();
  }
}
