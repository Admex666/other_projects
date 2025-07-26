// lib/screens/challenges/challenge_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/models/challenge.dart';
import 'package:frontend/services/challenge_service.dart';

class ChallengeDetailScreen extends StatefulWidget {
  final String challengeId;
  final String userId;

  const ChallengeDetailScreen({
    Key? key,
    required this.challengeId,
    required this.userId,
  }) : super(key: key);

  @override
  _ChallengeDetailScreenState createState() => _ChallengeDetailScreenState();
}

class _ChallengeDetailScreenState extends State<ChallengeDetailScreen> {
  final ChallengeService _challengeService = ChallengeService();
  Challenge? _challenge;
  bool _isLoading = true;
  bool _isJoining = false;
  String _error = '';

  final TextEditingController _personalTargetController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadChallenge();
  }

  @override
  void dispose() {
    _personalTargetController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _loadChallenge() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      final challenge = await _challengeService.getChallenge(widget.challengeId);
      setState(() {
        _challenge = challenge;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _joinChallenge() async {
    if (_challenge == null) return;

    setState(() => _isJoining = true);

    try {
      double? personalTarget;
      if (_personalTargetController.text.isNotEmpty) {
        personalTarget = double.tryParse(_personalTargetController.text);
      }

      await _challengeService.joinChallenge(
        widget.challengeId,
        personalTarget: personalTarget,
        notes: _notesController.text.isEmpty ? null : _notesController.text,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Sikeresen csatlakoztál a kihíváshoz!'),
            backgroundColor: Colors.green,
          ),
        );
        _loadChallenge(); // Frissítjük az adatokat
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isJoining = false);
    }
  }

  Future<void> _leaveChallenge() async {
    if (_challenge == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        title: const Text('Kihívás elhagyása'),
        content: const Text('Biztosan el szeretnéd hagyni ezt a kihívást?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Mégse'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Igen', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isJoining = true);

    try {
      await _challengeService.leaveChallenge(widget.challengeId);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Sikeresen elhagytad a kihívást'),
            backgroundColor: Colors.orange,
          ),
        );
        _loadChallenge(); // Frissítjük az adatokat
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isJoining = false);
    }
  }

  Future<void> _updateProgress() async {
    if (_challenge == null || !_challenge!.isParticipating) return;

    try {
      await _challengeService.updateChallengeProgress(widget.challengeId);
      await _loadChallenge(); // Frissítjük az adatokat
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Haladás frissítve!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba a frissítés során: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _showJoinDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        title: const Text('Csatlakozás a kihíváshoz'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_challenge?.targetAmount != null)
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TextField(
                  controller: _personalTargetController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'Személyes cél (opcionális)',
                    hintText: 'Alapértelmezett: ${_formatAmount(_challenge!.targetAmount!)} HUF',
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.all(16),
                  ),
                ),
              ),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFFF5F5F5),
                borderRadius: BorderRadius.circular(12),
              ),
              child: TextField(
                controller: _notesController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Jegyzet (opcionális)',
                  hintText: 'Miért szeretnél csatlakozni?',
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.all(16),
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Mégse'),
          ),
          ElevatedButton(
            onPressed: _isJoining ? null : () {
              Navigator.pop(context);
              _joinChallenge();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00D4A3),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: _isJoining 
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Text('Csatlakozás'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat, // Ezt a sort add hozzá
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00D4A3)))
          : _error.isNotEmpty
              ? _buildErrorState()
              : _challenge == null
                  ? const Center(child: Text('Kihívás nem található'))
                  : RefreshIndicator(
                      onRefresh: _loadChallenge,
                      color: const Color(0xFF00D4A3),
                      child: SingleChildScrollView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 100), // Extra bottom padding for floating button
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Header - Back button és cím
                            SafeArea(
                              bottom: false,
                              child: Row(
                                children: [
                                  GestureDetector(
                                    onTap: () => Navigator.pop(context),
                                    child: Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF00D4A3).withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: const Icon(
                                        Icons.arrow_back_ios,
                                        color: Color(0xFF00D4A3),
                                        size: 20,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  const Expanded(
                                    child: Text(
                                      'Kihívás részletei',
                                      style: TextStyle(
                                        fontSize: 24,
                                        fontWeight: FontWeight.bold,
                                        color: Color(0xFF2D3748),
                                      ),
                                    ),
                                  ),
                                  if (_challenge?.isParticipating == true)
                                    GestureDetector(
                                      onTap: _updateProgress,
                                      child: Container(
                                        padding: const EdgeInsets.all(8),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF00D4A3).withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: const Icon(
                                          Icons.refresh,
                                          color: Color(0xFF00D4A3),
                                          size: 20,
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 24),

                            _buildChallengeDetails(),
                          ],
                        ),
                      ),
                    ),
      floatingActionButton: _challenge != null && !_isLoading && _error.isEmpty
          ? _buildFloatingActionButton()
          : null,
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SafeArea(
              bottom: false,
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00D4A3).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(
                        Icons.arrow_back_ios,
                        color: Color(0xFF00D4A3),
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Expanded(
                    child: Text(
                      'Kihívás részletei',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF2D3748),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 40),
            const Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(_error, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadChallenge,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00D4A3),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Újrapróbálás'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChallengeDetails() {
    final challenge = _challenge!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header chips
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getTypeColor(challenge.challengeType),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                challenge.challengeType.displayName,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _getDifficultyColor(challenge.difficulty),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                challenge.difficulty.displayName,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Cím
        Text(
          challenge.title,
          style: const TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: Color(0xFF2D3748),
          ),
        ),
        const SizedBox(height: 12),

        // Leírás
        Text(
          challenge.description,
          style: const TextStyle(fontSize: 16, height: 1.5, color: Colors.grey),
        ),
        const SizedBox(height: 20),

        // Haladás (ha részt vesz)
        if (challenge.isParticipating && challenge.myProgress != null)
          _buildProgressSection(challenge.myProgress!),

        // Alapadatok
        _buildInfoSection(challenge),

        // Szabályok
        if (challenge.rules.isNotEmpty)
          _buildRulesSection(challenge.rules),

        // Jutalmak
        _buildRewardsSection(challenge.rewards),

        // Statisztikák
        _buildStatsSection(challenge),
      ],
    );
  }

  Widget _buildProgressSection(ChallengeProgress progress) {
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Haladásod',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2D3748),
                ),
              ),
              Text(
                '${progress.percentage.toStringAsFixed(1)}%',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF00D4A3),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: progress.percentage / 100,
            backgroundColor: Colors.grey[200],
            valueColor: AlwaysStoppedAnimation<Color>(
              progress.percentage >= 100 ? Colors.green : const Color(0xFF00D4A3),
            ),
            minHeight: 8,
          ),
          const SizedBox(height: 8),
          Text(
            '${_formatAmount(progress.currentValue)} / ${_formatAmount(progress.targetValue)} ${progress.unit}',
            style: TextStyle(color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoSection(Challenge challenge) {
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Alapadatok',
            style: TextStyle(
              fontSize: 18, 
              fontWeight: FontWeight.bold,
              color: Color(0xFF2D3748),
            ),
          ),
          const SizedBox(height: 12),
          _buildInfoRow(Icons.timer, 'Időtartam', '${challenge.durationDays} nap'),
          if (challenge.targetAmount != null)
            _buildInfoRow(Icons.attach_money, 'Cél összeg', 
                '${_formatAmount(challenge.targetAmount!)} HUF'),
          _buildInfoRow(Icons.people, 'Résztvevők', '${challenge.participantCount} fő'),
          _buildInfoRow(Icons.trending_up, 'Befejezési arány', 
              '${challenge.completionRate.toStringAsFixed(1)}%'),
          if (challenge.creatorUsername != null)
            _buildInfoRow(Icons.person, 'Létrehozó', challenge.creatorUsername!),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey[600]),
          const SizedBox(width: 12),
          Text(
            '$label:',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: TextStyle(color: Colors.grey[700]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRulesSection(List<ChallengeRule> rules) {
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Szabályok',
            style: TextStyle(
              fontSize: 18, 
              fontWeight: FontWeight.bold,
              color: Color(0xFF2D3748),
            ),
          ),
          const SizedBox(height: 12),
          ...rules.map((rule) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.check_circle_outline, 
                    size: 16, color: Color(0xFF00D4A3)),
                const SizedBox(width: 8),
                Expanded(child: Text(rule.description)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildRewardsSection(ChallengeReward rewards) {
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Jutalmak',
            style: TextStyle(
              fontSize: 18, 
              fontWeight: FontWeight.bold,
              color: Color(0xFF2D3748),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Icon(Icons.star, color: Colors.amber),
              const SizedBox(width: 8),
              Text('${rewards.points} pont'),
            ],
          ),
          if (rewards.badges.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.military_tech, color: Colors.blue),
                const SizedBox(width: 8),
                Expanded(
                  child: Text('Kitűzők: ${rewards.badges.join(', ')}'),
                ),
              ],
            ),
          ],
          if (rewards.title != null) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.title, color: Colors.purple),
                const SizedBox(width: 8),
                Expanded(child: Text('Cím: ${rewards.title}')),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatsSection(Challenge challenge) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Statisztikák',
            style: TextStyle(
              fontSize: 18, 
              fontWeight: FontWeight.bold,
              color: Color(0xFF2D3748),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStatItem('Résztvevő', '${challenge.participantCount}'),
              _buildStatItem('Befejezés', '${challenge.completionRate.toInt()}%'),
              _buildStatItem('Napok', '${challenge.durationDays}'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF00D4A3),
          ),
        ),
        Text(
          label,
          style: TextStyle(color: Colors.grey[600]),
        ),
      ],
    );
  }

  Widget _buildFloatingActionButton() {
    final challenge = _challenge!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: challenge.isParticipating
          ? Row(
              children: [
                Expanded(
                  child: FloatingActionButton.extended(
                    onPressed: _isJoining ? null : _leaveChallenge,
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                    heroTag: "leave",
                    label: _isJoining
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Elhagyás'),
                    icon: _isJoining ? null : const Icon(Icons.exit_to_app),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FloatingActionButton.extended(
                    onPressed: _updateProgress,
                    backgroundColor: const Color(0xFF00D4A3),
                    foregroundColor: Colors.white,
                    heroTag: "update",
                    label: const Text('Frissítés'),
                    icon: const Icon(Icons.refresh),
                  ),
                ),
              ],
            )
          : FloatingActionButton.extended(
              onPressed: _isJoining ? null : _showJoinDialog,
              backgroundColor: const Color(0xFF00D4A3),
              foregroundColor: Colors.white,
              heroTag: "join",
              label: _isJoining
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text(
                      'Csatlakozás a kihíváshoz',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
              icon: _isJoining ? null : const Icon(Icons.add),
            ),
    );
  }

  Color _getTypeColor(ChallengeType type) {
    switch (type) {
      case ChallengeType.savings: return Colors.green;
      case ChallengeType.expenseReduction: return Colors.red;
      case ChallengeType.habitStreak: return Colors.purple;
      case ChallengeType.budgetControl: return Colors.blue;
      case ChallengeType.investment: return Colors.orange;
      case ChallengeType.incomeBoost: return Colors.teal;
    }
  }

  Color _getDifficultyColor(ChallengeDifficulty difficulty) {
    switch (difficulty) {
      case ChallengeDifficulty.easy: return Colors.green;
      case ChallengeDifficulty.medium: return Colors.orange;
      case ChallengeDifficulty.hard: return Colors.red;
      case ChallengeDifficulty.expert: return Colors.purple;
    }
  }

  String _formatAmount(double amount) {
    if (amount >= 1000000) {
      return '${(amount / 1000000).toStringAsFixed(1)}M';
    } else if (amount >= 1000) {
      return '${(amount / 1000).toStringAsFixed(0)}k';
    } else {
      return amount.toStringAsFixed(0);
    }
  }
}