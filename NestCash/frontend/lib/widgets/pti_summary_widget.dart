// lib/widgets/pti_summary_widget.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/pti_service.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/screens/pti/pti_main_screen.dart';
import 'package:easy_localization/easy_localization.dart';

class PTISummaryWidget extends StatefulWidget {
  final String userId;
  final String username;

  const PTISummaryWidget({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _PTISummaryWidgetState createState() => _PTISummaryWidgetState();
}

class _PTISummaryWidgetState extends State<PTISummaryWidget> {
  final PTIService _ptiService = PTIService();
  PTIScoreResponse? _ptiScore;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPTIScore();
  }

  Future<void> _loadPTIScore() async {
    try {
      final score = await _ptiService.getPTIScore(period: PTIPeriod.weekly);
      if (score != null) {
        setState(() {
          _ptiScore = score;
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Error loading PTI score: $e');
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
            valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF6C63FF)),
          ),
        ),
      );
    }

    if (_ptiScore == null) {
      return SizedBox.shrink();
    }

    return Container(
      margin: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF6C63FF), Color(0xFF5A52E3)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Color(0xFF6C63FF).withOpacity(0.3),
            blurRadius: 20,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PTIMainScreen(
                userId: widget.userId,
              ),
            ),
          );
        },
        child: Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(
                          Icons.trending_up,
                          color: Colors.white,
                          size: 24,
                        ),
                      ),
                      SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'pti_ranking.pti_short'.tr(),
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'pti_full_name'.tr(),
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.8),
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.white.withOpacity(0.7),
                    size: 16,
                  ),
                ],
              ),
              
              SizedBox(height: 20),
              
              // PTI Score
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    '${_ptiScore!.ptiScore.toStringAsFixed(1)}',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 36,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    ' / 100',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontSize: 16,
                    ),
                  ),
                  Spacer(),
                  if (_ptiScore!.rank != null)
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.emoji_events,
                            color: Colors.white,
                            size: 16,
                          ),
                          SizedBox(width: 4),
                          Text(
                            '${_ptiScore!.rank}.',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
              
              SizedBox(height: 16),
              
              // Progress bar
              Container(
                height: 6,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: _ptiScore!.ptiScore / 100,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                ),
              ),
              
              SizedBox(height: 16),
              
              // Components preview
              Row(
                children: [
                  Expanded(
                    child: _buildMiniComponent(
                      '📚',
                      _ptiScore!.components.learningPoints,
                      'component_learning'.tr(),
                    ),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: _buildMiniComponent(
                      '💪',
                      _ptiScore!.components.habitScore,
                      'component_habits'.tr(),
                    ),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: _buildMiniComponent(
                      '🏆',
                      _ptiScore!.components.badgeScore,
                      'component_badges'.tr(),
                    ),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: _buildMiniComponent(
                      '📊',
                      _ptiScore!.components.limitScore,
                      'component_limits'.tr(),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMiniComponent(String emoji, double score, String label) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(
            emoji,
            style: TextStyle(fontSize: 16),
          ),
          SizedBox(height: 4),
          Text(
            '${score.toStringAsFixed(0)}',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 10,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}