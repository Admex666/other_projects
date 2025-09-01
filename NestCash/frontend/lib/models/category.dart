// lib/models/category.dart
class Category {
  final String id;
  final String name;        // Tárolt érték (kulcs vagy szöveg)
  final String displayName;
  final String type;
  final String userId;

  Category({
    required this.id,
    required this.name,
    required this.displayName, 
    required this.type,
    required this.userId,
  });

  factory Category.fromJson(Map<String, dynamic> json) {
    return Category(
      id: json['id'],
      name: json['name'],
      displayName: json['display_name'] ?? json['name'],
      type: json['type'],
      userId: json['user_id'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'display_name': displayName,
      'type': type,
      'user_id': userId,
    };
  }
}