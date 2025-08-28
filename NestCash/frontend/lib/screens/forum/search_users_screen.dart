// lib/screens/forum/search_users_screen.dart
import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/services/forum_service.dart';
import 'package:frontend/models/forum_models.dart';
import 'package:frontend/screens/messages/chat_screen.dart';
import 'package:frontend/providers/accountability_provider.dart';
import 'package:frontend/models/accountability_models.dart';
import 'package:provider/provider.dart';
import 'dart:async';

class SearchUsersScreen extends StatefulWidget {
  final bool isPartnerSearch; // Új paraméter
  
  const SearchUsersScreen({
    Key? key,
    this.isPartnerSearch = false,
  }) : super(key: key);

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
  Timer? _searchDebounce;

  @override
  void initState() {
    super.initState();
    _loadFollowing();
    _loadFollowers();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchDebounce?.cancel();
    super.dispose();
  }

  Future<void> _loadFollowing() async {
    try {
      final users = await _forumService.getFollowing();
      
      setState(() {
        _following = users;
        _isLoadingFollowing = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingFollowing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_loading_following'.tr(namedArgs: {'error': e.toString()}))),
      );
    }
  }

  Future<void> _loadFollowers() async {
    try {
      final users = await _forumService.getFollowers();
      
      setState(() {
        _followers = users;
        _isLoadingFollowers = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingFollowers = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_loading_followers'..tr(namedArgs:{'error': e.toString()}))),
      );
    }
  }

  Future<void> _searchUsers(String query) async {
    _searchDebounce?.cancel();
    
    if (query.trim().isEmpty || query.trim().length < 3) {
      setState(() {
        _searchResults.clear();
        _isSearching = false;
      });
      return;
    }

    setState(() {
      _isSearching = true;
    });

    _searchDebounce = Timer(Duration(milliseconds: 500), () async {
      if (!mounted) return;
      
      try {
        final users = await _forumService.searchUsers(query.trim());
        
        if (mounted) {
          setState(() {
            _searchResults = users;
            _isSearching = false;
          });
        }
      } catch (e) {
        if (mounted) {
          setState(() {
            _isSearching = false;
          });
          
          String errorMessage = 'error_searching_users_general'.tr();
          if (e.toString().contains('min_length')) {
            errorMessage = 'error_search_min_length'.tr();
          }
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(errorMessage)),
          );
        }
      }
    });
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
          content: Text(user.isFollowing ? 'follow_stopped'.tr() : 'follow_started'.tr()),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_following_user'.tr(namedArgs:{'error': e.toString()}))),
      );
    }
  }

  Future<void> _startConversation(ForumUser user) async {
    try {
      final result = await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ChatScreen(
            otherUserId: user.id,
            otherUsername: user.username,
          ),
        ),
      );
      
      if (result != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('conversation_started_with'.tr(namedArgs:{'username': user.username})),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_starting_conversation'.tr(namedArgs:{'error': e.toString()}))),
      );
    }
  }

  // ÚJ FUNKCIÓ: Partner kérelem küldése
  Future<void> _sendPartnershipRequest(ForumUser user) async {
    if (!widget.isPartnerSearch) return;
    
    final provider = Provider.of<AccountabilityProvider>(context, listen: false);

    // Ellenőrizzük, hogy a provider inicializált-e
    if (!provider.isInitialized) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('accountability_system_not_loaded'.tr()),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    
    // Ellenőrizzük, hogy már van-e kapcsolat
    if (provider.isPartnerWith(user.id)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('already_partner_with'.tr(namedArgs:{'username': user.username})),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    
    if (provider.hasPendingRequestWith(user.id)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('pending_request_exists_with'.tr(namedArgs:{'username': user.username})),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // Partnership kérelem dialógus
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => _buildPartnershipRequestDialog(user),
    );

    if (result != null) {
      final request = PartnershipRequest(
        targetUserId: user.id,
        message: result['message'] ?? '',
        checkinFrequency: result['frequency'] ?? CheckInFrequency.weekly,
        sharedGoals: result['goals'] ?? [],
      );

      final success = await provider.sendPartnershipRequest(request);
      
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('partnership_request_sent_to'.tr(namedArgs:{'username': user.username})),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('error_occurred'.tr(namedArgs:{'error': provider.error.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // ÚJ FUNKCIÓ: Partnership kérelem dialógus
  Widget _buildPartnershipRequestDialog(ForumUser user) {
    final TextEditingController messageController = TextEditingController();
    CheckInFrequency selectedFrequency = CheckInFrequency.weekly;
    List<String> selectedGoals = [];
    
    final availableGoals = [
      'goal_financial'.tr(),
      'goal_fitness_health'.tr(),
      'goal_career_learning'.tr(),
      'goal_personal_development'.tr(),
      'goal_habit_building'.tr(),
      'goal_project_management'.tr(),
    ];

    return StatefulBuilder(
      builder: (context, setDialogState) {
        return AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          title: Column(
            children: [
              CircleAvatar(
                backgroundColor: Color(0xFF00D4AA),
                radius: 30,
                child: Text(
                  user.username.isNotEmpty ? user.username[0].toUpperCase() : '?',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 24,
                  ),
                ),
              ),
              SizedBox(height: 12),
              Text(
                'partnership_request_title'.tr(),
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              Text(
                user.username,
                style: TextStyle(fontSize: 16, color: Colors.grey[600]),
              ),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'message_optional'.tr(),
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 8),
                TextField(
                  controller: messageController,
                  maxLines: 3,
                  decoration: InputDecoration(
                    hintText: 'partnership_intro_message_hint'.tr(),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    contentPadding: EdgeInsets.all(12),
                  ),
                ),
                SizedBox(height: 16),
                
                Text(
                  'checkin_frequency_title'.tr(),
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 8),
                DropdownButtonFormField<CheckInFrequency>(
                  value: selectedFrequency,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  items: CheckInFrequency.values.map((freq) {
                    return DropdownMenuItem(
                      value: freq,
                      child: Text(freq.displayName),
                    );
                  }).toList(),
                  onChanged: (value) {
                    if (value != null) {
                      setDialogState(() {
                        selectedFrequency = value;
                      });
                    }
                  },
                ),
                SizedBox(height: 16),
                
                Text(
                  'shared_goals_optional'.tr(),
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: availableGoals.map((goal) {
                    final isSelected = selectedGoals.contains(goal);
                    return FilterChip(
                      label: Text(
                        goal,
                        style: TextStyle(
                          color: isSelected ? Colors.white : Colors.grey[700],
                          fontSize: 12,
                        ),
                      ),
                      selected: isSelected,
                      onSelected: (selected) {
                        setDialogState(() {
                          if (selected) {
                            selectedGoals.add(goal);
                          } else {
                            selectedGoals.remove(goal);
                          }
                        });
                      },
                      selectedColor: Color(0xFF00D4AA),
                      checkmarkColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text(
                'cancel'.tr(),
                style: TextStyle(color: Colors.grey[600]),
              ),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop({
                  'message': messageController.text.trim(),
                  'frequency': selectedFrequency,
                  'goals': selectedGoals,
                });
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4AA),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                'send'.tr(),
                style: TextStyle(color: Colors.white),
              ),
            ),
          ],
        );
      },
    );
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
          widget.isPartnerSearch ? 'search_partners'.tr() : 'search_users'.tr(),
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
            child: Column(
              children: [
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(25),
                  ),
                  child: TextField(
                    controller: _searchController,
                    onChanged: _searchUsers,
                    decoration: InputDecoration(
                      hintText: widget.isPartnerSearch 
                          ? 'search_partners_hint'.tr()
                          : 'search_users_hint'.tr(),
                      hintStyle: TextStyle(color: Colors.grey[600]),
                      prefixIcon: Icon(
                        widget.isPartnerSearch ? Icons.people : Icons.search, 
                        color: Colors.grey[600]
                      ),
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
                
                // Partner search info
                if (widget.isPartnerSearch) ...[
                  SizedBox(height: 12),
                  Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.info_outline, color: Colors.black87, size: 20),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'search_partners_info'.tr(),
                            style: TextStyle(
                              color: Colors.black87,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),

          // Tabs (csak ha nem partner search)
          if (!widget.isPartnerSearch) ...[
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
                          'search_tab'.tr(),
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
                          'following_tab'.tr(namedArgs:{'count': _following.length.toString()}),
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
                          'followers_tab'.tr(namedArgs:{'count': _followers.length.toString()}),
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
          ],

          // Content
          Expanded(
            child: widget.isPartnerSearch ? _buildSearchResults() : _buildTabContent(),
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
              widget.isPartnerSearch ? Icons.people_alt : Icons.search,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'start_typing_to_search'.tr(),
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              widget.isPartnerSearch 
                  ? 'search_partners_by_name'.tr()
                  : 'search_users_by_name'.tr(),
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
              'no_results'.tr(),
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'try_different_search_terms'.tr(),
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
              'not_following_anyone_yet'.tr(),
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'search_and_follow_users'.tr(),
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
              'no_followers_yet'.tr(),
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'share_interesting_posts_get_followers'.tr(),
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
    // Csak akkor használjuk a providert, ha partner search módban vagyunk
    final accountabilityProvider = widget.isPartnerSearch 
        ? Provider.of<AccountabilityProvider>(context, listen: false)
        : null;
    
    final isPartner = widget.isPartnerSearch 
        ? (accountabilityProvider?.isPartnerWith(user.id) ?? false)
        : false;
    final hasPendingRequest = widget.isPartnerSearch 
        ? (accountabilityProvider?.hasPendingRequestWith(user.id) ?? false)
        : false;
        
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
        title: Row(
          children: [
            Text(
              user.username,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            if (isPartner) ...[
              SizedBox(width: 8),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Color(0xFF00D4AA).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'partner_label'.tr(),
                  style: TextStyle(
                    color: Color(0xFF00D4AA),
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ] else if (hasPendingRequest) ...[
              SizedBox(width: 8),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'pending_label'.tr(),
                  style: TextStyle(
                    color: Colors.orange,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ],
        ),
        subtitle: SizedBox(height: 4),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Üzenet gomb
            ElevatedButton(
              onPressed: () => _startConversation(user),
              child: Icon(
                Icons.message,
                size: 18,
                color: Colors.white,
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4AA),
                elevation: 0,
                padding: EdgeInsets.all(8),
                shape: CircleBorder(),
                minimumSize: Size(36, 36),
              ),
            ),
            SizedBox(width: 8),
            
            // Partner/Követés gomb
            if (widget.isPartnerSearch) ...[
              ElevatedButton(
                onPressed: isPartner || hasPendingRequest 
                    ? null 
                    : () => _sendPartnershipRequest(user),
                child: Text(
                  isPartner 
                      ? 'partner_label'.tr()
                      : hasPendingRequest
                          ? 'requested_label'.tr()
                          : 'add_partner'.tr(),
                  style: TextStyle(
                    color: isPartner || hasPendingRequest 
                        ? Colors.grey[700] 
                        : Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: isPartner 
                      ? Colors.green.withOpacity(0.2)
                      : hasPendingRequest
                          ? Colors.orange.withOpacity(0.2)
                          : Color(0xFF00D4AA),
                  elevation: 0,
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                ),
              ),
            ] else ...[
              ElevatedButton(
                onPressed: () => _toggleFollow(user),
                child: Text(
                  user.isFollowing ? 'following_label'.tr() : 'follow'.tr(),
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
            ],
          ],
        ),
      ),
    );
  }
}