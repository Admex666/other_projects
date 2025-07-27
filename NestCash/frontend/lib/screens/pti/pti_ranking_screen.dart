// lib/screens/pti/pti_ranking_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';

class PTIRankingScreen extends StatefulWidget {
  final String userId;
  final String username;

  const PTIRankingScreen({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _PTIRankingScreenState createState() => _PTIRankingScreenState();
}

class _PTIRankingScreenState extends State<PTIRankingScreen>
    with TickerProviderStateMixin {
  final PTIService _ptiService = PTIService();
  
  late TabController _tabController;
  PTIPeriod _selectedPeriod = PTIPeriod.weekly;
  RankingScope _selectedScope = RankingScope.global;
  
  PTIRankingResponse? _rankingData;
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadRanking();
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    super.dispose();
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) {
      setState(() {
        _selectedPeriod = PTIPeriod.values[_tabController.index];
      });
      _loadRanking();
    }
  }

  Future<void> _loadRanking() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final ranking = await _ptiService.getRanking(
        period: _selectedPeriod,
        scope: _selectedScope,
        limit: 100,
        offset: 0,
      );

      if (ranking != null) {
        setState(() {
          _rankingData = ranking;
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nem sikerült betölteni a ranglistát';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Hiba történt: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(
          'PTI Ranglista',
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.black),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.black,
          unselectedLabelColor: Colors.black54,
          indicatorColor: Colors.black,
          tabs: [
            Tab(text: 'Heti'),
            Tab(text: 'Havi'),
            Tab(text: 'Éves'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Scope selector
          Container(
            color: Colors.white,
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Text(
                  'Ranglista típusa:',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: SegmentedButton<RankingScope>(
                    segments: [
                      ButtonSegment<RankingScope>(
                        value: RankingScope.global,
                        label: Text('Globális'),
                        icon: Icon(Icons.public, size: 16),
                      ),
                      ButtonSegment<RankingScope>(
                        value: RankingScope.friends,
                        label: Text('Barátok'),
                        icon: Icon(Icons.people, size: 16),
                      ),
                    ],
                    selected: {_selectedScope},
                    onSelectionChanged: (Set<RankingScope> selection) {
                      setState(() {
                        _selectedScope = selection.first;
                      });
                      _loadRanking();
                    },
                    style: SegmentedButton.styleFrom(
                      selectedBackgroundColor: Color(0xFF00D4A3),
                      selectedForegroundColor: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildRankingContent(),
                _buildRankingContent(),
                _buildRankingContent(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRankingContent() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              _error!,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadRanking,
              child: Text('Újrapróbálás'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4A3),
              ),
            ),
          ],
        ),
      );
    }

    if (_rankingData == null || _rankingData!.rankings.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.leaderboard,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'Nincs ranglista adat',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadRanking,
      child: Column(
        children: [
          // Felhasználó saját pozíciója (ha nincs a top listában)
          if (_rankingData!.userRank != null && 
              !_rankingData!.rankings.any((r) => r.isCurrentUser))
            _buildUserPositionCard(),
          
          // Ranglista
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: _rankingData!.rankings.length,
              itemBuilder: (context, index) {
                final entry = _rankingData!.rankings[index];
                return _buildRankingItem(entry, index);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserPositionCard() {
    return Container(
      margin: EdgeInsets.all(16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF00D4A3), Color(0xFF00B894)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Color(0xFF00D4A3).withOpacity(0.3),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                '${_rankingData!.userRank}',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Az Ön pozíciója',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 14,
                  ),
                ),
                Text(
                  widget.username,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${_rankingData!.userScore?.toStringAsFixed(1) ?? 0}',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                'PTI pont',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.9),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRankingItem(PTIRankingEntry entry, int index) {
    final isCurrentUser = entry.isCurrentUser;
    final isTopThree = entry.rank <= 3;
    
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCurrentUser 
            ? Color(0xFF00D4A3).withOpacity(0.1)
            : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: isCurrentUser 
            ? Border.all(color: Color(0xFF00D4A3), width: 2)
            : null,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          // Rangsor szám/ikon
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: _getRankColor(entry.rank),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: isTopThree
                  ? Icon(
                      _getRankIcon(entry.rank),
                      color: Colors.white,
                      size: 20,
                    )
                  : Text(
                      '${entry.rank}',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
          ),
          SizedBox(width: 16),
          
          // Felhasználó info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        entry.displayName,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: isCurrentUser ? Color(0xFF00D4A3) : Colors.black,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (entry.isAnonymous)
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          'Anonim',
                          style: TextStyle(
                            fontSize: 10,
                            color: Colors.grey[600],
                          ),
                        ),
                      ),
                    if (isCurrentUser)
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Color(0xFF00D4A3),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          'Ön',
                          style: TextStyle(
                            fontSize: 10,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
                SizedBox(height: 4),
                Row(
                  children: [
                    _buildComponentChip('📚', entry.components.learningPoints, Colors.blue),
                    SizedBox(width: 4),
                    _buildComponentChip('💪', entry.components.habitScore, Colors.green),
                    SizedBox(width: 4),
                    _buildComponentChip('🏆', entry.components.badgeScore, Colors.orange),
                    SizedBox(width: 4),
                    _buildComponentChip('📊', entry.components.limitScore, Colors.purple),
                  ],
                ),
              ],
            ),
          ),
          
          // PTI pontszám
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${entry.ptiScore.toStringAsFixed(1)}',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: isCurrentUser ? Color(0xFF00D4A3) : Colors.black,
                ),
              ),
              Text(
                'PTI',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildComponentChip(String emoji, double value, Color color) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            emoji,
            style: TextStyle(fontSize: 10),
          ),
          SizedBox(width: 2),
          Text(
            '${value.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Color _getRankColor(int rank) {
    switch (rank) {
      case 1:
        return Colors.amber[600]!; // Arany
      case 2:
        return Colors.grey[400]!; // Ezüst
      case 3:
        return Colors.brown[400]!; // Bronz
      default:
        return Color(0xFF00D4A3);
    }
  }

  IconData _getRankIcon(int rank) {
    switch (rank) {
      case 1:
        return Icons.emoji_events; // Trófea
      case 2:
        return Icons.military_tech; // Médál
      case 3:
        return Icons.workspace_premium; // Kitüntetés
      default:
        return Icons.person;
    }
  }
}