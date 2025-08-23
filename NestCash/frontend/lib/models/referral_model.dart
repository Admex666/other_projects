// lib/models/referral_model.dart

enum ReferralSource {
  socialMedia,
  friendFamily,
  advertisement,
  searchEngine,
  blogArticle,
  podcast,
  appStore,
  other;

  String get value {
    switch (this) {
      case ReferralSource.socialMedia:
        return 'social_media';
      case ReferralSource.friendFamily:
        return 'friend_family';
      case ReferralSource.advertisement:
        return 'advertisement';
      case ReferralSource.searchEngine:
        return 'search_engine';
      case ReferralSource.blogArticle:
        return 'blog_article';
      case ReferralSource.podcast:
        return 'podcast';
      case ReferralSource.appStore:
        return 'app_store';
      case ReferralSource.other:
        return 'other';
    }
  }

  String get displayName {
    switch (this) {
      case ReferralSource.socialMedia:
        return 'Közösségi média';
      case ReferralSource.friendFamily:
        return 'Barát/családtag ajánlása';
      case ReferralSource.advertisement:
        return 'Hirdetés';
      case ReferralSource.searchEngine:
        return 'Keresőmotor';
      case ReferralSource.blogArticle:
        return 'Blog/cikk';
      case ReferralSource.podcast:
        return 'Podcast';
      case ReferralSource.appStore:
        return 'App áruház';
      case ReferralSource.other:
        return 'Egyéb';
    }
  }

  String get description {
    switch (this) {
      case ReferralSource.socialMedia:
        return 'Facebook, Instagram, TikTok, Twitter, stb.';
      case ReferralSource.friendFamily:
        return 'Valaki ajánlotta neked';
      case ReferralSource.advertisement:
        return 'Online vagy offline reklám';
      case ReferralSource.searchEngine:
        return 'Google, Bing keresés';
      case ReferralSource.blogArticle:
        return 'Online cikk vagy blog poszt';
      case ReferralSource.podcast:
        return 'Podcastban hallottam róla';
      case ReferralSource.appStore:
        return 'Google Play vagy App Store böngészés';
      case ReferralSource.other:
        return 'Máshol hallottam róla';
    }
  }

  static ReferralSource fromString(String value) {
    return ReferralSource.values.firstWhere(
      (source) => source.value == value,
      orElse: () => ReferralSource.other,
    );
  }
}

class ReferralSourceInfo {
  final String name;
  final String description;
  final String icon;

  const ReferralSourceInfo({
    required this.name,
    required this.description,
    required this.icon,
  });

  factory ReferralSourceInfo.fromJson(Map<String, dynamic> json) {
    return ReferralSourceInfo(
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      icon: json['icon'] ?? 'help',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'description': description,
      'icon': icon,
    };
  }
}