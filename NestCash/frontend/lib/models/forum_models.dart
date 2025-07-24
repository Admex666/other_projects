// lib/models/forum_models.dart

class ForumPost {
  final String id;
  final String userId;
  final String username;
  final String title;
  final String content;
  final String category;
  final String privacyLevel;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int likeCount;
  final int commentCount;
  final bool isLikedByMe;
  final bool isMyPost;

  ForumPost({
    required this.id,
    required this.userId,
    required this.username,
    required this.title,
    required this.content,
    required this.category,
    required this.privacyLevel,
    required this.createdAt,
    required this.updatedAt,
    required this.likeCount,
    required this.commentCount,
    required this.isLikedByMe,
    required this.isMyPost,
  });

  factory ForumPost.fromJson(Map<String, dynamic> json) {
    return ForumPost(
      id: json['id'],
      userId: json['user_id'],
      username: json['username'],
      title: json['title'],
      content: json['content'],
      category: json['category'],
      privacyLevel: json['privacy_level'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      likeCount: json['like_count'],
      commentCount: json['comment_count'],
      isLikedByMe: json['is_liked_by_me'] ?? false,
      isMyPost: json['is_my_post'] ?? false,
    );
  }

  String get categoryDisplayName {
    switch (category) {
      case 'general':
        return 'Általános';
      case 'budgeting':
        return 'Költségvetés';
      case 'investing':
        return 'Befektetés';
      case 'savings':
        return 'Megtakarítás';
      case 'career':
        return 'Karrier';
      case 'expenses':
        return 'Kiadások';
      case 'tips':
        return 'Tippek';
      case 'questions':
        return 'Kérdések';
      default:
        return category;
    }
  }
}

class ForumComment {
  final String id;
  final String postId;
  final String userId;
  final String username;
  final String content;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool isMyComment;

  ForumComment({
    required this.id,
    required this.postId,
    required this.userId,
    required this.username,
    required this.content,
    required this.createdAt,
    required this.updatedAt,
    required this.isMyComment,
  });

  factory ForumComment.fromJson(Map<String, dynamic> json) {
    return ForumComment(
      id: json['id'],
      postId: json['post_id'],
      userId: json['user_id'],
      username: json['username'],
      content: json['content'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      isMyComment: json['is_my_comment'] ?? false,
    );
  }
}

class ForumUser {
  final String id;
  final String username;
  final bool isFollowing;
  final bool isFollowedBy;

  ForumUser({
    required this.id,
    required this.username,
    required this.isFollowing,
    required this.isFollowedBy,
  });

  factory ForumUser.fromJson(Map<String, dynamic> json) {
    return ForumUser(
      id: json['id'],
      username: json['username'],
      isFollowing: json['is_following'] ?? false,
      isFollowedBy: json['is_followed_by'] ?? false,
    );
  }
}

class ForumNotification {
  final String id;
  final String fromUserId;
  final String fromUsername;
  final String type;
  final String? postId;
  final String message;
  final bool isRead;
  final DateTime createdAt;

  ForumNotification({
    required this.id,
    required this.fromUserId,
    required this.fromUsername,
    required this.type,
    this.postId,
    required this.message,
    required this.isRead,
    required this.createdAt,
  });

  factory ForumNotification.fromJson(Map<String, dynamic> json) {
    return ForumNotification(
      id: json['id'],
      fromUserId: json['from_user_id'],
      fromUsername: json['from_username'],
      type: json['type'],
      postId: json['post_id'],
      message: json['message'],
      isRead: json['is_read'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  String get typeDisplayName {
    switch (type) {
      case 'like':
        return 'Kedvelés';
      case 'comment':
        return 'Komment';
      case 'follow':
        return 'Követés';
      default:
        return type;
    }
  }
}

class ForumStats {
  final int myPostsCount;
  final int myLikesReceived;
  final int followersCount;
  final int followingCount;

  ForumStats({
    required this.myPostsCount,
    required this.myLikesReceived,
    required this.followersCount,
    required this.followingCount,
  });

  factory ForumStats.fromJson(Map<String, dynamic> json) {
    return ForumStats(
      myPostsCount: json['my_posts_count'],
      myLikesReceived: json['my_likes_received'],
      followersCount: json['followers_count'],
      followingCount: json['following_count'],
    );
  }
}

enum PostCategory {
  general,
  budgeting,
  investing,
  savings,
  career,
  expenses,
  tips,
  questions,
}

extension PostCategoryExtension on PostCategory {
  String get value {
    switch (this) {
      case PostCategory.general:
        return 'general';
      case PostCategory.budgeting:
        return 'budgeting';
      case PostCategory.investing:
        return 'investing';
      case PostCategory.savings:
        return 'savings';
      case PostCategory.career:
        return 'career';
      case PostCategory.expenses:
        return 'expenses';
      case PostCategory.tips:
        return 'tips';
      case PostCategory.questions:
        return 'questions';
    }
  }

  String get displayName {
    switch (this) {
      case PostCategory.general:
        return 'Általános';
      case PostCategory.budgeting:
        return 'Költségvetés';
      case PostCategory.investing:
        return 'Befektetés';
      case PostCategory.savings:
        return 'Megtakarítás';
      case PostCategory.career:
        return 'Karrier';
      case PostCategory.expenses:
        return 'Kiadások';
      case PostCategory.tips:
        return 'Tippek';
      case PostCategory.questions:
        return 'Kérdések';
    }
  }
}

enum FeedType {
  all,
  following,
  myPosts,
}

extension FeedTypeExtension on FeedType {
  String get value {
    switch (this) {
      case FeedType.all:
        return 'all';
      case FeedType.following:
        return 'following';
      case FeedType.myPosts:
        return 'my_posts';
    }
  }

  String get displayName {
    switch (this) {
      case FeedType.all:
        return 'Minden poszt';
      case FeedType.following:
        return 'Követettek';
      case FeedType.myPosts:
        return 'Saját posztok';
    }
  }
}

enum SortBy {
  newest,
  popular,
  mostCommented,
}

extension SortByExtension on SortBy {
  String get value {
    switch (this) {
      case SortBy.newest:
        return 'newest';
      case SortBy.popular:
        return 'popular';
      case SortBy.mostCommented:
        return 'most_commented';
    }
  }

  String get displayName {
    switch (this) {
      case SortBy.newest:
        return 'Legújabb';
      case SortBy.popular:
        return 'Legnépszerűbb';
      case SortBy.mostCommented:
        return 'Legtöbb komment';
    }
  }
}