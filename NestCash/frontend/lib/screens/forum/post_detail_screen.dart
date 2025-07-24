// lib/screens/forum/post_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/forum_service.dart';
import 'package:frontend/models/forum_models.dart';

class PostDetailScreen extends StatefulWidget {
  final String postId;

  const PostDetailScreen({
    Key? key,
    required this.postId,
  }) : super(key: key);

  @override
  _PostDetailScreenState createState() => _PostDetailScreenState();
}

class _PostDetailScreenState extends State<PostDetailScreen> {
  final ForumService _forumService = ForumService();
  final TextEditingController _commentController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  ForumPost? _post;
  List<ForumComment> _comments = [];
  bool _isLoadingPost = true;
  bool _isLoadingComments = true;
  bool _isSubmittingComment = false;
  bool _hasMoreComments = true;
  int _commentsSkip = 0;
  final int _commentsLimit = 50;

  @override
  void initState() {
    super.initState();
    _loadPost();
    _loadComments();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _commentController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 500) {
      if (!_isLoadingComments && _hasMoreComments) {
        _loadMoreComments();
      }
    }
  }

  Future<void> _loadPost() async {
    try {
      final postData = await _forumService.getPost(widget.postId);
      setState(() {
        _post = ForumPost.fromJson(postData);
        _isLoadingPost = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingPost = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a poszt betöltésekor: $e')),
      );
    }
  }

  Future<void> _loadComments() async {
    try {
      final response = await _forumService.getComments(
        widget.postId,
        skip: 0,
        limit: _commentsLimit,
      );

      final List<dynamic> commentsJson = response['comments'];
      final List<ForumComment> newComments = commentsJson
          .map((json) => ForumComment.fromJson(json))
          .toList();

      setState(() {
        _comments = newComments;
        _commentsSkip = _commentsLimit;
        _hasMoreComments = newComments.length == _commentsLimit;
        _isLoadingComments = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingComments = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kommentek betöltésekor: $e')),
      );
    }
  }

  Future<void> _loadMoreComments() async {
    if (_isLoadingComments || !_hasMoreComments) return;

    setState(() {
      _isLoadingComments = true;
    });

    try {
      final response = await _forumService.getComments(
        widget.postId,
        skip: _commentsSkip,
        limit: _commentsLimit,
      );

      final List<dynamic> commentsJson = response['comments'];
      final List<ForumComment> newComments = commentsJson
          .map((json) => ForumComment.fromJson(json))
          .toList();

      setState(() {
        _comments.addAll(newComments);
        _commentsSkip += _commentsLimit;
        _hasMoreComments = newComments.length == _commentsLimit;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kommentek betöltésekor: $e')),
      );
    } finally {
      setState(() {
        _isLoadingComments = false;
      });
    }
  }

  Future<void> _toggleLike() async {
    if (_post == null) return;

    try {
      await _forumService.toggleLike(_post!.id);
      
      setState(() {
        _post = ForumPost(
          id: _post!.id,
          userId: _post!.userId,
          username: _post!.username,
          title: _post!.title,
          content: _post!.content,
          category: _post!.category,
          privacyLevel: _post!.privacyLevel,
          createdAt: _post!.createdAt,
          updatedAt: _post!.updatedAt,
          likeCount: _post!.isLikedByMe ? _post!.likeCount - 1 : _post!.likeCount + 1,
          commentCount: _post!.commentCount,
          isLikedByMe: !_post!.isLikedByMe,
          isMyPost: _post!.isMyPost,
        );
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kedvelés során: $e')),
      );
    }
  }

  Future<void> _submitComment() async {
    if (_commentController.text.trim().isEmpty || _isSubmittingComment) return;

    setState(() {
      _isSubmittingComment = true;
    });

    try {
      final commentData = await _forumService.createComment(
        widget.postId,
        _commentController.text.trim(),
      );

      final newComment = ForumComment.fromJson(commentData);
      
      setState(() {
        _comments.insert(0, newComment);
        _commentController.clear();
        if (_post != null) {
          _post = ForumPost(
            id: _post!.id,
            userId: _post!.userId,
            username: _post!.username,
            title: _post!.title,
            content: _post!.content,
            category: _post!.category,
            privacyLevel: _post!.privacyLevel,
            createdAt: _post!.createdAt,
            updatedAt: _post!.updatedAt,
            likeCount: _post!.likeCount,
            commentCount: _post!.commentCount + 1,
            isLikedByMe: _post!.isLikedByMe,
            isMyPost: _post!.isMyPost,
          );
        }
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Komment sikeresen elküldve!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a komment küldésekor: $e')),
      );
    } finally {
      setState(() {
        _isSubmittingComment = false;
      });
    }
  }

  Future<void> _deleteComment(ForumComment comment) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Komment törlése'),
        content: Text('Biztosan törölni szeretnéd ezt a kommentet?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Mégse'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Törlés', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await _forumService.deleteComment(comment.id);
        
        setState(() {
          _comments.removeWhere((c) => c.id == comment.id);
          if (_post != null) {
            _post = ForumPost(
              id: _post!.id,
              userId: _post!.userId,
              username: _post!.username,
              title: _post!.title,
              content: _post!.content,
              category: _post!.category,
              privacyLevel: _post!.privacyLevel,
              createdAt: _post!.createdAt,
              updatedAt: _post!.updatedAt,
              likeCount: _post!.likeCount,
              commentCount: _post!.commentCount - 1,
              isLikedByMe: _post!.isLikedByMe,
              isMyPost: _post!.isMyPost,
            );
          }
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Komment sikeresen törölve!')),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hiba a komment törlésekor: $e')),
        );
      }
    }
  }

  Future<void> _deletePost() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Poszt törlése'),
        content: Text('Biztosan törölni szeretnéd ezt a posztot?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Mégse'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Törlés', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await _forumService.deletePost(widget.postId);
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Poszt sikeresen törölve!')),
        );
        
        Navigator.pop(context, true);
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hiba a poszt törlésekor: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFF5F5F5),
      appBar: AppBar(
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Poszt részletei',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          if (_post?.isMyPost == true)
            PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'delete') {
                  _deletePost();
                }
              },
              itemBuilder: (context) => [
                PopupMenuItem(
                  value: 'delete',
                  child: Row(
                    children: [
                      Icon(Icons.delete, color: Colors.red, size: 20),
                      SizedBox(width: 8),
                      Text('Törlés', style: TextStyle(color: Colors.red)),
                    ],
                  ),
                ),
              ],
            ),
        ],
      ),
      body: _isLoadingPost
          ? Center(child: CircularProgressIndicator(color: Color(0xFF00D4AA)))
          : _post == null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text(
                        'Nem sikerült betölteni a posztot',
                        style: TextStyle(fontSize: 18, color: Colors.grey[600]),
                      ),
                    ],
                  ),
                )
              : Column(
                  children: [
                    // Post content
                    Expanded(
                      child: SingleChildScrollView(
                        controller: _scrollController,
                        child: Column(
                          children: [
                            // Post card
                            Container(
                              margin: EdgeInsets.all(16),
                              padding: EdgeInsets.all(20),
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
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // Post header
                                  Row(
                                    children: [
                                      CircleAvatar(
                                        backgroundColor: Color(0xFF00D4AA),
                                        radius: 24,
                                        child: Text(
                                          _post!.username.isNotEmpty
                                              ? _post!.username[0].toUpperCase()
                                              : '?',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 18,
                                          ),
                                        ),
                                      ),
                                      SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              _post!.username,
                                              style: TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 16,
                                              ),
                                            ),
                                            Text(
                                              _formatDateTime(_post!.createdAt),
                                              style: TextStyle(
                                                color: Colors.grey[600],
                                                fontSize: 12,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Container(
                                        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                        decoration: BoxDecoration(
                                          color: _getCategoryColor(_post!.category).withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(16),
                                        ),
                                        child: Text(
                                          _post!.categoryDisplayName,
                                          style: TextStyle(
                                            color: _getCategoryColor(_post!.category),
                                            fontSize: 12,
                                            fontWeight: FontWeight.w500,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  
                                  SizedBox(height: 16),
                                  
                                  // Post title
                                  Text(
                                    _post!.title,
                                    style: TextStyle(
                                      fontSize: 22,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.black87,
                                    ),
                                  ),
                                  
                                  SizedBox(height: 12),
                                  
                                  // Post content
                                  Text(
                                    _post!.content,
                                    style: TextStyle(
                                      fontSize: 16,
                                      color: Colors.grey[700],
                                      height: 1.5,
                                    ),
                                  ),
                                  
                                  SizedBox(height: 20),
                                  
                                  // Post actions
                                  Row(
                                    children: [
                                      InkWell(
                                        onTap: _toggleLike,
                                        borderRadius: BorderRadius.circular(20),
                                        child: Container(
                                          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                          decoration: BoxDecoration(
                                            color: _post!.isLikedByMe
                                                ? Colors.red.withOpacity(0.1)
                                                : Colors.grey.withOpacity(0.1),
                                            borderRadius: BorderRadius.circular(20),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Icon(
                                                _post!.isLikedByMe ? Icons.favorite : Icons.favorite_border,
                                                color: _post!.isLikedByMe ? Colors.red : Colors.grey[600],
                                                size: 20,
                                              ),
                                              SizedBox(width: 6),
                                              Text(
                                                '${_post!.likeCount}',
                                                style: TextStyle(
                                                  color: _post!.isLikedByMe ? Colors.red : Colors.grey[600],
                                                  fontSize: 16,
                                                  fontWeight: FontWeight.w500,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                      
                                      SizedBox(width: 16),
                                      
                                      Container(
                                        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                        decoration: BoxDecoration(
                                          color: Colors.grey.withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(20),
                                        ),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(
                                              Icons.comment_outlined,
                                              color: Colors.grey[600],
                                              size: 20,
                                            ),
                                            SizedBox(width: 6),
                                            Text(
                                              '${_post!.commentCount}',
                                              style: TextStyle(
                                                color: Colors.grey[600],
                                                fontSize: 16,
                                                fontWeight: FontWeight.w500,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),

                                      Spacer(),
                                      
                                      if (_post!.privacyLevel != 'public')
                                        Container(
                                          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                          decoration: BoxDecoration(
                                            color: Colors.orange.withOpacity(0.1),
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              Icon(
                                                _post!.privacyLevel == 'private' ? Icons.lock : Icons.group,
                                                size: 14,
                                                color: Colors.orange,
                                              ),
                                              SizedBox(width: 4),
                                              Text(
                                                _post!.privacyLevel == 'private' ? 'Privát' : 'Barátok',
                                                style: TextStyle(
                                                  color: Colors.orange,
                                                  fontSize: 12,
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

                            // Comments section
                            Container(
                              margin: EdgeInsets.symmetric(horizontal: 16),
                              padding: EdgeInsets.all(16),
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
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Kommentek (${_post!.commentCount})',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.black87,
                                    ),
                                  ),
                                  
                                  SizedBox(height: 16),
                                  
                                  if (_isLoadingComments)
                                    Center(
                                      child: Padding(
                                        padding: EdgeInsets.all(20),
                                        child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
                                      ),
                                    )
                                  else if (_comments.isEmpty)
                                    Center(
                                      child: Padding(
                                        padding: EdgeInsets.all(20),
                                        child: Column(
                                          children: [
                                            Icon(
                                              Icons.comment_outlined,
                                              size: 48,
                                              color: Colors.grey[400],
                                            ),
                                            SizedBox(height: 8),
                                            Text(
                                              'Még nincsenek kommentek',
                                              style: TextStyle(
                                                color: Colors.grey[600],
                                                fontSize: 16,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    )
                                  else
                                    Column(
                                      children: [
                                        ..._comments.map((comment) => _buildCommentCard(comment)).toList(),
                                        if (_isLoadingComments)
                                          Padding(
                                            padding: EdgeInsets.all(16),
                                            child: Center(
                                              child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
                                            ),
                                          ),
                                      ],
                                    ),
                                ],
                              ),
                            ),
                            
                            SizedBox(height: 100), // Space for comment input
                          ],
                        ),
                      ),
                    ),

                    // Comment input
                    Container(
                      padding: EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        border: Border(
                          top: BorderSide(color: Colors.grey[200]!),
                        ),
                      ),
                      child: SafeArea(
                        child: Row(
                          children: [
                            Expanded(
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.grey[100],
                                  borderRadius: BorderRadius.circular(25),
                                ),
                                child: TextField(
                                  controller: _commentController,
                                  decoration: InputDecoration(
                                    hintText: 'Írj egy kommentet...',
                                    hintStyle: TextStyle(color: Colors.grey[600]),
                                    contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                                    border: InputBorder.none,
                                  ),
                                  maxLines: null,
                                  textCapitalization: TextCapitalization.sentences,
                                ),
                              ),
                            ),
                            SizedBox(width: 12),
                            InkWell(
                              onTap: _isSubmittingComment ? null : _submitComment,
                              child: Container(
                                padding: EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Color(0xFF00D4AA),
                                  shape: BoxShape.circle,
                                ),
                                child: _isSubmittingComment
                                    ? SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(
                                          color: Colors.white,
                                          strokeWidth: 2,
                                        ),
                                      )
                                    : Icon(
                                        Icons.send,
                                        color: Colors.white,
                                        size: 20,
                                      ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildCommentCard(ForumComment comment) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                backgroundColor: Color(0xFF00D4AA),
                radius: 16,
                child: Text(
                  comment.username.isNotEmpty ? comment.username[0].toUpperCase() : '?',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
              SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      comment.username,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                    Text(
                      _formatDateTime(comment.createdAt),
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
              if (comment.isMyComment)
                PopupMenuButton<String>(
                  onSelected: (value) {
                    if (value == 'delete') {
                      _deleteComment(comment);
                    }
                  },
                  itemBuilder: (context) => [
                    PopupMenuItem(
                      value: 'delete',
                      child: Row(
                        children: [
                          Icon(Icons.delete, color: Colors.red, size: 16),
                          SizedBox(width: 8),
                          Text('Törlés', style: TextStyle(color: Colors.red, fontSize: 14)),
                        ],
                      ),
                    ),
                  ],
                  child: Icon(Icons.more_vert, size: 16, color: Colors.grey[600]),
                ),
            ],
          ),
          
          SizedBox(height: 8),
          
          Text(
            comment.content,
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[700],
              height: 1.4,
            ),
          ),
        ],
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