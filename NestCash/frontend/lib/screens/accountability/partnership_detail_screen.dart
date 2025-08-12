// lib/screens/accountability/partnership_detail_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:frontend/models/accountability_models.dart';
import 'package:frontend/providers/accountability_provider.dart';
import 'checkin_screen.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/screens/messages/chat_screen.dart';

class PartnershipDetailScreen extends StatefulWidget {
  final Partnership partnership;

  const PartnershipDetailScreen({
    Key? key,
    required this.partnership,
  }) : super(key: key);

  @override
  _PartnershipDetailScreenState createState() => _PartnershipDetailScreenState();
}

class _PartnershipDetailScreenState extends State<PartnershipDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<CheckIn> _checkIns = [];
  bool _isLoading = true;
  bool _hasCheckedInToday = false;

  @override
    void initState() {
      super.initState();
      _tabController = TabController(length: 3, vsync: this);
      _loadData();
    }

    Future<void> _loadData() async {
    setState(() => _isLoading = true);
    
    final provider = Provider.of<AccountabilityProvider>(context, listen: false);
    final authService = AuthService(); // AuthService példány létrehozása
    
    try {
      // Load check-ins
      await provider.loadRecentCheckIns(widget.partnership.id, limit: 50);
      
      final userId = await authService.getUserId(); // AuthService-ből userId lekérése
      
      if (userId != null) {
        // Check if user has checked in today
        final hasCheckedIn = await provider.hasCheckedInToday(
          widget.partnership.id, 
          userId, // AuthService-ből kapott userId
        );
        
        setState(() {
          _checkIns = provider.recentCheckIns;
          _hasCheckedInToday = hasCheckedIn;
        });
      } else {
        setState(() {
          _checkIns = provider.recentCheckIns;
          _hasCheckedInToday = false;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba az adatok betöltésekor: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: Icon(Icons.arrow_back, color: Colors.black87, size: 24),
                  ),
                  Expanded(
                    child: Text(
                      widget.partnership.partnerUsername,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: _handleMenuAction,
                    icon: Icon(Icons.more_vert, color: Colors.black87),
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        value: 'end',
                        child: Row(
                          children: [
                            Icon(Icons.close, color: Colors.red, size: 20),
                            SizedBox(width: 8),
                            Text('Partnership lezárása'),
                          ],
                        ),
                      ),
                      PopupMenuItem(
                        value: 'block',
                        child: Row(
                          children: [
                            Icon(Icons.block, color: Colors.red, size: 20),
                            SizedBox(width: 8),
                            Text('Felhasználó blokkolása'),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Stats summary
            Container(
              padding: EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                children: [
                  Expanded(
                    child: _buildStatCard(
                      'Összes check-in',
                      widget.partnership.totalCheckins.toString(),
                      Icons.check_circle,
                      Color(0xFF4CAF50),
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: _buildStatCard(
                      'Sikeresség',
                      '${widget.partnership.successRate.toStringAsFixed(0)}%',
                      Icons.trending_up,
                      Color(0xFF2196F3),
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: _buildStatCard(
                      'Gyakoriság',
                      widget.partnership.checkinFrequency.displayName,
                      Icons.schedule,
                      Color(0xFF9C27B0),
                    ),
                  ),
                ],
              ),
            ),

            SizedBox(height: 20),

            // Content
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: Column(
                  children: [
                    // Tab bar
                    Container(
                      margin: EdgeInsets.all(20),
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
                      child: TabBar(
                        controller: _tabController,
                        indicator: BoxDecoration(
                          color: Color(0xFF00D4AA),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        labelColor: Colors.white,
                        unselectedLabelColor: Colors.grey[600],
                        labelStyle: TextStyle(fontWeight: FontWeight.w600),
                        tabs: [
                          Tab(text: 'Áttekintés'),
                          Tab(text: 'Check-in-ek'),
                          Tab(text: 'Célok'),
                        ],
                      ),
                    ),

                    // Tab content
                    Expanded(
                      child: TabBarView(
                        controller: _tabController,
                        children: [
                          _buildOverviewTab(),
                          _buildCheckInsTab(),
                          _buildGoalsTab(),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      // Floating check-in button
      floatingActionButton: widget.partnership.isActive && !_hasCheckedInToday
          ? FloatingActionButton.extended(
              onPressed: _showCheckInDialog,
              backgroundColor: Color(0xFF00D4AA),
              icon: Icon(Icons.add_task, color: Colors.white),
              label: Text(
                'Check-in',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            )
          : null,
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Partnership info
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
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
                Row(
                  children: [
                    Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        color: Color(0xFF00D4AA).withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          widget.partnership.partnerUsername.isNotEmpty
                              ? widget.partnership.partnerUsername[0].toUpperCase()
                              : '?',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF00D4AA),
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
                            widget.partnership.partnerUsername,
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                          ),
                          SizedBox(height: 4),
                          Container(
                            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: _getStatusColor().withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              widget.partnership.statusDisplayName,
                              style: TextStyle(
                                color: _getStatusColor(),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                
                // Chat gomb hozzáadása
                SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => ChatScreen(
                            otherUserId: widget.partnership.partnerUserId,
                            otherUsername: widget.partnership.partnerUsername,
                          ),
                        ),
                      );
                    },
                    icon: Icon(Icons.chat_bubble_outline, size: 18),
                    label: Text('Chat megnyitása'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Color(0xFF00D4AA),
                      side: BorderSide(color: Color(0xFF00D4AA)),
                      padding: EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  ),
                ),
                
                if (widget.partnership.acceptedAt != null) ...[
                  SizedBox(height: 16),
                  Text(
                    'Partnership kezdete: ${_formatDate(widget.partnership.acceptedAt!)}',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                  ),
                ],
              ],
            ),
          ),

          SizedBox(height: 20),

          // Today's status
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
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
                  'Mai állapot',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                SizedBox(height: 16),
                Row(
                  children: [
                    Icon(
                      _hasCheckedInToday ? Icons.check_circle : Icons.radio_button_unchecked,
                      color: _hasCheckedInToday ? Colors.green : Colors.grey[400],
                      size: 24,
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _hasCheckedInToday 
                            ? 'Már beszámoltál ma!' 
                            : 'Még nem számoltál be ma',
                        style: TextStyle(
                          color: _hasCheckedInToday ? Colors.green : Colors.grey[600],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
                if (!_hasCheckedInToday) ...[
                  SizedBox(height: 12),
                  Text(
                    'Ne felejtsd el leadni a mai check-in-ed!',
                    style: TextStyle(
                      color: Colors.orange[700],
                      fontSize: 14,
                    ),
                  ),
                ],
              ],
            ),
          ),

          SizedBox(height: 20),

          // Recent activity
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
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
                  'Legutóbbi aktivitás',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                SizedBox(height: 16),
                if (_checkIns.isNotEmpty) ...[
                  ..._checkIns.take(3).map((checkIn) => _buildRecentCheckInItem(checkIn)),
                ] else ...[
                  Text(
                    'Még nincsenek check-in-ek',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentCheckInItem(CheckIn checkIn) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Color(0xFFF5F5F5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(
            checkIn.goalsMet ? Icons.check_circle : Icons.cancel,
            color: checkIn.goalsMet ? Colors.green : Colors.red,
            size: 20,
          ),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      checkIn.date,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    SizedBox(width: 8),
                    // Felhasználó megjelenítése
                    Consumer<AccountabilityProvider>(
                      builder: (context, provider, child) {
                        final isMyCheckIn = provider.currentUserId == checkIn.userId;
                        return Container(
                          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isMyCheckIn 
                                ? Color(0xFF00D4AA).withOpacity(0.1)
                                : Colors.orange.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            isMyCheckIn ? 'Te' : widget.partnership.partnerUsername,
                            style: TextStyle(
                              color: isMyCheckIn ? Color(0xFF00D4AA) : Colors.orange[700],
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                ),
                if (checkIn.notes != null && checkIn.notes!.isNotEmpty)
                  Padding(
                    padding: EdgeInsets.only(top: 4),
                    child: Text(
                      checkIn.notes!,
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 12,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
            ),
          ),
          Text(
            '${checkIn.progressRating}/5',
            style: TextStyle(
              color: Color(0xFF00D4AA),
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCheckInsTab() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
      );
    }

    if (_checkIns.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.assignment_turned_in,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              'Még nincsenek check-in-ek',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.grey[600],
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Itt jelennek meg a beszámolók',
              style: TextStyle(
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(20),
      itemCount: _checkIns.length,
      itemBuilder: (context, index) {
        final checkIn = _checkIns[index];
        return _buildCheckInCard(checkIn);
      },
    );
  }

  Widget _buildCheckInCard(CheckIn checkIn) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Icon(
                  checkIn.goalsMet ? Icons.check_circle : Icons.cancel,
                  color: checkIn.goalsMet ? Colors.green : Colors.red,
                  size: 24,
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        checkIn.date,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                      SizedBox(height: 4),
                      // Felhasználó megjelenítése
                      Consumer<AccountabilityProvider>(
                        builder: (context, provider, child) {
                          final isMyCheckIn = provider.currentUserId == checkIn.userId;
                          return Row(
                            children: [
                              Container(
                                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: isMyCheckIn 
                                      ? Color(0xFF00D4AA).withOpacity(0.1)
                                      : Colors.orange.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  isMyCheckIn ? 'Te' : widget.partnership.partnerUsername,
                                  style: TextStyle(
                                    color: isMyCheckIn ? Color(0xFF00D4AA) : Colors.orange[700],
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Color(0xFF00D4AA).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${checkIn.progressRating}/5',
                    style: TextStyle(
                      color: Color(0xFF00D4AA),
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),

            SizedBox(height: 12),

            // Status
            Text(
              checkIn.goalsMet ? 'Célok teljesítve' : 'Célok nem teljesítve',
              style: TextStyle(
                color: checkIn.goalsMet ? Colors.green : Colors.red,
                fontWeight: FontWeight.w500,
              ),
            ),

            // Notes
            if (checkIn.notes != null && checkIn.notes!.isNotEmpty) ...[
              SizedBox(height: 12),
              Text(
                'Jegyzetek:',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[700],
                ),
              ),
              SizedBox(height: 4),
              Text(
                checkIn.notes!,
                style: TextStyle(
                  color: Colors.grey[600],
                  height: 1.4,
                ),
              ),
            ],

            // Progress rating visualization
            SizedBox(height: 12),
            Row(
              children: [
                Text(
                  'Haladás: ',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: Colors.grey[700],
                  ),
                ),
                ...List.generate(5, (index) {
                  return Icon(
                    index < checkIn.progressRating ? Icons.star : Icons.star_outline,
                    color: Color(0xFF00D4AA),
                    size: 20,
                  );
                }),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGoalsTab() {
    return Padding(
      padding: EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Shared goals
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
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
                  'Közös célok',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                SizedBox(height: 16),
                if (widget.partnership.sharedGoals.isNotEmpty) ...[
                  ...widget.partnership.sharedGoals.map((goal) => _buildGoalItem(goal)),
                ] else ...[
                  Text(
                    'Nincsenek meghatározott közös célok',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 14,
                    ),
                  ),
                ],
              ],
            ),
          ),

          SizedBox(height: 20),

          // Check-in frequency
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
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
                  'Check-in beállítások',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
                SizedBox(height: 16),
                Row(
                  children: [
                    Icon(Icons.schedule, color: Color(0xFF00D4AA), size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Gyakoriság: ${widget.partnership.checkinFrequency.displayName}',
                      style: TextStyle(
                        color: Colors.grey[700],
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGoalItem(String goal) {
    return Container(
      margin: EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(
            Icons.assistant_direction_outlined,
            color: Color(0xFF00D4AA),
            size: 20,
          ),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              goal,
              style: TextStyle(
                color: Colors.grey[700],
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor() {
    switch (widget.partnership.status) {
      case PartnershipStatus.active:
        return Colors.green;
      case PartnershipStatus.pending:
        return Colors.orange;
      case PartnershipStatus.declined:
        return Colors.red;
      case PartnershipStatus.ended:
        return Colors.grey;
      case PartnershipStatus.blocked:
        return Colors.red;
    }
  }

  String _formatDate(DateTime date) {
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
  }

  Future<void> _showCheckInDialog() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => CheckInScreen(
          partnershipId: widget.partnership.id,
          partnerName: widget.partnership.partnerUsername,
        ),
      ),
    );

    if (result == true) {
      _loadData(); // Refresh data after check-in
    }
  }

  void _handleMenuAction(String action) {
    switch (action) {
      case 'end':
        _showEndPartnershipDialog();
        break;
      case 'block':
        _showBlockUserDialog();
        break;
    }
  }

  Future<void> _showEndPartnershipDialog() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Partnership lezárása'),
        content: Text('Biztosan le szeretnéd zárni ezt a partnership-et?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Mégse'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: Text('Lezárás'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final provider = Provider.of<AccountabilityProvider>(context, listen: false);
      final success = await provider.endPartnership(widget.partnership.id);
      
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Partnership lezárva'),
            backgroundColor: Colors.green,
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

  Future<void> _showBlockUserDialog() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Felhasználó blokkolása'),
        content: Text('Biztosan blokkolni szeretnéd ${widget.partnership.partnerUsername} felhasználót?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Mégse'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: Text('Blokkolás'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      // Itt implementálhatod a blokkolás logikát
      // Jelenleg nincs backend API hozzá a meglévő service-ben
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Blokkolás funkció még nem implementált'),
          backgroundColor: Colors.orange,
        ),
      );
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }
}