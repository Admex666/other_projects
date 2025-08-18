// lib/screens/admin_dashboard_screen.dart
import 'package:flutter/material.dart';
import '../models/admin_models.dart';
import '../services/analytics_service.dart';
import '../models/user_health.dart';

class AdminDashboardScreen extends StatefulWidget {
  const AdminDashboardScreen({Key? key}) : super(key: key);

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final AnalyticsService _analyticsService = AnalyticsService();
  
  AdminStats? _stats;
  List<AdminUserHealthScore>? _healthScores;
  bool _isLoading = true;
  bool _isRecalculating = false; // Új állapot az újraszámításhoz
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final stats = await _analyticsService.getAdminStats();
      final healthScores = await _analyticsService.getAllHealthScores();

      setState(() {
        _stats = stats;
        _healthScores = healthScores;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  // Új metódus a health score-ok újraszámításához
  Future<void> _recalculateHealthScores() async {
    // Megerősítő dialog
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Health Score-ok újraszámítása'),
        content: const Text(
          'Biztosan újra szeretnéd számítani az összes felhasználó health score-ját? '
          'Ez eltarthat egy ideig és az adatok átmenetileg változhatnak.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Mégse'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.indigo,
              foregroundColor: Colors.white,
            ),
            child: const Text('Újraszámítás'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() {
      _isRecalculating = true;
    });

    try {
      await _analyticsService.recalculateAllHealthScores();
      
      // Sikeres üzenet
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Health score-ok sikeresen újraszámítva!'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
      // Adatok újratöltése
      await _loadData();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba történt az újraszámítás során: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isRecalculating = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        // Újraszámítás gomb az AppBar-ban
        actions: [
          if (!_isLoading) // Csak akkor jelenjen meg, ha nem töltünk
            IconButton(
              onPressed: _isRecalculating ? null : _recalculateHealthScores,
              icon: _isRecalculating 
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Icon(Icons.refresh),
              tooltip: 'Health Score-ok újraszámítása',
            ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.analytics), text: 'Statisztikák'),
            Tab(icon: Icon(Icons.people), text: 'Felhasználók'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? _buildErrorWidget()
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildStatsTab(),
                    _buildUsersTab(),
                  ],
                ),
      // Alternatív: FloatingActionButton az újraszámításhoz
      floatingActionButton: !_isLoading && _errorMessage == null 
          ? FloatingActionButton.extended(
              onPressed: _isRecalculating ? null : _recalculateHealthScores,
              backgroundColor: _isRecalculating ? Colors.grey : Colors.indigo,
              foregroundColor: Colors.white,
              icon: _isRecalculating 
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Icon(Icons.calculate),
              label: Text(_isRecalculating ? 'Számítás...' : 'Újraszámítás'),
            )
          : null,
    );
  }

  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
          const SizedBox(height: 16),
          Text(
            'Hiba történt',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            _errorMessage ?? 'Ismeretlen hiba',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadData,
            child: const Text('Újrapróbálás'),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsTab() {
    if (_stats == null) return const Center(child: Text('Nincsenek adatok'));

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildOverviewCards(),
            const SizedBox(height: 24),
            _buildHealthDistribution(),
            const SizedBox(height: 24),
            _buildAverageScores(),
          ],
        ),
      ),
    );
  }

  // lib/screens/admin_dashboard_screen.dart

  Widget _buildOverviewCards() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                'Összes felhasználó',
                _stats!.totalUsers.toString(),
                Icons.people_outline,
                Colors.blue,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                'Aktív felhasználók\n(7 nap)',
                '${_stats!.activeUsers}',
                Icons.people,
                Colors.green,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                'Onboarding Befejezési Arány',
                '${_stats!.onboardingCompletionRate.toStringAsFixed(1)}%',
                Icons.check_circle_outline,
                Colors.purple,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                'Átlagos TTV',
                '${_stats!.averageTTVMinutes.toStringAsFixed(1)} perc',
                Icons.trending_up,
                Colors.deepOrange,
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Row( // Új sor az inaktív felhasználóknak
          children: [
            Expanded(
              child: _buildStatCard(
                'Inaktív felhasználók aránya\n(30+ nap)',
                '${_stats!.inactiveUserRate.toStringAsFixed(1)}%',
                Icons.person_off_outlined,
                Colors.red,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(child: Container()), // Helykitöltő
          ],
        ),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 24),
              const Spacer(),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHealthDistribution() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Health Score Megoszlás',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          ..._stats!.healthDistribution.entries.map(
            (entry) => _buildHealthDistributionItem(entry.key, entry.value),
          ),
        ],
      ),
    );
  }

  Widget _buildHealthDistributionItem(String level, int count) {
    Color color;
    String displayName;
    
    switch (level) {
      case 'excellent':
        color = Colors.green;
        displayName = 'Kiváló';
        break;
      case 'good':
        color = Colors.lightGreen;
        displayName = 'Jó';
        break;
      case 'fair':
        color = Colors.orange;
        displayName = 'Közepes';
        break;
      case 'poor':
        color = Colors.red;
        displayName = 'Gyenge';
        break;
      default:
        color = Colors.grey;
        displayName = level;
    }

    final total = _stats!.healthDistribution.values.fold(0, (sum, val) => sum + val);
    final percentage = total > 0 ? (count / total * 100) : 0.0;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(displayName, style: const TextStyle(fontWeight: FontWeight.w500)),
          const Spacer(),
          Text('$count (${percentage.toStringAsFixed(1)}%)'),
        ],
      ),
    );
  }

  Widget _buildAverageScores() {
    final scores = _stats!.averageScores;
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Átlag Score-ok',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          _buildScoreItem('Összes', scores.overall, 0.3, Colors.indigo),
          const SizedBox(height: 8),
          _buildScoreItem('Bejelentkezés', scores.loginFrequency, 0.3, Colors.blue),
          const SizedBox(height: 8),
          _buildScoreItem('Funkciók', scores.featureUsage, 0.4, Colors.purple),
          const SizedBox(height: 8),
          _buildScoreItem('Közösség', scores.engagement, 0.3, Colors.green),
        ],
      ),
    );
  }

  Widget _buildScoreItem(String name, double score, double weight, Color color) {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: Text(name, style: const TextStyle(fontWeight: FontWeight.w500)),
        ),
        Expanded(
          flex: 3,
          child: LinearProgressIndicator(
            value: score / 100,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '${score.toStringAsFixed(1)}%',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ],
    );
  }

  Widget _buildUsersTab() {
    if (_healthScores == null) return const Center(child: Text('Nincsenek adatok'));

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _healthScores!.length,
        itemBuilder: (context, index) {
          final user = _healthScores![index];
          return _buildUserCard(user);
        },
      ),
    );
  }

  Widget _buildUserCard(AdminUserHealthScore user) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: ExpansionTile(
        title: Text(
          user.username,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(user.email),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: _getHealthColor(user.healthLevel),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            '${user.overallScoreInt}%',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(child: _buildMiniScoreCard('Bejelentkezés', user.loginFrequencyScore, Colors.blue)),
                    const SizedBox(width: 8),
                    Expanded(child: _buildMiniScoreCard('Funkciók', user.featureUsageScore, Colors.purple)),
                    const SizedBox(width: 8),
                    Expanded(child: _buildMiniScoreCard('Közösség', user.engagementScore, Colors.green)),
                  ],
                ),
                const SizedBox(height: 16),
                _buildUserDetails(user.details),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniScoreCard(String title, double score, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            '${score.round()}%',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: color,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            title,
            style: const TextStyle(fontSize: 12),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildUserDetails(AdminHealthDetails details) {
    return Column(
      children: [
        _buildDetailRow('Utolsó bejelentkezés', '${details.daysSinceLastLogin} napja'),
        _buildDetailRow('Összes session', details.totalSessions.toString()),
        _buildDetailRow('Tranzakciók', details.transactionCount.toString()),
        _buildDetailRow('Onboarding', details.onboardingCompleted ? 'Befejezve' : 'Függőben'),
        _buildDetailRow('Badge-ek', details.badgeProgressCount.toString()),
        _buildDetailRow('Forum bejegyzések', details.forumPostsCount.toString()),
        _buildDetailRow('Forum hozzászólások', details.forumCommentsCount.toString()),
        _buildDetailRow('Aktív partnership', details.hasActivePartnership ? 'Igen' : 'Nem'),
        _buildDetailRow('Tudástár aktivitás', details.knowledgeActivityCount?.toString() ?? '0'),
        _buildDetailRow('Teljesített leckék', details.knowledgeLessonsCompleted?.toString() ?? '0'),
        _buildDetailRow('Üzenet aktivitás', details.messagesActivityCount?.toString() ?? '0'),
        _buildDetailRow('Elküldött üzenetek', details.messagesSentCount?.toString() ?? '0'),
        _buildDetailRow('Szokások használat', details.habitsActivityCount?.toString() ?? '0'),
        _buildDetailRow('Korlátok használat', details.limitsActivityCount?.toString() ?? '0'),
        _buildDetailRow('PTI használat', details.ptiActivityCount?.toString() ?? '0'),
        _buildDetailRow('Badge használat', details.badgeActivityCount?.toString() ?? '0'),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(
              label,
              style: TextStyle(color: Colors.grey[600]),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  Color _getHealthColor(String healthLevel) {
    switch (healthLevel) {
      case 'excellent':
        return Colors.green;
      case 'good':
        return Colors.lightGreen;
      case 'fair':
        return Colors.orange;
      case 'poor':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}