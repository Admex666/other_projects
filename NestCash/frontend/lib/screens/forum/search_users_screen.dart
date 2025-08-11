// lib/screens/forum/search_users_screen.dart
import 'package:flutter/material.dart';
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
        SnackBar(content: Text('Hiba a követettek betöltésekor: $e')),
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
        SnackBar(content: Text('Hiba a követők betöltésekor: $e')),
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
          
          String errorMessage = 'Hiba a keresés során';
          if (e.toString().contains('min_length')) {
            errorMessage = 'Legalább 3 karakter szükséges a kereséshez';
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
          content: Text(user.isFollowing ? 'Követés megszüntetve' : 'Követés elkezdve'),
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a követéskor: $e')),
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
            content: Text('Beszélgetés elindítva ${user.username} felhasználóval'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a beszélgetés indításakor: $e')),
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
          content: Text('Az accountability rendszer még nem töltődött be. Próbáld újra!'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    
    // Ellenőrizzük, hogy már van-e kapcsolat
    if (provider.isPartnerWith(user.id)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Már partner vagy ${user.username} felhasználóval'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    
    if (provider.hasPendingRequestWith(user.id)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Már van függő kérelem ${user.username} felhasználóval'),
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
        checkinFrequency: result['frequency'] ?? CheckinFrequency.weekly,
        sharedGoals: result['goals'] ?? [],
      );

      final success = await provider.sendPartnershipRequest(request);
      
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Partnership kérelem elküldve ${user.username} részére!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba: ${provider.error}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  // ÚJ FUNKCIÓ: Partnership kérelem dialógus
  Widget _buildPartnershipRequestDialog(ForumUser user) {
    final TextEditingController messageController = TextEditingController();
    CheckinFrequency selectedFrequency = CheckinFrequency.weekly;
    List<String> selectedGoals = [];
    
    final availableGoals = [
      'Pénzügyi célok',
      'Fitness/Egészség',
      'Karrier/Tanulás',
      'Személyes fejlődés',
      'Szokásépítés',
      'Projektmenedzsment',
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
                'Partnership kérelem',
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
                  'Üzenet (opcionális)',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 8),
                TextField(
                  controller: messageController,
                  maxLines: 3,
                  decoration: InputDecoration(
                    hintText: 'Mutatkozz be és írd le, miért szeretnétek partnerek lenni...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    contentPadding: EdgeInsets.all(12),
                  ),
                ),
                SizedBox(height: 16),
                
                Text(
                  'Check-in gyakoriság',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 8),
                DropdownButtonFormField<CheckinFrequency>(
                  value: selectedFrequency,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  items: CheckinFrequency.values.map((freq) {
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
                  'Közös célok (választható)',
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
                'Mégse',
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
                'Küldés',
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
          widget.isPartnerSearch ? 'Partner keresése' : 'Felhasználók keresése',
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
                          ? 'Keress accountability partnereket...'
                          : 'Keress felhasználókat...',
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
                            'Keress olyan felhasználókat, akikkel szeretnél accountability partnerek lenni',
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
              'Kezdj el gépelni a kereséshez',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              widget.isPartnerSearch 
                  ? 'Keress accountability partnereket név alapján'
                  : 'Keress felhasználókat név alapján',
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
                  'Partner',
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
                  'Függő',
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
                      ? 'Partner'
                      : hasPendingRequest
                          ? 'Kérve'
                          : 'Partner+',
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
                  user.isFollowing ? 'Követve' : 'Követés',
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