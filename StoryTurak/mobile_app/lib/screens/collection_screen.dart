import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/keldor_service.dart';
import '../services/auth_service.dart';
import '../models/keldor_models.dart';
import '../theme.dart';

class CollectionScreen extends StatefulWidget {
  const CollectionScreen({Key? key}) : super(key: key);

  @override
  State<CollectionScreen> createState() => _CollectionScreenState();
}

class _CollectionScreenState extends State<CollectionScreen> {
  List<Collection> _collections = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadCollections();
  }

  Future<void> _loadCollections() async {
    final token = context.read<AuthService>().token;
    if (token != null) {
      final cols = await context.read<KeldorService>().fetchCollections(token);
      if (mounted) {
        setState(() {
          _collections = cols;
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KeldorTheme.background,
      appBar: AppBar(
        title: const Text("Gyűjtőalbum", style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: _isLoading 
          ? const Center(child: CircularProgressIndicator()) 
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _collections.length,
              itemBuilder: (ctx, index) {
                  return _buildCollectionCard(_collections[index]);
              },
          ),
    );
  }

  Widget _buildCollectionCard(Collection col) {
      // Calculate progress
      final double progress = col.totalItems > 0 ? col.foundItems / col.totalItems : 0.0;
      
      return Container(
          margin: const EdgeInsets.only(bottom: 24),
          decoration: BoxDecoration(
              color: const Color(0xFF1E293B),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white10),
          ),
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                  // HEADER
                  Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                              Text(col.name, style: const TextStyle(color: Colors.amber, fontSize: 18, fontWeight: FontWeight.bold)),
                              const SizedBox(height: 4),
                              Text(col.description, style: const TextStyle(color: Colors.white54, fontSize: 14)),
                              const SizedBox(height: 12),
                              Row(
                                  children: [
                                      Expanded(
                                          child: ClipRRect(
                                              borderRadius: BorderRadius.circular(4),
                                              child: LinearProgressIndicator(
                                                  value: progress,
                                                  backgroundColor: Colors.black,
                                                  color: Colors.amber,
                                                  minHeight: 8,
                                              ),
                                          ),
                                      ),
                                      const SizedBox(width: 12),
                                      Text("${col.foundItems} / ${col.totalItems}", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                  ],
                              )
                          ],
                      ),
                  ),
                  
                  // GRID
                  GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 4,
                          childAspectRatio: 0.8,
                          crossAxisSpacing: 8,
                          mainAxisSpacing: 8,
                      ),
                      itemCount: col.items.length,
                      itemBuilder: (ctx, idx) {
                          final item = col.items[idx];
                          return _buildCollectionItem(item);
                      },
                  )
              ],
          ),
      );
  }

  Widget _buildCollectionItem(CollectionItem item) {
      final rarityColor = _getRarityColor(item.rarity);
      final isCommon = rarityColor == Colors.white10;
      
      return Column(
          children: [
              Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                      color: item.found ? (isCommon ? Colors.white10 : rarityColor.withOpacity(0.2)) : Colors.black26,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                          color: item.found ? (isCommon ? Colors.white24 : rarityColor) : Colors.white10,
                          width: item.found ? 1.5 : 1
                      ),
                      boxShadow: [
                          if (item.found && !isCommon)
                              BoxShadow(color: rarityColor.withOpacity(0.2), blurRadius: 4, spreadRadius: 0)
                      ]
                  ),
                  child: Icon(
                      item.found ? _getIcon(item.iconCode) : Icons.lock_outline,
                      color: item.found ? (isCommon ? Colors.white70 : rarityColor) : Colors.white12,
                      size: 24,
                  ),
              ),
              const SizedBox(height: 4),
              Text(
                  item.name,
                  style: TextStyle(
                      color: item.found ? Colors.white70 : Colors.white24,
                      fontSize: 10,
                      fontWeight: item.found ? FontWeight.bold : FontWeight.normal
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
              ),
              if (item.found) 
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(item.rarity.toUpperCase(), style: TextStyle(color: isCommon ? Colors.white12 : rarityColor, fontSize: 8)),
                  )
          ],
      );
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

  IconData _getIcon(String code) {
      switch (code) {
          case 'architecture': return Icons.architecture;
          case 'explore': return Icons.explore;
          case 'offline_bolt': return Icons.offline_bolt;
          case 'confirmation_number': return Icons.confirmation_number;
          case 'monetization_on': return Icons.monetization_on;
          case 'local_pharmacy': return Icons.local_pharmacy;
          case 'help_outline': return Icons.help_outline;
          case 'security': return Icons.security;
          case 'build': return Icons.build;
          case 'cookie': return Icons.cookie;
          default: return Icons.circle;
      }
  }
}
