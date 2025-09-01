// lib/screens/knowledge/knowledge_screen.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:easy_localization/easy_localization.dart';
import '../../services/auth_service.dart'; // AuthService import hozzáadása
import 'lesson_detail_screen.dart';
import 'package:provider/provider.dart';
import '../../providers/subscription_provider.dart';
import '../../widgets/subscription/feature_locked_widget.dart';
import '../../models/subscription.dart';
import '../../utils/subscription_utils.dart';
import '../../widgets/subscription/subscription_widgets.dart';
import 'package:frontend/config/config.dart'; 

class KnowledgeScreen extends StatefulWidget {
  final String userId;

  const KnowledgeScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _KnowledgeScreenState createState() => _KnowledgeScreenState();
}

class _KnowledgeScreenState extends State<KnowledgeScreen> {
  final AuthService _authService = AuthService();
  List<CategoryWithLessons> categories = [];
  UserStats? userStats;
  bool isLoading = true;
  String? selectedDifficulty;
  bool _hasKnowledgeAccess = false;
  int _dailyLessonCount = 0;
  bool _isCheckingAccess = false;
  Map<String, dynamic>? _dailyStats;

  @override
  void initState() {
    super.initState();
    _checkKnowledgeAccess(); // Ez rögtön ellenőrzi a jogosultságot
  }

