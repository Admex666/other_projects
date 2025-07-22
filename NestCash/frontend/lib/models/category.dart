// lib/models/category.dart
class Category {
  final String id;
  final String name;
  final String type; // 'income' or 'expense'
  final String userId; // A backend CategoryRead séma tartalmazza, bár a default kategóriáknál üres lehet

  Category({
    required this.id,
    required this.name,
    required this.type,
    required this.userId,
  });

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: json['id'],
      name: json['name'],
      type: json['type'],
      userId: json['user_id'] ?? '', // Kezeli, ha a user_id hiányzik (pl. default kategóriák)
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'user_id': userId,
    };
  }
}