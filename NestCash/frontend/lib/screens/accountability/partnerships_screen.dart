// lib/screens/accountability/partnerships_screen.dart

import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/utils/category_translate.dart';
import 'package:provider/provider.dart';
import 'package:frontend/models/accountability_models.dart';
import 'package:frontend/providers/accountability_provider.dart';
import 'package:frontend/providers/subscription_provider.dart';
import 'partner_matching_screen.dart';
import 'accountability_setup_screen.dart';
import 'package:frontend/screens/forum/search_users_screen.dart';
import 'partnership_detail_screen.dart';
import 'package:frontend/widgets/subscription/upgrade_dialog.dart';
import 'package:frontend/models/subscription.dart';

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
    
    await provider.refreshCurrentUser();
    await provider.loadPartnerships();
    
    // DEBUG: partnership-ek ellenőrzése
    print('=== LOADED PARTNERSHIPS ===');
    for (final partnership in provider.partnerships) {
      print('Partnership: id=${partnership.id}, '
            'partnerUserId=${partnership.partnerUserId}, '
            'status=${partnership.status}, '
            'isIncoming=${partnership.isIncoming}');
    }
    print('Current user ID: ${provider.currentUserId}');
    print('=== END PARTNERSHIPS ===');

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
                      'accountability_partners'.tr(),
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
                    flex: 2,
                    child: Consumer<SubscriptionProvider>(
                      builder: (context, subscription, child) {
                        if (subscription.isPlusOrHigher) {
                          return Container(
                            height: 44,
                            child: ElevatedButton.icon(
                              onPressed: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) => PartnerMatchingScreen(),
                                  ),
                                ).then((_) => _loadData());
                              },
                              icon: Icon(Icons.auto_awesome, color: Colors.white, size: 20),
                              label: Text(
                                'matching'.tr(),
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
                        } else {
                          return Container(
                            height: 44,
                            child: ElevatedButton.icon(
                              onPressed: () {
                                showDialog(
                                  context: context,
                                  builder: (context) => UpgradeDialog(
                                    featureName: 'ai_matching'.tr(),
                                    description: 'ai_matching_description'.tr(),
                                    requiredTier: SubscriptionTier.plus,
                                  ),
                                );
                              },
                              icon: Icon(Icons.lock, color: Colors.white, size: 20),
                              label: Text(
                                'matching'.tr(),
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.orange.withOpacity(0.7),
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                            ),
                          );
                        }
                      },
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Consumer<AccountabilityProvider>(
                      builder: (context, provider, child) {
                        return Container(
                          height: 44,
                          child: ElevatedButton.icon(
                            onPressed: () async {
                              final result = await Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => AccountabilitySetupScreen(
                                    isEdit: true,
                                    existingProfile: provider.profile,
                                  ),
                                ),
                              );
                              
                              if (result == true) {
                                _loadData();
                              }
                            },
                            icon: Icon(
                              Icons.edit,
                              color: Colors.white,
                              size: 18,
                            ),
                            label: Text(
                              'profile'.tr(),
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFF00D4AA),
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
                          Tab(text: 'active_tab'.tr()),
                          Tab(text: 'requests_tab'.tr()),
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
            title: 'no_active_partners'.tr(),
            message: 'start_building_connections'.tr(),
            actionText: 'search_partner'.tr(),
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
            title: 'no_pending_requests'.tr(),
            message: 'requests_appear_here'.tr(),
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
    return Consumer<AccountabilityProvider>(
      builder: (context, provider, child) {
        final isIncomingRequest = provider.isIncomingRequest(partnership);
        
        print('Rendering card for ${partnership.id}: '
              'isPending=$isPending, isIncomingRequest=$isIncomingRequest, '
              'currentUserId=${provider.currentUserId}');

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
                            'check-ins'.tr(),
                            partnership.totalCheckins.toString(),
                            Icons.check_circle_outline,
                          ),
                        ),
                        Expanded(
                          child: _buildStatItem(
                            'success_rate'.tr(),
                            '${partnership.successRate.toStringAsFixed(0)}%',
                            Icons.trending_up,
                          ),
                        ),
                        Expanded(
                          child: _buildStatItem(
                            'frequency'.tr(),
                            partnership.checkinFrequency.displayName,
                            Icons.schedule,
                          ),
                        ),
                      ],
                    ),
                  ],

                  if (isPending) ...[
                    SizedBox(height: 16),
                    
                    // JAVÍTOTT logika: csak bejövő kérelmeknél jelenítjük meg a gombokat
                    if (isIncomingRequest) ...[
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
                                  'reject'.tr(),
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
                                  'accept'.tr(),
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
                    ] else ...[
                      // Kimenő kérelem esetén csak státusz megjelenítése
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.orange.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.schedule, color: Colors.orange, size: 16),
                            SizedBox(width: 8),
                            Text(
                              'waiting_for_response'.tr(),
                              style: TextStyle(
                                color: Colors.orange,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],

                  // Shared goals
                  if (partnership.sharedGoals.isNotEmpty) ...[
                    SizedBox(height: 16),
                    Text(
                      'common_goals_label'.tr(),
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
                            CategoryTranslate.getLocalizedGoal(goal).tr(),
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
                          'additional_goals'.tr(namedArgs: {'count': (partnership.sharedGoals.length - 3).toString()}),
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
      },
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
          content: Text(accept ? 'partnership_accepted'.tr() : 'partnership_declined'.tr()),
          backgroundColor: accept ? Colors.green : Colors.orange,
        ),
      );
      _loadData();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('error_occurred'.tr(namedArgs: {'error': provider.error ?? ''})),
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