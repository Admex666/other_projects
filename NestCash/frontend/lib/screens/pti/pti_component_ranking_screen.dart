// lib/screens/pti/pti_component_ranking_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';

class PTIComponentRankingScreen extends StatefulWidget {
  final String userId;
  final String username;
  final PTIComponent? initialComponent;
  final PTIPeriod? initialPeriod;

  const PTIComponentRankingScreen({
    Key? key,
    required this.userId,
    required this.username,
    this.initialComponent,
    this.initialPeriod,
  }) : super(key: key);

  @override
  _PTIComponentRankingScreenState createState() => _PTIComponentRankingScreenState();
}

class _PTIComponentRankingScreenState extends State<PTIComponentRankingScreen>
    with TickerProviderStateMixin {
  final PTIService _ptiService = PTIService();
  
  late TabController _periodTabController;
  PTIPeriod _selectedPeriod = PTIPeriod.weekly;
  PTIComponent _selectedComponent = PTIComponent.total;
  RankingScope _selectedScope = RankingScope.global;
  
  PTIComponentRankingResponse? _rankingData;
  bool _isLoading = false;
  String? _error;

  final List<PTIComponent> _availableComponents = [
    PTIComponent.total,
    PTIComponent.learning,
    PTIComponent.habits,
    PTIComponent.badges,
    PTIComponent.limits,
  ];

  @override
  void initState() {
    super.initState();
    
    // Kezdeti értékek beállítása
    _selectedPeriod = widget.initialPeriod ?? PTIPeriod.weekly;
    _selectedComponent = widget.initialComponent ?? PTIComponent.total;
    
    _periodTabController = TabController(
      length: 3, 
      vsync: this,
      initialIndex: PTIPeriod.values.indexOf(_selectedPeriod),
    );
    _periodTabController.addListener(_onPeriodTabChanged);
    
    _loadComponentRanking();
  }

  @override
  void dispose() {
    _periodTabController.removeListener(_onPeriodTabChanged);
    _periodTabController.dispose();
    super.dispose();
  }

  void _onPeriodTabChanged() {
    if (_periodTabController.indexIsChanging) {
      setState(() {
        _selectedPeriod = PTIPeriod.values[_periodTabController.index];
      });
      _loadComponentRanking();
    }
  }

  Future<void> _loadComponentRanking() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final ranking = await _ptiService.getComponentRanking(
        period: _selectedPeriod,
        component: _selectedComponent,
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
          _error = 'Nem sikerült betölteni a komponens ranglistát';
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
          'PTI Komponens Ranglisták',
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.black),
        bottom: TabBar(
          controller: _periodTabController,
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
          // Komponens és scope selectorok
          _buildControlsSection(),
          
          // Ranglista tartalom
          Expanded(
            child: TabBarView(
              controller: _periodTabController,
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

  Widget _buildControlsSection() {
    return Container(
      color: Colors.white,
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          // Komponens kiválasztás
          Row(
            children: [
              Icon(
                Icons.category,
                color: Color(0xFF00D4A3),
                size: 20,
              ),
              SizedBox(width: 8),
              Text(
                'Komponens:',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          
          // Komponens gombok
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _availableComponents.map((component) {
              final isSelected = _selectedComponent == component;
              return GestureDetector(
                onTap: () {
                  setState(() {
                    _selectedComponent = component;
                  });
                  _loadComponentRanking();
                },
                child: Container(
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: isSelected 
                        ? Color(0xFF00D4A3) 
                        : Colors.grey[200],
                    borderRadius: BorderRadius.circular(20),
                    border: isSelected 
                        ? Border.all(color: Color(0xFF00D4A3), width: 2)
                        : null,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _getComponentIcon(component),
                        style: TextStyle(fontSize: 16),
                      ),
                      SizedBox(width: 6),
                      Text(
                        _getComponentName(component),
                        style: TextStyle(
                          color: isSelected ? Colors.white : Colors.black87,
                          fontWeight: isSelected 
                              ? FontWeight.bold 
                              : FontWeight.normal,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
          SizedBox(height: 16),
          
          // Scope selector
          Row(
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
                    _loadComponentRanking();
                  },
                  style: SegmentedButton.styleFrom(
                    selectedBackgroundColor: Color(0xFF00D4A3),
                    selectedForegroundColor: Colors.white,
                  ),
                ),
              ),
            ],
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
              onPressed: _loadComponentRanking,
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
            Text(
              _getComponentIcon(_selectedComponent),
              style: TextStyle(fontSize: 64),
            ),
            SizedBox(height: 16),
            Text(
              'Nincs ${_getComponentName(_selectedComponent).toLowerCase()} ranglista adat',
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
      onRefresh: _loadComponentRanking,
      child: Column(
        children: [
          // Header info kártya
          _buildHeaderInfoCard(),
          
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
                return _buildComponentRankingItem(entry, index);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderInfoCard() {
    return Container(
      margin: EdgeInsets.all(16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              Text(
                _getComponentIcon(_selectedComponent),
                style: TextStyle(fontSize: 32),
              ),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _rankingData!.componentDisplayName,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${_selectedPeriod.displayName} ranglista',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Color(0xFF00D4A3).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  '${_rankingData!.totalParticipants} résztvevő',
                  style: TextStyle(
                    color: Color(0xFF00D4A3),
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildUserPositionCard() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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
                if (_rankingData!.userPercentile != null)
                  Text(
                    'Top ${(100 - _rankingData!.userPercentile!).toStringAsFixed(1)}%',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.9),
                      fontSize: 12,
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
                'pont',
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

  Widget _buildComponentRankingItem(PTIComponentRankingEntry entry, int index) {
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
                    Text(
                      'Percentilis: ${entry.percentile.toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                    Spacer(),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: _getComponentColor(_selectedComponent).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${_getScoreDisplayText(entry.componentScore)}',
                        style: TextStyle(
                          fontSize: 12,
                          color: _getComponentColor(_selectedComponent),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          
          // Komponens pontszám
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${entry.componentScore.toStringAsFixed(1)}',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: isCurrentUser ? Color(0xFF00D4A3) : Colors.black,
                ),
              ),
              Text(
                _getScoreUnit(_selectedComponent),
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

  String _getComponentIcon(PTIComponent component) {
    switch (component) {
      case PTIComponent.learning:
        return '📚';
      case PTIComponent.habits:
        return '💪';
      case PTIComponent.badges:
        return '🏆';
      case PTIComponent.limits:
        return '📊';
      case PTIComponent.total:
        return '🏆';
    }
  }

  String _getComponentName(PTIComponent component) {
    switch (component) {
      case PTIComponent.learning:
        return 'Tanulás';
      case PTIComponent.habits:
        return 'Szokások';
      case PTIComponent.badges:
        return 'Kitűzők';
      case PTIComponent.limits:
        return 'Limitek';
      case PTIComponent.total:
        return 'Összesített PTI';
    }
  }

  Color _getComponentColor(PTIComponent component) {
    switch (component) {
      case PTIComponent.learning:
        return Colors.blue;
      case PTIComponent.habits:
        return Colors.green;
      case PTIComponent.badges:
        return Colors.orange;
      case PTIComponent.limits:
        return Colors.purple;
      case PTIComponent.total:
        return Color(0xFF00D4A3);
    }
  }

  String _getScoreUnit(PTIComponent component) {
    switch (component) {
      case PTIComponent.total:
        return 'PTI';
      default:
        return 'pont';
    }
  }

  String _getScoreDisplayText(double score) {
    if (_selectedComponent == PTIComponent.habits) {
      return '${score.toInt()} szokás';
    } else if (_selectedComponent == PTIComponent.badges) {
      return '${score.toInt()} badge';
    } else if (_selectedComponent == PTIComponent.limits) {
      return '${score.toStringAsFixed(1)} betartás';
    }
    return '${score.toStringAsFixed(1)} pont';
  }

  Color _getRankColor(int rank) {
    switch (rank) {
      case 1:
        return Colors.amber[600]!;
      case 2:
        return Colors.grey[400]!;
      case 3:
        return Colors.brown[400]!;
      default:
        return Color(0xFF00D4A3);
    }
  }

  IconData _getRankIcon(int rank) {
    switch (rank) {
      case 1:
        return Icons.emoji_events;
      case 2:
        return Icons.military_tech;
      case 3:
        return Icons.workspace_premium;
      default:
        return Icons.person;
    }
  }
}