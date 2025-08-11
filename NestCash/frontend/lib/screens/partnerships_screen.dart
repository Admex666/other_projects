// lib/screens/partnerships_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/accountability_models.dart';
import '../providers/accountability_provider.dart';
import '../providers/subscription_provider.dart';
import 'partner_matching_screen.dart';
import '../screens/forum/search_users_screen.dart';
import 'partnership_detail_screen.dart';

class PartnershipsScreen extends StatefulWidget {
  const PartnershipsScreen({Key? key}) : super(key: key);

  @override
  _PartnershipsScreenState createState() => _PartnershipsScreenState();
}

class _PartnershipsScreenState extends State<PartnershipsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    
    final provider = Provider.of<AccountabilityProvider>(context, listen: false);
    await provider.loadPartnerships();
    
    setState(() => _isLoading = false);
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
                      'Accountability partnerek',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  IconButton(
                    onPressed: _loadData,
                    icon: Icon(Icons.refresh, color: Colors.black87, size: 24),
                  ),
                ],
              ),
            ),

            // Action buttons
            Container(
              padding: EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                children: [
                  Expanded(
                    child: Consumer<SubscriptionProvider>(
                      builder: (context, subscription, child) {
                        return Container(
                          height: 44,
                          child: ElevatedButton.icon(
                            onPressed: () {
                              if (subscription.isPlusOrHigher) {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => PartnerMatchingScreen(),
                                  ),
                                ).then((_) => _loadData());
                              } else {
                                // Módosított rész: SearchUsersScreen partner móddal
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => SearchUsersScreen(isPartnerSearch: true),
                                  ),
                                ).then((_) => _loadData());
                              }
                            },
                            icon: Icon(
                              subscription.isPlusOrHigher ? Icons.auto_awesome : Icons.search,
                              color: Colors.white,
                              size: 20,
                            ),
                            label: Text(
                              subscription.isPlusOrHigher ? 'Matching' : 'Keresés',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.orange,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        );
                      },
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
                          Tab(text: 'Aktív'),
                          Tab(text: 'Kérelmek'),
                        ],
                      ),
                    ),

                    // Tab content
                    Expanded(
                      child: TabBarView(
                        controller: _tabController,
                        children: [
                          _buildActivePartnersTab(),
                          _buildRequestsTab(),
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
    );
  }

  Widget _buildActivePartnersTab() {
    return Consumer<AccountabilityProvider>(
      builder: (context, provider, child) {
        if (_isLoading) {
          return Center(
            child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
          );
        }

        final activePartners = provider.activePartnerships;

        if (activePartners.isEmpty) {
          return _buildEmptyState(
            icon: Icons.group,
            title: 'Nincs aktív partner',
            message: 'Kezdj el új kapcsolatokat építeni!',
            actionText: 'Partner keresése',
              onAction: () {
                final subscription = Provider.of<SubscriptionProvider>(context, listen: false);
                if (subscription.isPlusOrHigher) {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => PartnerMatchingScreen()),
                  ).then((_) => _loadData());
                } else {
                  // Módosított rész: SearchUsersScreen partner móddal
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => SearchUsersScreen(isPartnerSearch: true)),
                  ).then((_) => _loadData());
                }
              },
          );
        }

        return ListView.builder(
          padding: EdgeInsets.all(20),
          itemCount: activePartners.length,
          itemBuilder: (context, index) {
            return _buildPartnershipCard(activePartners[index]);
          },
        );
      },
    );
  }

  Widget _buildRequestsTab() {
    return Consumer<AccountabilityProvider>(
      builder: (context, provider, child) {
        if (_isLoading) {
          return Center(
            child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
          );
        }

        final pendingPartners = provider.pendingPartnerships;

        if (pendingPartners.isEmpty) {
          return _buildEmptyState(
            icon: Icons.hourglass_empty,
            title: 'Nincs függő kérelem',
            message: 'Itt jelennek meg a partnership kérelmek.',
          );
        }

        return ListView.builder(
          padding: EdgeInsets.all(20),
          itemCount: pendingPartners.length,
          itemBuilder: (context, index) {
            return _buildPartnershipCard(pendingPartners[index], isPending: true);
          },
        );
      },
    );
  }

  Widget _buildPartnershipCard(Partnership partnership, {bool isPending = false}) {
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
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PartnershipDetailScreen(partnership: partnership),
            ),
          ).then((_) => _loadData());
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  // Avatar
                  Container(
                    width: 50,
                    height: 50,
                    decoration: BoxDecoration(
                      color: Color(0xFF00D4AA).withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Text(
                        partnership.partnerUsername.isNotEmpty
                            ? partnership.partnerUsername[0].toUpperCase()
                            : '?',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF00D4AA),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 16),
                  
                  // Name and status
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          partnership.partnerUsername,
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 4),
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getStatusColor(partnership.status).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            partnership.statusDisplayName,
                            style: TextStyle(
                              color: _getStatusColor(partnership.status),
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Arrow
                  Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.grey[400],
                    size: 16,
                  ),
                ],
              ),

              if (!isPending) ...[
                SizedBox(height: 16),
                
                // Stats
                Row(
                  children: [
                    Expanded(
                      child: _buildStatItem(
                        'Check-in-ek',
                        partnership.totalCheckins.toString(),
                        Icons.check_circle_outline,
                      ),
                    ),
                    Expanded(
                      child: _buildStatItem(
                        'Sikeresség',
                        '${partnership.successRate.toStringAsFixed(0)}%',
                        Icons.trending_up,
                      ),
                    ),
                    Expanded(
                      child: _buildStatItem(
                        'Gyakoriság',
                        partnership.checkinFrequency.displayName,
                        Icons.schedule,
                      ),
                    ),
                  ],
                ),
              ],

              if (isPending) ...[
                SizedBox(height: 16),
                
                // Pending actions
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 36,
                        child: OutlinedButton(
                          onPressed: () => _respondToPartnership(partnership.id, false),
                          style: OutlinedButton.styleFrom(
                            side: BorderSide(color: Colors.red),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: Text(
                            'Elutasítás',
                            style: TextStyle(
                              color: Colors.red,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Container(
                        height: 36,
                        child: ElevatedButton(
                          onPressed: () => _respondToPartnership(partnership.id, true),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Color(0xFF00D4AA),
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: Text(
                            'Elfogadás',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],

              // Shared goals
              if (partnership.sharedGoals.isNotEmpty) ...[
                SizedBox(height: 16),
                Text(
                  'Közös célok:',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey[700],
                  ),
                ),
                SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: partnership.sharedGoals.take(3).map((goal) {
                    return Container(
                      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Color(0xFF00D4AA).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        goal,
                        style: TextStyle(
                          color: Color(0xFF00D4AA),
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    );
                  }).toList(),
                ),
                if (partnership.sharedGoals.length > 3)
                  Padding(
                    padding: EdgeInsets.only(top: 4),
                    child: Text(
                      '+${partnership.sharedGoals.length - 3} további',
                      style: TextStyle(
                        color: Colors.grey[500],
                        fontSize: 11,
                      ),
                    ),
                  ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: Color(0xFF00D4AA), size: 20),
        SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String message,
    String? actionText,
    VoidCallback? onAction,
  }) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              title,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.grey[600],
              ),
            ),
            SizedBox(height: 8),
            Text(
              message,
              style: TextStyle(
                color: Colors.grey[500],
              ),
              textAlign: TextAlign.center,
            ),
            if (actionText != null && onAction != null) ...[
              SizedBox(height: 24),
              Container(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: onAction,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFF00D4AA),
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Text(
                    actionText,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(PartnershipStatus status) {
    switch (status) {
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

  Future<void> _respondToPartnership(String partnershipId, bool accept) async {
    final provider = Provider.of<AccountabilityProvider>(context, listen: false);
    
    final success = await provider.respondToPartnership(partnershipId, accept);
    
    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(accept ? 'Partnership elfogadva!' : 'Partnership elutasítva'),
          backgroundColor: accept ? Colors.green : Colors.orange,
        ),
      );
      _loadData();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hiba történt: ${provider.error}'),
          backgroundColor: Colors.red,
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