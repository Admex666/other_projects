// lib/screens/forum/search_users_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/forum_service.dart';
import 'package:frontend/models/forum_models.dart';

class SearchUsersScreen extends StatefulWidget {
  const SearchUsersScreen({Key? key}) : super(key: key);

  @override
  _SearchUsersScreenState createState() => _SearchUsersScreenState();
}

class _SearchUsersScreenState extends State<SearchUsersScreen> {
  final ForumService _forumService = ForumService();
  final TextEditingController _searchController = TextEditingController();
  
  List<ForumUser> _searchResults = [];
  List<ForumUser> _following = [];
  List<ForumUser> _followers = [];
  bool _isSearching = false;
  bool _isLoadingFollowing = true;
  bool _isLoadingFollowers = true;
  
  int _selectedTab = 0;

  @override
  void initState() {
    super.initState();
    _loadFollowing();
    _loadFollowers();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadFollowing() async {
    try {
      final response = await _forumService.getFollowing();
      final List<dynamic> usersJson = response['following'];
      final List<ForumUser> users = usersJson.map((json) => ForumUser.fromJson(json)).toList();
      
      setState(() {
        _following = users;
        _isLoadingFollowing = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingFollowing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a követettek betöltésekor: $e')),
      );
    }
  }

  Future<void> _loadFollowers() async {
    try {
      final response = await _forumService.getFollowers();
      final List<dynamic> usersJson = response['followers'];
      final List<ForumUser> users = usersJson.map((json) => ForumUser.fromJson(json)).toList();
      
      setState(() {
        _followers = users;
        _isLoadingFollowers = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingFollowers = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a követők betöltésekor: $e')),
      );
    }
  }

  Future<void> _searchUsers(String query) async {
    if (query.trim().isEmpty) {
      setState(() {
        _searchResults.clear();
      });
      return;
    }

    setState(() {
      _isSearching = true;
    });

    try {
      final response = await _forumService.searchUsers(query.trim());
      final List<dynamic> usersJson = response['users'];
      final List<ForumUser> users = usersJson.map((json) => ForumUser.fromJson(json)).toList();
      
      setState(() {
        _searchResults = users;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a keresés során: $e')),
      );
    } finally {
      setState(() {
        _isSearching = false;
      });
    }
  }

  Future<void> _toggleFollow(ForumUser user) async {
    try {
      if (user.isFollowing) {
        await _forumService.unfollowUser(user.id);
      } else {
        await _forumService.followUser(user.id);
      }

      // Update local state
      setState(() {
        // Update in search results
        final searchIndex = _searchResults.indexWhere((u) => u.id == user.id);
        if (searchIndex != -1) {
          _searchResults[searchIndex] = ForumUser(
            id: user.id,
            username: user.username,
            isFollowing: !user.isFollowing,
            isFollowedBy: user.isFollowedBy,
          );
        }

        // Update in following list
        if (user.isFollowing) {
          _following.removeWhere((u) => u.id == user.id);
        } else {
          _following.add(ForumUser(
            id: user.id,
            username: user.username,
            isFollowing: !user.isFollowing,
            isFollowedBy: user.isFollowedBy,
          ));
        }
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(user.isFollowing ? 'Követés megszüntetve' : 'Követés elkezdve'),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a követéskor: $e')),
      );
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
          'Felhasználók keresése',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: Column(
        children: [
          // Search bar
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Color(0xFF00D4A3),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(30),
                bottomRight: Radius.circular(30),
              ),
            ),
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(25),
              ),
              child: TextField(
                controller: _searchController,
                onChanged: _searchUsers,
                decoration: InputDecoration(
                  hintText: 'Keress felhasználókat...',
                  hintStyle: TextStyle(color: Colors.grey[600]),
                  prefixIcon: Icon(Icons.search, color: Colors.grey[600]),
                  suffixIcon: _isSearching
                      ? Padding(
                          padding: EdgeInsets.all(12),
                          child: SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              color: Color(0xFF00D4AA),
                              strokeWidth: 2,
                            ),
                          ),
                        )
                      : _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: Icon(Icons.clear, color: Colors.grey[600]),
                              onPressed: () {
                                _searchController.clear();
                                setState(() {
                                  _searchResults.clear();
                                });
                              },
                            )
                          : null,
                  contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  border: InputBorder.none,
                ),
              ),
            ),
          ),

          // Tabs
          Container(
            margin: EdgeInsets.all(16),
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
            child: Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: () => setState(() => _selectedTab = 0),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        color: _selectedTab == 0 ? Color(0xFF00D4AA) : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'Keresés',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: _selectedTab == 0 ? Colors.white : Colors.grey[600],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: InkWell(
                    onTap: () => setState(() => _selectedTab = 1),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        color: _selectedTab == 1 ? Color(0xFF00D4AA) : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'Követettek (${_following.length})',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: _selectedTab == 1 ? Colors.white : Colors.grey[600],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: InkWell(
                    onTap: () => setState(() => _selectedTab = 2),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        color: _selectedTab == 2 ? Color(0xFF00D4AA) : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'Követők (${_followers.length})',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: _selectedTab == 2 ? Colors.white : Colors.grey[600],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Content
          Expanded(
            child: _buildTabContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildTabContent() {
    switch (_selectedTab) {
      case 0:
        return _buildSearchResults();
      case 1:
        return _buildFollowingList();
      case 2:
        return _buildFollowersList();
      default:
        return _buildSearchResults();
    }
  }

  Widget _buildSearchResults() {
    if (_searchController.text.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.search,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'Kezdj el gépelni a kereséshez',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Keress felhasználókat név alapján',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    if (_searchResults.isEmpty && !_isSearching) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.person_search,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'Nincs találat',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Próbálj meg más keresési feltételt',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.symmetric(horizontal: 16),
      itemCount: _searchResults.length,
      itemBuilder: (context, index) {
        final user = _searchResults[index];
        return _buildUserCard(user);
      },
    );
  }

  Widget _buildFollowingList() {
    if (_isLoadingFollowing) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
      );
    }

    if (_following.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.people_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'Még nem követsz senkit',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Keress és kövesd más felhasználókat',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.symmetric(horizontal: 16),
      itemCount: _following.length,
      itemBuilder: (context, index) {
        final user = _following[index];
        return _buildUserCard(user);
      },
    );
  }

  Widget _buildFollowersList() {
    if (_isLoadingFollowers) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
      );
    }

    if (_followers.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.people_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'Még nincsenek követőid',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Ossz meg érdekes posztokat és találj követőket',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.symmetric(horizontal: 16),
      itemCount: _followers.length,
      itemBuilder: (context, index) {
        final user = _followers[index];
        return _buildUserCard(user);
      },
    );
  }

  Widget _buildUserCard(ForumUser user) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
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
      child: ListTile(
        contentPadding: EdgeInsets.all(16),
        leading: CircleAvatar(
          backgroundColor: Color(0xFF00D4AA),
          radius: 24,
          child: Text(
            user.username.isNotEmpty ? user.username[0].toUpperCase() : '?',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
        ),
        title: Text(
          user.username,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(height: 4),
            /*
            Row(
              children: [
                Text(
                  '${user.followerCount} követő',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
                SizedBox(width: 16),
                Text(
                  '${user.followingCount} követett',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            */
          ],
        ),
        trailing: ElevatedButton(
          onPressed: () => _toggleFollow(user),
          child: Text(
            user.isFollowing ? 'Követés megszüntetése' : 'Követés',
            style: TextStyle(
              color: user.isFollowing ? Colors.grey[700] : Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
          style: ElevatedButton.styleFrom(
            backgroundColor: user.isFollowing ? Colors.grey[200] : Color(0xFF00D4AA),
            elevation: 0,
            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ),
      ),
    );
  }
}