  // Új metódus
  Future<void> _loadDailyStats() async {
    final token = await _authService.getToken();
    if (token == null) return;

    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/knowledge/daily-stats'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _dailyStats = data;
          _dailyLessonCount = data['daily_lessons_completed'] ?? 0;
        });
        print('Daily stats loaded: $_dailyStats');
      }
    } catch (e) {
      print('Error loading daily stats: $e');
    }
  }

  // _checkKnowledgeAccess metódus
  Future<void> _checkKnowledgeAccess() async {
    setState(() => _isCheckingAccess = true);
    
    try {
      final subscriptionProvider = Provider.of<SubscriptionProvider>(context, listen: false);
      
      // DAILY STATS BETÖLTÉSE ELŐSZÖR
      await _loadDailyStats();
      
      // Ha van full access, akkor mindent engedélyezünk
      if (subscriptionProvider.hasFullKnowledge) {
        setState(() {
          _hasKnowledgeAccess = true;
        });
        _loadData();
        return;
      }
      
      // Free felhasználók esetén ellenőrizzük a napi limitet
      final canTakeMoreLessons = _dailyStats?['can_take_more_lessons'] ?? true;
      
      setState(() {
        _hasKnowledgeAccess = true; // Mindig engedjük a belépést
      });
      
      _loadData();
    } catch (e) {
      print('Error checking knowledge access: $e');
      setState(() => _hasKnowledgeAccess = true); // Hiba esetén is engedjük
      _loadData();
    } finally {
      setState(() => _isCheckingAccess = false);
    }
  }

  Future<void> _loadData() async {
    setState(() => isLoading = true);
    
    try {
      // Token ellenőrzés
      final token = await _authService.getToken();
      if (token == null) {
        _handleAuthError();
        return;
      }

      await Future.wait([
        _loadCategories(),
        _loadUserStats(),
      ]);
    } catch (e) {
      print('Error loading data: $e');
      _handleLoadError(e);
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> _loadCategories() async {
    final token = await _authService.getToken();
    if (token == null) {
      _handleAuthError();
      return;
    }
    
    String url = '${ApiConfig.baseUrl}/knowledge/categories';
    if (selectedDifficulty != null) {
      url += '?difficulty=$selectedDifficulty';
    }

    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          categories = data.map((json) => CategoryWithLessons.fromJson(json)).toList();
        });
        print('Categories loaded: ${categories.length}'); // Debug
        for (var cat in categories) {
          print('Category: ${cat.name}, completed: ${cat.completedLessons}/${cat.totalLessons}'); // Debug
        }
      } else if (response.statusCode == 401) {
        _handleAuthError();
      } else {
        throw Exception('Failed to load categories: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading categories: $e');
      rethrow;
    }
  }

  Future<void> _loadUserStats() async {
    final token = await _authService.getToken();
    if (token == null) {
      _handleAuthError();
      return;
    }

    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/knowledge/stats'),
        headers: {'Authorization': 'Bearer $token'},
      );

      print('Stats response status: ${response.statusCode}');
      print('Stats response body: ${response.body}');

      if (response.statusCode == 200) {
        final statsData = json.decode(response.body);
        print('Parsed stats data: $statsData'); // Extra debug
        setState(() {
          userStats = UserStats.fromJson(statsData);
        });
        print('UserStats loaded successfully:');
        print('- Current streak: ${userStats?.currentStreak}');
        print('- Total lessons: ${userStats?.totalLessonsCompleted}');
        print('- Study minutes: ${userStats?.totalStudyMinutes}');
        print('- Average score: ${userStats?.averageQuizScore}');
      } else if (response.statusCode == 401) {
        _handleAuthError();
      } else {
        throw Exception('Failed to load user stats: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading user stats: $e');
      rethrow;
    }
  }

  Future<void> _completeDailyChallenge() async {
    final token = await _authService.getToken();
    if (token == null) {
      _handleAuthError();
      return;
    }

    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/knowledge/daily-challenge'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('knowledge.daily_challenge_complete_success'.tr()),
            backgroundColor: Colors.green,
          ),
        );
        _loadUserStats();
      } else if (response.statusCode == 401) {
        _handleAuthError();
      } else {
        throw Exception('Failed to complete daily challenge: ${response.statusCode}');
      }
    } catch (e) {
      print('Error completing daily challenge: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('error_occured'.tr(namedArgs: {'error': e.toString()})),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _handleAuthError() {
    // Token érvénytelen vagy hiányzik - kijelentkeztetés és visszairányítás
    _authService.logout();
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('knowledge.session_expired'.tr()),
          backgroundColor: Colors.red,
        ),
      );
      
      // Navigáció a bejelentkező képernyőre
      Navigator.of(context).pushNamedAndRemoveUntil(
        '/', // Vagy ahogy a bejelentkező route-od hívják
        (route) => false,
      );
    }
  }

  void _handleLoadError(dynamic error) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('knowledge.loading_error'.tr(namedArgs: {'error': error.toString()})),
          backgroundColor: Colors.red,
          action: SnackBarAction(
            label: 'knowledge.retry'.tr(),
            onPressed: _loadData,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF00D4A3),
      body: SafeArea(
        child: Column(
          children: [
            // Header változatlan...
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
                      'knowledge.title'.tr(),
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  // USAGE INDICATOR HOZZÁADÁSA
                  Consumer<SubscriptionProvider>(
                    builder: (context, provider, child) {
                      if (!provider.hasFullKnowledge) {
                        final current = _dailyStats?['daily_lessons_completed'] ?? 0;
                        final limit = _dailyStats?['daily_lessons_limit'] ?? 1;
                        
                        return InlineUsageIndicator(
                          current: current,
                          limit: limit,
                          color: Color(0xFF00D4A3),
                        );
                      }
                      return SizedBox(width: 48);
                    },
                  ),
                ],
              ),
            ),
            
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
                child: _isCheckingAccess
                    ? const Center(child: CircularProgressIndicator(color: Color(0xFF00D4A3)))
                    : !_hasKnowledgeAccess
                        ? FeatureLockedWidget(
                            featureName: 'knowledge.title'.tr(),
                            description: 'knowledge.feature_locked_description'.tr(),
                            requiredTier: SubscriptionTier.plus,
                          )
                        : isLoading
                            ? const Center(child: CircularProgressIndicator(color: Color(0xFF00D4A3)))
                            : RefreshIndicator(
                                onRefresh: _loadData,
                                color: const Color(0xFF00D4A3),
                                child: SingleChildScrollView(
                                  physics: const AlwaysScrollableScrollPhysics(),
                                  padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      if (userStats != null) _buildStatsCard(),
                                      const SizedBox(height: 40),
                                      _buildDailyChallengeCard(),
                                      const SizedBox(height: 40),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            'knowledge.categories'.tr(),
                                            style: TextStyle(
                                              fontSize: 24,
                                              fontWeight: FontWeight.bold,
                                              color: Color(0xFF2D3748),
                                            ),
                                          ),
                                          Container(
                                            decoration: BoxDecoration(
                                              color: const Color(0xFF00D4A3),
                                              borderRadius: BorderRadius.circular(12),
                                            ),
                                            child: PopupMenuButton<String>(
                                              icon: const Icon(Icons.filter_list, color: Colors.white),
                                              onSelected: (value) {
                                                setState(() {
                                                  selectedDifficulty = value == 'all' ? null : value;
                                                });
                                                _loadCategories();
                                              },
                                              itemBuilder: (context) => [
                                                PopupMenuItem(value: 'all', child: Text('knowledge.all_levels'.tr())),
                                                PopupMenuItem(value: 'beginner', child: Text('knowledge.beginner'.tr())),
                                                PopupMenuItem(value: 'professional', child: Text('knowledge.pro'.tr())),
                                              ],
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 16),
                                      ...categories.map((category) => _buildCategoryCard(category)),
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

  Widget _buildStatsCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF00D4A3), Color(0xFF00B894)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00D4A3).withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'knowledge.your_stats'.tr(),
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStatItem(
                  '🔥',
                  '${userStats!.currentStreak}',
                  'knowledge.daily_streak'.tr(),
                ),
              ),
              Expanded(
                child: _buildStatItem(
                  '📚',
                  '${userStats!.totalLessonsCompleted}',
                  'knowledge.lessons_completed'.tr(),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildStatItem(
                  '⏱️',
                  '${userStats!.totalStudyMinutes}',
                  'knowledge.study_minutes'.tr(),
                ),
              ),
              Expanded(
                child: _buildStatItem(
                  '📊',
                  '${userStats!.averageQuizScore.toInt()}%',
                  'knowledge.average_score'.tr(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String emoji, String value, String label) {
    return Column(
      children: [
        Text(
          emoji,
          style: const TextStyle(fontSize: 24),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.white70,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildDailyChallengeCard() {
    final isCompleted = userStats?.dailyChallengeCompletedToday ?? false;
    
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isCompleted ? Colors.green.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(
          color: isCompleted ? Colors.green : Colors.orange,
          width: 2,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isCompleted ? Colors.green : Colors.orange,
              shape: BoxShape.circle,
            ),
            child: Icon(
              isCompleted ? Icons.check : Icons.star,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  isCompleted ? 'knowledge.daily_challenge_completed'.tr() : 'knowledge.daily_challenge'.tr(),
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: isCompleted ? Colors.green : Colors.orange,
                  ),
                ),
                Text(
                  isCompleted 
                    ? 'knowledge.challenge_completed_message'.tr()
                    : 'knowledge.challenge_todo_message'.tr(),
                  style: const TextStyle(
                    fontSize: 13,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
          ),
          if (!isCompleted)
            ElevatedButton(
              onPressed: _completeDailyChallenge,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
              child: Text(
                'knowledge.start_button'.tr(),
                style: const TextStyle(color: Colors.white),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildCategoryCard(CategoryWithLessons category) {
    final progress = category.totalLessons > 0 
        ? category.completedLessons / category.totalLessons 
        : 0.0;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
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
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(15),
          onTap: () => _showCategoryLessons(category),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Color(int.parse(category.color?.substring(1) ?? 'FF00D4A3', radix: 16) | 0xFF000000)
                            .withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        category.icon ?? '📚',
                        style: const TextStyle(fontSize: 24),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            category.name,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF2D3748),
                            ),
                          ),
                          if (category.description != null)
                            Text(
                              category.description!,
                              style: const TextStyle(
                                fontSize: 14,
                                color: Colors.grey,
                              ),
                            ),
                        ],
                      ),
                    ),
                    const Icon(
                      Icons.arrow_forward_ios,
                      color: Colors.grey,
                      size: 16,
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'knowledge.lesson_progress'.tr(namedArgs: {'completed': category.completedLessons.toString(), 'total': category.totalLessons.toString()}),
                            style: const TextStyle(
                              fontSize: 14,
                              color: Colors.grey,
                            ),
                          ),
                          const SizedBox(height: 4),
                          LinearProgressIndicator(
                            value: progress,
                            backgroundColor: Colors.grey[200],
                            valueColor: AlwaysStoppedAnimation<Color>(
                              Color(int.parse(category.color?.substring(1) ?? 'FF00D4A3', radix: 16) | 0xFF000000),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    Text(
                      '${(progress * 100).toInt()}%',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF00D4A3),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showCategoryLessons(CategoryWithLessons category) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.5,
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
                decoration: BoxDecoration(
                  color: Color(int.parse(category.color?.substring(1) ?? 'FF00D4A3', radix: 16) | 0xFF000000),
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(20),
                    topRight: Radius.circular(20),
                  ),
                ),
                child: Row(
                  children: [
                    Text(
                      category.icon ?? '📚',
                      style: const TextStyle(fontSize: 32),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        category.name,
                        style: const TextStyle(
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
                child: ListView.builder(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: category.lessons.length,
                  itemBuilder: (context, index) {
                    final lesson = category.lessons[index];
                    return _buildLessonCard(lesson);
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLessonCard(LessonSummary lesson) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: lesson.isCompleted ? Colors.green.withOpacity(0.1) : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: lesson.isCompleted ? Colors.green : Colors.grey[300]!,
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () async {
            final subscriptionProvider = Provider.of<SubscriptionProvider>(context, listen: false);
            
            bool canAccess = false;
            
            if (subscriptionProvider.hasFullKnowledge) {
              // Fizetős felhasználók mindig hozzáférhetnek
              canAccess = true;
            } else {
              // Free felhasználók: ellenőrizzük a napi limitet
              final canTakeMoreLessons = _dailyStats?['can_take_more_lessons'] ?? true;
              
              if (canTakeMoreLessons) {
                canAccess = true;
              } else {
                // Itt jelenítjük meg az upgrade dialógust
                SubscriptionUtils.showUpgradeDialog(
                  context,
                  feature: 'knowledge.more_lessons_today'.tr(),
                  requiredTier: SubscriptionTier.plus,
                );
                return;
              }
            }
            
            if (canAccess) {
              Navigator.pop(context);
              final result = await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => LessonDetailScreen(
                    lessonId: lesson.id,
                    userId: widget.userId,
                  ),
                ),
              );
              
              // Ha visszajött a lecke képernyőről és teljesítette, frissítjük a daily stats-ot
              if (result == true) {
                await Future.wait([
                  _loadDailyStats(),
                  _loadCategories(),
                  _loadUserStats(),
                ]);
                setState(() {}); // UI frissítés
              }
            }
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: lesson.isCompleted 
                        ? Colors.green 
                        : (lesson.difficulty == 'beginner' ? Colors.orange : Colors.blue),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    lesson.isCompleted ? Icons.check : Icons.play_arrow,
                    color: Colors.white,
                    size: 16,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lesson.title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      if (lesson.description != null)
                        Text(
                          lesson.description!,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                          ),
                        ),
                      Row(
                        children: [
                          Icon(
                            Icons.access_time,
                            size: 14,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'knowledge.estimated_minutes'.tr(namedArgs: {'minutes': lesson.estimatedMinutes.toString()}),
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                          if (lesson.hasQuiz) ...[
                            const SizedBox(width: 12),
                            Icon(
                              Icons.quiz,
                              size: 14,
                              color: Colors.grey[600],
                            ),
                            const SizedBox(width: 4),
                            Text(
                              'knowledge.quiz'.tr(),
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                          if (lesson.quizScore != null) ...[
                            const SizedBox(width: 12),
                            Icon(
                              Icons.star,
                              size: 14,
                              color: Colors.orange,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '${lesson.quizScore}%',
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.orange,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
                Text(
                  lesson.difficulty == 'beginner' ? '🟢' : '🔵',
                  style: const TextStyle(fontSize: 16),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Model osztályok (ezek változatlanok maradtak)
class CategoryWithLessons {
  final String id;
  final String name;
  final String? description;
  final String? icon;
  final String? color;
  final List<LessonSummary> lessons;
  final int totalLessons;
  final int completedLessons;

  CategoryWithLessons({
    required this.id,
    required this.name,
    this.description,
    this.icon,
    this.color,
    required this.lessons,
    required this.totalLessons,
    required this.completedLessons,
  });

  factory CategoryWithLessons.fromJson(Map<String, dynamic> json) {
    return CategoryWithLessons(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      icon: json['icon'],
      color: json['color'],
      lessons: (json['lessons'] as List)
          .map((lesson) => LessonSummary.fromJson(lesson))
          .toList(),
      totalLessons: json['total_lessons'],
      completedLessons: json['completed_lessons'],
    );
  }
}

class LessonSummary {
  final String id;
  final String title;
  final String? description;
  final String difficulty;
  final int estimatedMinutes;
  final int totalPages;
  final bool hasQuiz;
  final bool isCompleted;
  final int? quizScore;
  final String categoryName;

  LessonSummary({
    required this.id,
    required this.title,
    this.description,
    required this.difficulty,
    required this.estimatedMinutes,
    required this.totalPages,
    required this.hasQuiz,
    required this.isCompleted,
    this.quizScore,
    required this.categoryName,
  });

  factory LessonSummary.fromJson(Map<String, dynamic> json) {
    return LessonSummary(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      difficulty: json['difficulty'],
      estimatedMinutes: json['estimated_minutes'],
      totalPages: json['total_pages'],
      hasQuiz: json['has_quiz'],
      isCompleted: json['is_completed'],
      quizScore: json['quiz_score'],
      categoryName: json['category_name'],
    );
  }
}

class UserStats {
  final int currentStreak;
  final int longestStreak;
  final int totalLessonsCompleted;
  final int totalQuizAttempts;
  final double averageQuizScore;
  final int totalStudyMinutes;
  final bool dailyChallengeCompletedToday;
  final int dailyChallengeStreak;

  UserStats({
    required this.currentStreak,
    required this.longestStreak,
    required this.totalLessonsCompleted,
    required this.totalQuizAttempts,
    required this.averageQuizScore,
    required this.totalStudyMinutes,
    required this.dailyChallengeCompletedToday,
    required this.dailyChallengeStreak,
  });

  factory UserStats.fromJson(Map<String, dynamic> json) {
    print('Parsing UserStats from JSON: $json');
    
    // Explicit type conversion és null safety
    return UserStats(
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
      longestStreak: (json['longest_streak'] as num?)?.toInt() ?? 0,
      totalLessonsCompleted: (json['total_lessons_completed'] as num?)?.toInt() ?? 0,
      totalQuizAttempts: (json['total_quiz_attempts'] as num?)?.toInt() ?? 0,
      averageQuizScore: (json['average_quiz_score'] as num?)?.toDouble() ?? 0.0,
      totalStudyMinutes: (json['total_study_minutes'] as num?)?.toInt() ?? 0,
      dailyChallengeCompletedToday: json['daily_challenge_completed_today'] as bool? ?? false,
      dailyChallengeStreak: (json['daily_challenge_streak'] as num?)?.toInt() ?? 0,
    );
  }
}