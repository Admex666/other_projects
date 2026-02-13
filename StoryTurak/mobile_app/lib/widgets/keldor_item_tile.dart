import 'package:flutter/material.dart';
import '../models/keldor_models.dart';
import '../theme.dart';

class KeldorItemHelper {
  static Color getRarityColor(String rarity) {
    switch (rarity.toLowerCase()) {
      case 'uncommon': return Colors.greenAccent;
      case 'rare': return Colors.blueAccent;
      case 'epic': return Colors.purpleAccent;
      case 'legendary': return Colors.orangeAccent;
      default: return Colors.white10;
    }
  }

  static Widget buildItemIcon(String? iconCode, Color color, double size) {
    IconData icon = Icons.help_outline;
    switch (iconCode) {
        case 'local_pharmacy': icon = Icons.local_pharmacy; break;
        case 'monetization_on': icon = Icons.monetization_on; break;
        case 'security': icon = Icons.security; break;
        case 'build': icon = Icons.build; break;
        case 'architecture': icon = Icons.architecture; break;
        case 'explore': icon = Icons.explore; break;
        case 'offline_bolt': icon = Icons.offline_bolt; break;
        case 'confirmation_number': icon = Icons.confirmation_number; break;
        case 'cookie': icon = Icons.cookie; break;
        case 'help_outline': icon = Icons.help_outline; break;
        case 'shield': icon = Icons.shield; break;
        case 'dagger_curved': icon = Icons.explore; break; 
        case 'gun': icon = Icons.offline_bolt; break; 
        case 'whip': icon = Icons.gesture; break; 
        case 'axe': icon = Icons.architecture; break;
    }
    return Icon(icon, color: color, size: size);
  }
}

class KeldorItemCard extends StatelessWidget {
  // Let's use specific fields to be flexible between Item/InventorySlot
  final String? name;
  final String rarity;
  final String? iconCode;
  final int? quantity;
  final bool isEquipped;
  final VoidCallback? onTap;
  final double size;
  final bool showQuantity;

  const KeldorItemCard({
    Key? key,
    required this.name,
    required this.rarity,
    this.iconCode,
    this.quantity,
    this.isEquipped = false,
    this.onTap,
    this.size = 70,
    this.showQuantity = true,
  }) : super(key: key);

  // Factory constructor for convenience
  factory KeldorItemCard.fromSlot(InventorySlot slot, {VoidCallback? onTap, double size = 70, bool showQuantity = true}) {
    return KeldorItemCard(
      name: slot.name,
      rarity: slot.rarity,
      iconCode: slot.iconCode,
      quantity: slot.quantity,
      isEquipped: slot.equipped,
      onTap: onTap,
      size: size,
      showQuantity: showQuantity,
    );
  }
    
  factory KeldorItemCard.fromItem(Item item, {VoidCallback? onTap, double size = 70}) {
      return KeldorItemCard(
        name: item.name,
        rarity: item.rarity,
        iconCode: item.iconCode,
        quantity: 1,
        isEquipped: false,
        onTap: onTap,
        size: size,
        showQuantity: false, // Items usually don't show qty in shop
      );
  }

  @override
  Widget build(BuildContext context) {
    final rarityColor = KeldorItemHelper.getRarityColor(rarity);
    final isCommon = rarityColor == Colors.white10;

    return InkWell(
      onTap: onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
            color: isCommon ? KeldorTheme.surface : rarityColor.withOpacity(0.15),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: isEquipped ? Colors.green : (isCommon ? Colors.white12 : rarityColor.withOpacity(0.5)), 
                width: isEquipped ? 2 : 1
            ),
            boxShadow: [
                if (!isCommon && isEquipped)
                    BoxShadow(color: rarityColor.withOpacity(0.2), blurRadius: 8, spreadRadius: 1)
            ]
        ),
        child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
                KeldorItemHelper.buildItemIcon(iconCode, isCommon ? Colors.white70 : rarityColor, size * 0.4),
                if (showQuantity && quantity != null && quantity! > 1) ...[
                    const SizedBox(height: 4),
                    Text("${quantity}x", style: TextStyle(color: isCommon ? Colors.white54 : rarityColor, fontSize: 10, fontWeight: FontWeight.bold)),
                ]
            ],
        ),
      ),
    );
  }
}

class KeldorItemTile extends StatelessWidget {
  final String name;
  final String rarity;
  final String? description;
  final String? iconCode;
  final Widget? trailing;
  final VoidCallback? onTap;

  const KeldorItemTile({
    Key? key,
    required this.name,
    required this.rarity,
    this.description,
    this.iconCode,
    this.trailing,
    this.onTap,
  }) : super(key: key);

  factory KeldorItemTile.fromItem(Item item, {Widget? trailing, VoidCallback? onTap}) {
    return KeldorItemTile(
      name: item.name,
      rarity: item.rarity,
      description: item.description,
      iconCode: item.iconCode,
      trailing: trailing,
      onTap: onTap,
    );
  }
  
  factory KeldorItemTile.fromSlot(InventorySlot slot, {Widget? trailing, VoidCallback? onTap}) {
      return KeldorItemTile(
        name: slot.name ?? "Tárgy",
        rarity: slot.rarity,
        description: slot.description, // Slot might not have desc usually, but good fallback
        iconCode: slot.iconCode,
        trailing: trailing,
        onTap: onTap,
      );
    }

  @override
  Widget build(BuildContext context) {
      final rarityColor = KeldorItemHelper.getRarityColor(rarity);
      final isCommon = rarityColor == Colors.white10;

      return Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
              color: isCommon ? KeldorTheme.surface : rarityColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: isCommon ? Colors.white12 : rarityColor.withOpacity(0.5)),
          ),
          child: ListTile(
              onTap: onTap,
              leading: KeldorItemHelper.buildItemIcon(iconCode, isCommon ? Colors.white70 : rarityColor, 32),
              title: Text(name, style: TextStyle(color: isCommon ? Colors.white : rarityColor, fontWeight: FontWeight.bold)),
              subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                      if (description != null)
                        Text(description!, style: const TextStyle(color: Colors.white54, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                      
                      const SizedBox(height: 4),
                      Text(rarity.toUpperCase(), style: TextStyle(color: isCommon ? Colors.white24 : rarityColor, fontSize: 10, letterSpacing: 1.5, fontWeight: FontWeight.bold)),
                  ],
              ),
              trailing: trailing,
          ),
      );
  }
}
