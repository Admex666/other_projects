// lib/screens/challenges/my_challenges_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/models/challenge.dart';
import 'package:frontend/services/challenge_service.dart';
import 'package:frontend/screens/challenges/challenge_detail_screen.dart';

class MyChallengesScreen extends StatefulWidget {
  final String userId;

  const MyChallengesScreen({
    Key? key,
    required this.userId,
  }) : super(key: key);

  @override
  _MyChallengesScreenState createState() => _MyChallengesScreenState();
}

class _MyChallengesScreenState extends State<MyChallengesScreen> {
  final ChallengeService _challengeService = ChallengeService();
  List<UserChallenge> _userChallenges = [];
  bool _isLoading = true;
  String _error = '';

  ParticipationStatus? _selectedStatus;
  ChallengeType? _selectedType;

  @override
  void initState() {
    super.initState();
    _loadMyChallenges();
  }

  Future<void> _loadMyChallenges() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      final challenges = await _challengeService.getMyParticipations(
        status: _selectedStatus,
        challengeType: _selectedType,
      );

      setState(() {
        _userChallenges = challenges;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _showFilterBottomSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.8,
        minChildSize: 0.4,
        builder: (context, scrollController) => Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
            ),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: const BoxDecoration(
                  color: Color(0xFF00D4A3),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                  ),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.filter_list, color: Colors.white, size: 28),
                    const SizedBox(width: 16),
                    const Expanded(
                      child: Text(
                        'Szűrők',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close, color: Colors.white),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Státusz szűrő
                      const Text(
                        'Státusz',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2D3748),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildFilterChip(
                            'Összes',
                            _selectedStatus == null,
                            () {
                              setState(() => _selectedStatus = null);
                              Navigator.pop(context);
                              _loadMyChallenges();
                            },
                          ),
                          ...ParticipationStatus.values.map((status) => _buildFilterChip(
                            status.displayName,
                            _selectedStatus == status,
                            () {
                              setState(() => _selectedStatus = _selectedStatus == status ? null : status);
                              Navigator.pop(context);
                              _loadMyChallenges();
                            },
                          )),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Típus szűrő
                      const Text(
                        'Típus',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF2D3748),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildFilterChip(
                            'Összes',
                            _selectedType == null,
                            () {
                              setState(() => _selectedType = null);
                              Navigator.pop(context);
                              _loadMyChallenges();
                            },
                          ),
                          ...ChallengeType.values.map((type) => _buildFilterChip(
                            type.displayName,
                            _selectedType == type,
                            () {
                              setState(() => _selectedType = _selectedType == type ? null : type);
                              Navigator.pop(context);
                              _loadMyChallenges();
                            },
                          )),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00D4A3) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF00D4A3) : Colors.grey[300]!,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.grey[700],
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header - KnowledgeScreen stílusú
        Container(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.grey.withOpacity(0.1),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Saját kihívásaim',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2D3748),
                ),
              ),
              GestureDetector(
                onTap: _showFilterBottomSheet,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00D4A3),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.filter_list,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
              ),
            ],
          ),
        ),

        // Lista tartalom
        Expanded(
          child: _buildContent(),
        ),
      ],
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error.isNotEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(_error, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadMyChallenges,
              child: const Text('Újrapróbálás'),
            ),
          ],
        ),
      );
    }

    if (_userChallenges.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assignment_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'Még nincs kihívásod',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 8),
            Text(
              'Csatlakozz kihívásokhoz a Felfedezés tabon!',
              style: TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadMyChallenges,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        itemCount: _userChallenges.length,
        itemBuilder: (context, index) {
          final userChallenge = _userChallenges[index];
          return _buildUserChallengeCard(userChallenge);
        },
      ),
    );
  }

  Widget _buildUserChallengeCard(UserChallenge userChallenge) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ChallengeDetailScreen(
              challengeId: userChallenge.challengeId,
              userId: widget.userId,
            ),
          ),
        ).then((_) => _loadMyChallenges()),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: _getTypeColor(userChallenge.challengeType),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      userChallenge.challengeType.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: _getStatusColor(userChallenge.status),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      userChallenge.status.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: _getDifficultyColor(userChallenge.challengeDifficulty),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      userChallenge.challengeDifficulty.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Cím
              Text(
                userChallenge.challengeTitle,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF2D3748),
                ),
              ),
              const SizedBox(height: 12),

              // Haladás
              Text(
                'Haladás',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[700],
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: LinearProgressIndicator(
                      value: userChallenge.progress.percentage / 100,
                      backgroundColor: Colors.grey[200],
                      valueColor: AlwaysStoppedAnimation<Color>(
                        userChallenge.progress.percentage >= 100
                            ? Colors.green
                            : _getStatusColor(userChallenge.status),
                      ),
                      minHeight: 8,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '${userChallenge.progress.percentage.toStringAsFixed(1)}%',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: Color(0xFF2D3748),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  '${_formatAmount(userChallenge.progress.currentValue)} / ${_formatAmount(userChallenge.progress.targetValue)} ${userChallenge.progress.unit}',
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
              ),
              const SizedBox(height: 16),

              // Statisztikák és időpontok
              _buildInfoRow(
                Icons.calendar_month,
                'Csatlakozás: ${_formatDate(userChallenge.joinedAt)}',
                Colors.grey[600]!,
              ),
              if (userChallenge.earnedPoints > 0)
                _buildInfoRow(
                  Icons.star,
                  '${userChallenge.earnedPoints} pont',
                  Colors.amber,
                ),

              // Befejezés dátuma (ha van)
              if (userChallenge.completedAt != null)
                _buildInfoRow(
                  Icons.check_circle,
                  'Befejezve: ${_formatDate(userChallenge.completedAt!)}',
                  Colors.green,
                ),

              // Streak információ (ha aktív)
              if (userChallenge.status == ParticipationStatus.active &&
                  userChallenge.currentStreak > 0)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Row(
                    children: [
                      Icon(Icons.local_fire_department, size: 18, color: Colors.orange),
                      const SizedBox(width: 6),
                      Text(
                        'Jelenlegi sorozat: ${userChallenge.currentStreak} nap',
                        style: TextStyle(color: Colors.grey[700], fontSize: 13),
                      ),
                      if (userChallenge.bestStreak > userChallenge.currentStreak) ...[
                        const SizedBox(width: 16),
                        Text(
                          'Legjobb: ${userChallenge.bestStreak} nap',
                          style: TextStyle(color: Colors.grey[700], fontSize: 13),
                        ),
                      ],
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String text, Color color) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(width: 6),
          Text(
            text,
            style: TextStyle(color: Colors.grey[700], fontSize: 13),
          ),
        ],
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
      case ChallengeDifficulty.easy: return const Color(0xFF00D4A3);
      case ChallengeDifficulty.medium: return Colors.orange;
      case ChallengeDifficulty.hard: return Colors.red;
      case ChallengeDifficulty.expert: return Colors.purple;
    }
  }

  Color _getStatusColor(ParticipationStatus status) {
    switch (status) {
      case ParticipationStatus.active: return const Color(0xFF00D4A3);
      case ParticipationStatus.completed: return Colors.green;
      case ParticipationStatus.failed: return Colors.red;
      case ParticipationStatus.abandoned: return Colors.grey;
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

  String _formatDate(DateTime date) {
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}.';
  }
}