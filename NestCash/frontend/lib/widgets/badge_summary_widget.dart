// lib/widgets/badge_summary_widget.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/badge_service.dart';
import 'package:frontend/models/badge_models.dart';
import 'package:frontend/screens/profile/badges_screen.dart';

class BadgeSummaryWidget extends StatefulWidget {
  final String userId;
  final String username;

  const BadgeSummaryWidget({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _BadgeSummaryWidgetState createState() => _BadgeSummaryWidgetState();
}

class _BadgeSummaryWidgetState extends State<BadgeSummaryWidget> {
  final BadgeService _badgeService = BadgeService();
  BadgeStats? _badgeStats;
  List<UserBadge> _recentBadges = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadBadgeStats();
  }

  Future<void> _loadBadgeStats() async {
    try {
      final statsResponse = await _badgeService.getBadgeStats();
      if (statsResponse != null) {
        setState(() {
          _badgeStats = BadgeStats.fromJson(statsResponse);
          _recentBadges = _badgeStats!.recentBadges.take(3).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Error loading badge stats: $e');
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Container(
        margin: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
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
        child: Center(
          child: CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4AA)),
          ),
        ),
      );
    }

    if (_badgeStats == null) {
      return SizedBox.shrink();
    }

    return Container(
      margin: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
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
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => BadgesScreen(
                userId: widget.userId,
                username: widget.username,
              ),
            ),
          );
        },
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.emoji_events,
                        color: Colors.amber[600],
                        size: 24,
                      ),
                      SizedBox(width: 8),
                      Text(
                        'Kitűzők',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.grey[400],
                    size: 16,
                  ),
                ],
              ),
              
              SizedBox(height: 16),
              
              // Statisztikák
              Row(
                children: [
                  Expanded(
                    child: _buildStatItem(
                      'Összes',
                      _badgeStats!.totalBadges.toString(),
                      Icons.emoji_events,
                      Colors.orange,
                    ),
                  ),
                  Expanded(
                    child: _buildStatItem(
                      'Pontok',
                      _badgeStats!.totalPoints.toString(),
                      Icons.stars,
                      Colors.blue,
                    ),
                  ),
                  Expanded(
                    child: _buildStatItem(
                      'Haladás',
                      _badgeStats!.inProgressCount.toString(),
                      Icons.trending_up,
                      Colors.green,
                    ),
                  ),
                ],
              ),
              
              // Legutóbbi badge-ek
              if (_recentBadges.isNotEmpty) ...[
                SizedBox(height: 16),
                Text(
                  'Legutóbbi kitűzők',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Colors.grey[700],
                  ),
                ),
                SizedBox(height: 8),
                Row(
                  children: _recentBadges.map((badge) {
                    return Expanded(
                      child: Container(
                        margin: EdgeInsets.only(right: 8),
                        padding: EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          children: [
                            Text(
                              badge.badgeIcon ?? '🏆',
                              style: TextStyle(fontSize: 20),
                            ),
                            SizedBox(height: 4),
                            Text(
                              badge.badgeName ?? badge.badgeCode,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w500,
                              ),
                              textAlign: TextAlign.center,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }
}