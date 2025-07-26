// lib/screens/habits/habit_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/models/habit.dart';
import 'package:frontend/services/habit_service.dart';
import 'package:intl/intl.dart';

class HabitDetailScreen extends StatefulWidget {
  final String habitId;
  final String userId;

  const HabitDetailScreen({
    Key? key,
    required this.habitId,
    required this.userId,
  }) : super(key: key);

  @override
  _HabitDetailScreenState createState() => _HabitDetailScreenState();
}

class _HabitDetailScreenState extends State<HabitDetailScreen>
    with TickerProviderStateMixin {
  final HabitService _habitService = HabitService();
  
  Habit? _habit;
  HabitStats? _stats;
  List<HabitLog> _recentLogs = [];
  bool _isLoading = true;
  String _error = '';
  
  late TabController _tabController;
  final _valueController = TextEditingController();
  final _notesController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _valueController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      final results = await Future.wait([
        _habitService.getHabit(widget.habitId),
        _habitService.getHabitStats(widget.habitId),
        _habitService.getHabitLogs(widget.habitId, limit: 30),
      ]);

      setState(() {
        _habit = results[0] as Habit;
        _stats = results[1] as HabitStats;
        _recentLogs = results[2] as List<HabitLog>;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _logHabit() async {
    if (_habit == null) return;

    final today = DateFormat('yyyy-MM-dd').format(DateTime.now());
    final existingLog = _recentLogs.firstWhere(
      (log) => log.date == today,
      orElse: () => HabitLog(
        id: '',
        userId: widget.userId,
        habitId: widget.habitId,
        date: today,
        completed: false,
        createdAt: DateTime.now(),
      ),
    );

    await _showLogDialog(existingLog);
  }

  Future<void> _showLogDialog(HabitLog? existingLog) async {
    if (_habit == null) return;

    final isEditing = existingLog?.id.isNotEmpty ?? false;
    bool completed = existingLog?.completed ?? false;
    
    if (_habit!.trackingType == TrackingType.numeric) {
      _valueController.text = existingLog?.value?.toString() ?? '';
    }
    _notesController.text = existingLog?.notes ?? '';

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          title: Text(
            isEditing ? 'Szokás szerkesztése' : 'Szokás rögzítése',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Completion switch
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey[50],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Icon(Icons.check_circle, color: Colors.grey[600]),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Teljesítve',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    Switch(
                      value: completed,
                      onChanged: (value) {
                        setDialogState(() {
                          completed = value;
                        });
                      },
                      activeColor: Color(0xFF00D4AA),
                    ),
                  ],
                ),
              ),
              
              // Value field for numeric habits
              if (_habit!.trackingType == TrackingType.numeric) ...[
                const SizedBox(height: 16),
                TextFormField(
                  controller: _valueController,
                  decoration: InputDecoration(
                    labelText: 'Érték',
                    hintText: 'Adj meg egy értéket',
                    prefixIcon: Icon(Icons.numbers),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: Color(0xFF00D4AA), width: 2),
                    ),
                  ),
                  keyboardType: TextInputType.number,
                ),
              ],
              
              // Notes field
              const SizedBox(height: 16),
              TextFormField(
                controller: _notesController,
                decoration: InputDecoration(
                  labelText: 'Jegyzetek (opcionális)',
                  hintText: 'Írj egy rövid megjegyzést...',
                  prefixIcon: Icon(Icons.note),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: Color(0xFF00D4AA), width: 2),
                  ),
                ),
                maxLines: 3,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text('Mégse'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4AA),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              child: Text(isEditing ? 'Frissítés' : 'Rögzítés'),
            ),
          ],
        ),
      ),
    );

    if (result == true) {
      try {
        if (isEditing && existingLog != null) {
          await _habitService.updateHabitLog(
            widget.habitId,
            existingLog.id,
            {
              'completed': completed,
              if (_habit!.trackingType == TrackingType.numeric)
                'value': double.tryParse(_valueController.text),
              'notes': _notesController.text.isEmpty ? null : _notesController.text,
            },
          );
        } else {
          await _habitService.logHabitCompletion(
            widget.habitId,
            completed: completed,
            value: _habit!.trackingType == TrackingType.numeric 
                ? double.tryParse(_valueController.text)
                : null,
            notes: _notesController.text.isEmpty ? null : _notesController.text,
          );
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(isEditing ? 'Szokás frissítve!' : 'Szokás rögzítve!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );

        _loadData();
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
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
                      icon: Icon(
                        Icons.arrow_back,
                        color: Colors.black87,
                        size: 24,
                      ),
                    ),
                    Expanded(
                      child: Text(
                        'Betöltés...',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    SizedBox(width: 48),
                  ],
                ),
              ),
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
                  child: Center(
                    child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (_error.isNotEmpty || _habit == null) {
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
                      icon: Icon(
                        Icons.arrow_back,
                        color: Colors.black87,
                        size: 24,
                      ),
                    ),
                    Expanded(
                      child: Text(
                        'Hiba',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    SizedBox(width: 48),
                  ],
                ),
              ),
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
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.error_outline, size: 64, color: Colors.grey[400]),
                          const SizedBox(height: 16),
                          Text(
                            'Nem sikerült betölteni a szokást',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                              color: Colors.grey[600],
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _error,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[500],
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton(
                            onPressed: _loadData,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFF00D4AA),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                            child: Text('Újrapróbálás'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

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
                    icon: Icon(
                      Icons.arrow_back,
                      color: Colors.black87,
                      size: 24,
                    ),
                  ),
                  Expanded(
                    child: Text(
                      _habit!.title,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) async {
                      switch (value) {
                        case 'edit':
                          _showEditDialog();
                          break;
                        case 'archive':
                          _toggleArchive();
                          break;
                        case 'delete':
                          _showDeleteConfirmation();
                          break;
                      }
                    },
                    icon: Icon(Icons.more_vert, color: Colors.black87),
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        value: 'edit',
                        child: Row(
                          children: [
                            Icon(Icons.edit, size: 20),
                            SizedBox(width: 8),
                            Text('Szerkesztés'),
                          ],
                        ),
                      ),
                      PopupMenuItem(
                        value: 'archive',
                        child: Row(
                          children: [
                            Icon(_habit!.isActive ? Icons.archive : Icons.unarchive, size: 20),
                            SizedBox(width: 8),
                            Text(_habit!.isActive ? 'Archiválás' : 'Visszaállítás'),
                          ],
                        ),
                      ),
                      PopupMenuItem(
                        value: 'delete',
                        child: Row(
                          children: [
                            Icon(Icons.delete, size: 20, color: Colors.red),
                            SizedBox(width: 8),
                            Text('Törlés', style: TextStyle(color: Colors.red)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            
            // Tab Bar
            Container(
              margin: EdgeInsets.symmetric(horizontal: 20),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.1),
                borderRadius: BorderRadius.circular(25),
              ),
              child: TabBar(
                controller: _tabController,
                indicator: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(25),
                ),
                labelColor: Colors.black87,
                unselectedLabelColor: Colors.black54,
                tabs: const [
                  Tab(text: 'Áttekintés'),
                  Tab(text: 'Statisztikák'),
                  Tab(text: 'Előzmények'),
                ],
              ),
            ),
            
            SizedBox(height: 20),
            
            // Content Container
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
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildOverviewTab(),
                    _buildStatsTab(),
                    _buildHistoryTab(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _logHabit,
        backgroundColor: Colors.orange,
        child: Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildOverviewTab() {
    final isCompletedToday = _habit!.isCompletedToday ?? false;
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(height: 10),
          
          // Status card
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(15),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isCompletedToday 
                        ? Color(0xFF00D4AA) 
                        : Colors.grey[200],
                  ),
                  child: Icon(
                    isCompletedToday ? Icons.check : Icons.circle_outlined,
                    color: isCompletedToday ? Colors.white : Colors.grey[400],
                    size: 30,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isCompletedToday ? 'Ma teljesítve!' : 'Még nem teljesítve ma',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: isCompletedToday 
                              ? Color(0xFF00D4AA) 
                              : Colors.grey[600],
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Jelenlegi sorozat: ${_habit!.streakCount} nap',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Habit info
          _buildInfoSection('Részletek', [
            _buildInfoRow('Kategória', _habit!.category.value),
            _buildInfoRow('Típus', _getTrackingTypeLabel(_habit!.trackingType)),
            _buildInfoRow('Gyakoriság', _habit!.frequency.displayName),
            if (_habit!.description != null)
              _buildInfoRow('Leírás', _habit!.description!),
          ]),
          
          const SizedBox(height: 16),
          
          // Goal info
          if (_habit!.hasGoal) ...[
            _buildInfoSection('Cél', [
              _buildInfoRow('Cél érték', '${_habit!.targetValue}'),
              _buildInfoRow('Cél időszaka', _habit!.goalPeriod!.displayName),
              if (_habit!.dailyTarget != null)
                _buildInfoRow('Napi cél', _habit!.dailyTarget!.toStringAsFixed(1)),
              if (_habit!.usagePercentage != null)
                _buildProgressRow('Haladás', _habit!.usagePercentage!),
            ]),
            const SizedBox(height: 16),
          ],
          
          // Streak info
          _buildInfoSection('Teljesítmény', [
            _buildInfoRow('Jelenlegi sorozat', '${_habit!.streakCount} nap'),
            _buildInfoRow('Legjobb sorozat', '${_habit!.bestStreak} nap'),
            if (_habit!.lastCompleted != null)
              _buildInfoRow('Utoljára teljesítve', _formatDate(_habit!.lastCompleted!)),
          ]),
          
          SizedBox(height: 100), // Extra space for FAB
        ],
      ),
    );
  }

  Widget _buildStatsTab() {
    if (_stats == null) {
      return Center(
        child: CircularProgressIndicator(color: Color(0xFF00D4AA)),
      );
    }

    final overall = _stats!.overall;
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(height: 10),
          
          // Overall stats
          _buildStatsCard('Összesített statisztika', [
            _buildStatRow('Összes nap', overall.totalDays.toString()),
            _buildStatRow('Teljesített napok', overall.completedDays.toString()),
            _buildStatRow('Teljesítési arány', '${overall.completionRate.toStringAsFixed(1)}%'),
            if (overall.averageValue != null)
              _buildStatRow('Átlagérték', overall.averageValue!.toStringAsFixed(2)),
          ]),
          
          const SizedBox(height: 16),
          
          // Monthly progress
          if (_stats!.monthlyStats.isNotEmpty) ...[
            _buildStatsCard('Havi bontás', 
              _stats!.monthlyStats.map((monthly) => 
                _buildStatRow(
                  _formatMonth(monthly.month),
                  '${monthly.completedDays}/${monthly.totalDays} (${monthly.completionRate.toStringAsFixed(1)}%)',
                ),
              ).toList(),
            ),
          ],
          
          SizedBox(height: 100), // Extra space for FAB
        ],
      ),
    );
  }

  Widget _buildHistoryTab() {
    if (_recentLogs.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.history, size: 64, color: Colors.grey[400]),
              const SizedBox(height: 16),
              Text(
                'Még nincsenek bejegyzések',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Kezdj el rögzíteni a szokásaidat!',
                style: TextStyle(
                  color: Colors.grey[500],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(24),
      itemCount: _recentLogs.length,
      itemBuilder: (context, index) {
        final log = _recentLogs[index];
        return _buildLogCard(log);
      },
    );
  }

  Widget _buildLogCard(HabitLog log) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: EdgeInsets.all(16),
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: log.completed 
                ? Color(0xFF00D4AA) 
                : Colors.grey[200],
          ),
          child: Icon(
            log.completed ? Icons.check : Icons.close,
            color: log.completed ? Colors.white : Colors.grey[400],
            size: 20,
          ),
        ),
        title: Text(
          _formatDate(log.date),
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(height: 4),
            Text(
              log.completed ? 'Teljesítve' : 'Nem teljesítve',
              style: TextStyle(
                color: log.completed ? Colors.green : Colors.red,
                fontWeight: FontWeight.w500,
              ),
            ),
            if (log.value != null) ...[
              SizedBox(height: 2),
              Text('Érték: ${log.value}'),
            ],
            if (log.notes != null && log.notes!.isNotEmpty) ...[
              SizedBox(height: 2),
              Text(
                'Megjegyzés: ${log.notes}',
                style: TextStyle(fontStyle: FontStyle.italic),
              ),
            ],
          ],
        ),
        trailing: Container(
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(8),
          ),
          child: IconButton(
            onPressed: () => _showLogDialog(log),
            icon: Icon(Icons.edit, color: Colors.grey[600]),
            tooltip: 'Szerkesztés',
          ),
        ),
      ),
    );
  }

  Widget _buildInfoSection(String title, List<Widget> children) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
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
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressRow(String label, double percentage) {
    final color = percentage >= 100 
        ? Colors.green 
        : percentage >= 50 
            ? Colors.orange 
            : Colors.red;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '$label:',
                style: TextStyle(
                  fontWeight: FontWeight.w500,
                  color: Colors.grey[600],
                ),
              ),
              Text(
                '${percentage.toStringAsFixed(1)}%',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: percentage / 100,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCard(String title, List<Widget> children) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
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
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }

  Widget _buildStatRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.grey[600]),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  String _getTrackingTypeLabel(TrackingType type) {
    switch (type) {
      case TrackingType.boolean:
        return 'Igen/Nem';
      case TrackingType.numeric:
        return 'Numerikus';
    }
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat('yyyy. MMM dd.').format(date);
    } catch (e) {
      return dateStr;
    }
  }

  String _formatMonth(String monthStr) {
    try {
      final parts = monthStr.split('-');
      final year = int.parse(parts[0]);
      final month = int.parse(parts[1]);
      final date = DateTime(year, month);
      return DateFormat('yyyy. MMMM').format(date);
    } catch (e) {
      return monthStr;
    }
  }

  void _showEditDialog() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Szerkesztés funkció hamarosan elérhető'),
        backgroundColor: Color(0xFF00D4AA),
      ),
    );
  }

  void _toggleArchive() async {
    try {
      await _habitService.updateHabit(widget.habitId, {
        'is_active': !_habit!.isActive,
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(_habit!.isActive ? 'Szokás archiválva' : 'Szokás visszaállítva'),
          backgroundColor: Color(0xFF00D4AA),
        ),
      );
      
      Navigator.pop(context, true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hiba: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _showDeleteConfirmation() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        title: const Text(
          'Szokás törlése',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        content: const Text('Biztosan törölni szeretnéd ezt a szokást? Ez a művelet nem visszavonható.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Mégse'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              
              try {
                await _habitService.deleteHabit(widget.habitId);
                
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Szokás törölve'),
                    backgroundColor: Color(0xFF00D4AA),
                  ),
                );
                
                Navigator.pop(context, true);
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Hiba: $e'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: const Text('Törlés'),
          ),
        ],
      ),
    );
  }
}