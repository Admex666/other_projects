// lib/screens/forum/forum_main_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/forum_service.dart';
import 'package:frontend/models/forum_models.dart';
import 'package:frontend/screens/forum/create_post_screen.dart';
import 'package:frontend/screens/forum/post_detail_screen.dart';
import 'package:frontend/screens/forum/search_users_screen.dart';
import 'package:frontend/screens/forum/notifications_screen.dart';
import 'package:frontend/screens/forum/forum_settings_screen.dart';

class ForumMainScreen extends StatefulWidget {
  final String userId;
  final String username;

  const ForumMainScreen({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _ForumMainScreenState createState() => _ForumMainScreenState();
}

class _ForumMainScreenState extends State<ForumMainScreen> {
  final ForumService _forumService = ForumService();
  final ScrollController _scrollController = ScrollController();
  
  List<ForumPost> _posts = [];
  bool _isLoading = false;
  bool _hasMore = true;
  int _skip = 0;
  final int _limit = 20;
  
  FeedType _currentFeedType = FeedType.all;
  SortBy _currentSortBy = SortBy.newest;
  PostCategory? _selectedCategory;
  
  int _unreadNotificationCount = 0;

  @override
  void initState() {
    super.initState();
    _loadPosts();
    _loadUnreadNotificationCount();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 500) {
      if (!_isLoading && _hasMore) {
        _loadMorePosts();
      }
    }
  }

  Future<void> _loadPosts() async {
    if (_isLoading) return;
    
    setState(() {
      _isLoading = true;
      _skip = 0;
      _posts.clear();
      _hasMore = true;
    });

    try {
      final response = await _forumService.getPosts(
        skip: _skip,
        limit: _limit,
        category: _selectedCategory?.value,
        feedType: _currentFeedType.value,
        sortBy: _currentSortBy.value,
      );

      final List<dynamic> postsJson = response['posts'];
      final List<ForumPost> newPosts = postsJson.map((json) => ForumPost.fromJson(json)).toList();

      setState(() {
        _posts = newPosts;
        _skip += _limit;
        _hasMore = newPosts.length == _limit;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a posztok betöltésekor: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadMorePosts() async {
    if (_isLoading || !_hasMore) return;
    
    setState(() {
      _isLoading = true;
    });

    try {
      final response = await _forumService.getPosts(
        skip: _skip,
        limit: _limit,
        category: _selectedCategory?.value,
        feedType: _currentFeedType.value,
        sortBy: _currentSortBy.value,
      );

      final List<dynamic> postsJson = response['posts'];
      final List<ForumPost> newPosts = postsJson.map((json) => ForumPost.fromJson(json)).toList();

      setState(() {
        _posts.addAll(newPosts);
        _skip += _limit;
        _hasMore = newPosts.length == _limit;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a posztok betöltésekor: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadUnreadNotificationCount() async {
    try {
      final count = await _forumService.getUnreadNotificationCount();
      setState(() {
        _unreadNotificationCount = count;
      });
    } catch (e) {
      // Ignore error for notification count
    }
  }

  Future<void> _toggleLike(ForumPost post) async {
    try {
      await _forumService.toggleLike(post.id);
      
      // Update local state
      setState(() {
        final index = _posts.indexWhere((p) => p.id == post.id);
        if (index != -1) {
          final updatedPost = ForumPost(
            id: post.id,
            userId: post.userId,
            username: post.username,
            title: post.title,
            content: post.content,
            category: post.category,
            privacyLevel: post.privacyLevel,
            createdAt: post.createdAt,
            updatedAt: post.updatedAt,
            likeCount: post.isLikedByMe ? post.likeCount - 1 : post.likeCount + 1,
            commentCount: post.commentCount,
            isLikedByMe: !post.isLikedByMe,
            isMyPost: post.isMyPost,
          );
          _posts[index] = updatedPost;
        }
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kedvelés során: $e')),
      );
    }
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => DefaultTabController(
        length: 3,
        child: AlertDialog(
          title: Text('Szűrők és rendezés'),
          content: Container(
            width: double.maxFinite,
            height: 400, // Fix magasság
            child: Column(
              children: [
                TabBar(
                  labelColor: Color(0xFF00D4AA),
                  unselectedLabelColor: Colors.grey,
                  indicatorColor: Color(0xFF00D4AA),
                  tabs: [
                    Tab(text: 'Feed'),
                    Tab(text: 'Rendezés'),
                    Tab(text: 'Kategória'),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      // Feed típusa tab
                      StatefulBuilder(
                        builder: (context, setDialogState) => ListView(
                          children: FeedType.values.map((type) => RadioListTile<FeedType>(
                            title: Text(type.displayName),
                            value: type,
                            groupValue: _currentFeedType,
                            onChanged: (value) => setDialogState(() => _currentFeedType = value!),
                          )).toList(),
                        ),
                      ),
                      
                      // Rendezés tab
                      StatefulBuilder(
                        builder: (context, setDialogState) => ListView(
                          children: SortBy.values.map((sort) => RadioListTile<SortBy>(
                            title: Text(sort.displayName),
                            value: sort,
                            groupValue: _currentSortBy,
                            onChanged: (value) => setDialogState(() => _currentSortBy = value!),
                          )).toList(),
                        ),
                      ),
                      
                      // Kategória tab
                      StatefulBuilder(
                        builder: (context, setDialogState) => ListView(
                          children: [
                            RadioListTile<PostCategory?>(
                              title: Text('Összes'),
                              value: null,
                              groupValue: _selectedCategory,
                              onChanged: (value) => setDialogState(() => _selectedCategory = value),
                            ),
                            ...PostCategory.values.map((category) => RadioListTile<PostCategory?>(
                              title: Text(category.displayName),
                              value: category,
                              groupValue: _selectedCategory,
                              onChanged: (value) => setDialogState(() => _selectedCategory = value),
                            )).toList(),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Mégse'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                _loadPosts();
              },
              child: Text('Alkalmazás'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF00D4A3),
                Color(0xFFE8F6F3),
              ],
              stops: [0.0, 0.4],
            ),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.arrow_back, color: Colors.black87),
                      onPressed: () => Navigator.pop(context),
                    ),
                    Expanded(
                      child: Text(
                        'Fórum',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    Stack(
                      children: [
                        IconButton(
                          icon: Icon(Icons.notifications_outlined, color: Colors.black87),
                          onPressed: () async {
                            await Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => NotificationsScreen(),
                              ),
                            );
                            _loadUnreadNotificationCount();
                          },
                        ),
                        if (_unreadNotificationCount > 0)
                          Positioned(
                            right: 8,
                            top: 8,
                            child: Container(
                              padding: EdgeInsets.all(2),
                              decoration: BoxDecoration(
                                color: Colors.red,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              constraints: BoxConstraints(
                                minWidth: 16,
                                minHeight: 16,
                              ),
                              child: Text(
                                '$_unreadNotificationCount',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),

              // Content area
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: Column(
                    children: [
                      // Filter and action buttons
                      Container(
                        padding: EdgeInsets.all(20),
                        child: Row(
                          children: [
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: _showFilterDialog,
                                icon: Icon(Icons.filter_list, color: Colors.white, size: 18),
                                label: Text(
                                  'Szűrők',
                                  style: TextStyle(color: Colors.white, fontSize: 14),
                                ),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Color(0xFF00D4AA),
                                  padding: EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                ),
                              ),
                            ),
                            SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => SearchUsersScreen(),
                                  ),
                                ),
                                icon: Icon(Icons.search, color: Colors.white, size: 18),
                                label: Text(
                                  'Keresés',
                                  style: TextStyle(color: Colors.white, fontSize: 14),
                                ),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.blueAccent,
                                  padding: EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                ),
                              ),
                            ),
                            SizedBox(width: 12),
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => ForumSettingsScreen(),
                                  ),
                                ),
                                icon: Icon(Icons.settings, color: Colors.white, size: 18),
                                label: Text(
                                  'Beállítások',
                                  style: TextStyle(color: Colors.white, fontSize: 14),
                                ),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.grey[600],
                                  padding: EdgeInsets.symmetric(vertical: 12),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      // Posts list
                      Expanded(
                        child: RefreshIndicator(
                          onRefresh: _loadPosts,
                          child: _posts.isEmpty && !_isLoading
                              ? Center(
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(
                                        Icons.forum_outlined,
                                        size: 64,
                                        color: Colors.grey[400],
                                      ),
                                      SizedBox(height: 16),
                                      Text(
                                        'Még nincsenek posztok',
                                        style: TextStyle(
                                          fontSize: 18,
                                          color: Colors.grey[600],
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                      SizedBox(height: 8),
                                      Text(
                                        'Legyél te az első, aki megosztja gondolatait!',
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.grey[500],
                                        ),
                                        textAlign: TextAlign.center,
                                      ),
                                    ],
                                  ),
                                )
                              : ListView.builder(
                                  controller: _scrollController,
                                  padding: EdgeInsets.symmetric(horizontal: 16),
                                  itemCount: _posts.length + (_isLoading ? 1 : 0),
                                  itemBuilder: (context, index) {
                                    if (index == _posts.length) {
                                      return Center(
                                        child: Padding(
                                          padding: EdgeInsets.all(20),
                                          child: CircularProgressIndicator(
                                            color: Color(0xFF00D4AA),
                                          ),
                                        ),
                                      );
                                    }

                                    final post = _posts[index];
                                    return _buildPostCard(post);
                                  },
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => CreatePostScreen(),
            ),
          );
          if (result == true) {
            _loadPosts();
          }
        },
        backgroundColor: Color(0xFF00D4AA),
        child: Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildPostCard(ForumPost post) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PostDetailScreen(postId: post.id),
            ),
          );
          if (result == true) {
            _loadPosts();
          }
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Post header
              Row(
                children: [
                  CircleAvatar(
                    backgroundColor: Color(0xFF00D4AA),
                    radius: 20,
                    child: Text(
                      post.username.isNotEmpty ? post.username[0].toUpperCase() : '?',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          post.username,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          _formatDateTime(post.createdAt),
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: _getCategoryColor(post.category).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      post.categoryDisplayName,
                      style: TextStyle(
                        color: _getCategoryColor(post.category),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
              
              SizedBox(height: 12),
              
              // Post title
              Text(
                post.title,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
              
              SizedBox(height: 8),
              
              // Post content preview
              Text(
                post.content,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[700],
                  height: 1.4,
                ),
              ),
              
              SizedBox(height: 16),
              
              // Post actions
              Row(
                children: [
                  InkWell(
                    onTap: () => _toggleLike(post),
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            post.isLikedByMe ? Icons.favorite : Icons.favorite_border,
                            color: post.isLikedByMe ? Colors.red : Colors.grey[600],
                            size: 18,
                          ),
                          SizedBox(width: 4),
                          Text(
                            '${post.likeCount}',
                            style: TextStyle(
                              color: Colors.grey[600],
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  SizedBox(width: 16),
                  
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.comment_outlined,
                          color: Colors.grey[600],
                          size: 18,
                        ),
                        SizedBox(width: 4),
                        Text(
                          '${post.commentCount}',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  Spacer(),
                  
                  if (post.privacyLevel != 'public')
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            post.privacyLevel == 'private' ? Icons.lock : Icons.group,
                            size: 12,
                            color: Colors.orange,
                          ),
                          SizedBox(width: 4),
                          Text(
                            post.privacyLevel == 'private' ? 'Privát' : 'Barátok',
                            style: TextStyle(
                              color: Colors.orange,
                              fontSize: 10,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getCategoryColor(String category) {
    switch (category) {
      case 'budgeting':
        return Colors.blue;
      case 'investing':
        return Colors.green;
      case 'savings':
        return Colors.orange;
      case 'career':
        return Colors.purple;
      case 'expenses':
        return Colors.red;
      case 'tips':
        return Colors.teal;
      case 'questions':
        return Colors.indigo;
      default:
        return Colors.grey;
    }
  }

  String _formatDateTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);

    if (difference.inMinutes < 1) {
      return 'Most';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes} perce';
    } else if (difference.inDays < 1) {
      return '${difference.inHours} órája';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} napja';
    } else {
      return '${dateTime.year}. ${dateTime.month.toString().padLeft(2, '0')}. ${dateTime.day.toString().padLeft(2, '0')}.';
    }
  }
}