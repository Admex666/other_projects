// lib/screens/onboarding/tutorial_screen.dart

import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../../models/onboarding_model.dart';
import '../../services/onboarding_service.dart';
import '../../services/auth_service.dart';
import '../../services/analytics_service.dart';
import '/main.dart';

import 'package:frontend/screens/add_incomes_screen.dart';
import 'package:frontend/screens/analysis_screen.dart';
import 'package:frontend/screens/limits/manage_limits_screen.dart';
import 'package:frontend/screens/forum/forum_main_screen.dart'; 
import 'package:frontend/screens/challenges/challenges_main_screen.dart';
import 'package:frontend/screens/pti/pti_main_screen.dart';
import 'package:frontend/screens/profile/badges_screen.dart';
import 'package:frontend/screens/knowledge/knowledge_screen.dart';

class TutorialScreen extends StatefulWidget {
  final UserType userType;
  
  const TutorialScreen({
    Key? key,
    required this.userType,
  }) : super(key: key);

  @override
  _TutorialScreenState createState() => _TutorialScreenState();
}

class _TutorialScreenState extends State<TutorialScreen> with TickerProviderStateMixin {
  final OnboardingService _onboardingService = OnboardingService();
  final AnalyticsService _analyticsService = AnalyticsService();
  final AuthService _authService = AuthService();
  final PageController _pageController = PageController();
  
  bool _isLoading = false;
  bool _isInitialized = false;
  int _currentPage = 0;
  List<TutorialPageData> _tutorialPages = [];
  
  String? _currentUserId;
  String? _currentUsername;
  
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      duration: Duration(milliseconds: 600),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeInOut),
    );
    
    _initializeUserDataAndTutorial();
    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _pageController.dispose();
    super.dispose();
  }

  Future<void> _initializeUserDataAndTutorial() async {
    try {
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 3,
        stepType: 'tutorial_started',
        additionalData: {
          'user_type': widget.userType.toString().split('.').last,
        },
      );

      _currentUserId = await _authService.getUserId();
      _currentUsername = await _authService.getCurrentUsername();
      
      await _initializeTutorialPages();
    } catch (e) {
      print('Error initializing user data: $e');
      await _initializeTutorialPages();
    }
  }

  Future<void> _initializeTutorialPages() async {
    try {
      final tutorialContent = await _onboardingService.getTutorialContent(widget.userType);
      
      if (tutorialContent.steps.isNotEmpty) {
        setState(() {
          _tutorialPages = tutorialContent.steps.map((step) => 
            TutorialPageData(
              title: step.title,
              description: step.content,
              iconData: _getIconForStep(step.title),
              color: _getColorForUserType(widget.userType),
              features: _getFeaturesForStep(step.title),
              actionText: step.highlightElement ?? 'ob_tutorial.actions.continue_label'.tr(),
            )
          ).toList();
          _isInitialized = true;
        });
      } else {
        _initializeStaticTutorialPages();
      }
    } catch (e) {
      _initializeStaticTutorialPages();
    }
  }

  void _initializeStaticTutorialPages() {
    List<TutorialPageData> pages;
    
    switch (widget.userType) {
      case UserType.awareSpender:
        pages = _getAwareSpenderTutorial();
        break;
      case UserType.communityDriven:
        pages = _getCommunityDrivenTutorial();
        break;
      case UserType.learner:
        pages = _getLearnerTutorial();
        break;
      case UserType.advanced:
        pages = _getAdvancedTutorial();
        break;
      case UserType.competitive:
        pages = _getCompetitiveTutorial();
        break;
      default:
        pages = _getAwareSpenderTutorial();
    }
    
    setState(() {
      _tutorialPages = pages;
      _isInitialized = true;
    });
  }

  IconData _getIconForStep(String title) {
    if (title.contains('Tranzakció') || title.contains('tranzakció') || title.contains('Transaction')) return Icons.receipt_long;
    if (title.contains('Elemzés') || title.contains('elemzés') || title.contains('Analytics')) return Icons.analytics;
    if (title.contains('Korlát') || title.contains('korlát') || title.contains('Limit')) return Icons.warning_amber;
    if (title.contains('Közösség') || title.contains('közösség') || title.contains('Community')) return Icons.people;
    if (title.contains('Kitűzők') || title.contains('kitűző') || title.contains('Badges')) return Icons.emoji_events;
    if (title.contains('Tudás') || title.contains('tudás') || title.contains('Knowledge')) return Icons.school;
    if (title.contains('Kvíz') || title.contains('kvíz') || title.contains('Quiz')) return Icons.quiz;
    if (title.contains('Import') || title.contains('import')) return Icons.upload_file;
    if (title.contains('Szabály') || title.contains('szabály') || title.contains('Rule')) return Icons.settings;
    if (title.contains('Ranglista') || title.contains('ranglista') || title.contains('Leaderboard')) return Icons.leaderboard;
    if (title.contains('Kihívások') || title.contains('kihívás') || title.contains('Challenges')) return Icons.speed;
    return Icons.lightbulb;
  }

  Color _getColorForUserType(UserType userType) {
    switch (userType) {
      case UserType.awareSpender: return Color(0xFF4CAF50);
      case UserType.communityDriven: return Color(0xFF9C27B0);
      case UserType.learner: return Color(0xFF3F51B5);
      case UserType.advanced: return Color(0xFF607D8B);
      case UserType.competitive: return Color(0xFFFF6F00);
      default: return Color(0xFF4CAF50);
    }
  }

  List<String> _getFeaturesForStep(String title) {
    if (title.contains('Tranzakció') || title.contains('Transaction')) return [
      'ob_tutorial.features.transaction_1'.tr(),
      'ob_tutorial.features.transaction_2'.tr(),
      'ob_tutorial.features.transaction_3'.tr()
    ];
    if (title.contains('Elemzés') || title.contains('Analytics')) return [
      'ob_tutorial.features.analytics_1'.tr(),
      'ob_tutorial.features.analytics_2'.tr(),
      'ob_tutorial.features.analytics_3'.tr()
    ];
    if (title.contains('Korlát') || title.contains('Limit')) return [
      'ob_tutorial.features.limit_1'.tr(),
      'ob_tutorial.features.limit_2'.tr(),
      'ob_tutorial.features.limit_3'.tr()
    ];
    if (title.contains('Közösség') || title.contains('Community')) return [
      'ob_tutorial.features.community_1'.tr(),
      'ob_tutorial.features.community_2'.tr(),
      'ob_tutorial.features.community_3'.tr()
    ];
    if (title.contains('Kihívás') || title.contains('Challenge')) return [
      'ob_tutorial.features.challenge_1'.tr(),
      'ob_tutorial.features.challenge_2'.tr(),
      'ob_tutorial.features.challenge_3'.tr()
    ];
    if (title.contains('Tudás') || title.contains('Knowledge')) return [
      'ob_tutorial.features.knowledge_1'.tr(),
      'ob_tutorial.features.knowledge_2'.tr(),
      'ob_tutorial.features.knowledge_3'.tr()
    ];
    if (title.contains('Import') || title.contains('Import')) return [
      'ob_tutorial.features.import_1'.tr(),
      'ob_tutorial.features.import_2'.tr(),
      'ob_tutorial.features.import_3'.tr()
    ];
    if (title.contains('Ranglista') || title.contains('Leaderboard')) return [
      'ob_tutorial.features.leaderboard_1'.tr(),
      'ob_tutorial.features.leaderboard_2'.tr(),
      'ob_tutorial.features.leaderboard_3'.tr()
    ];
    return [
      'ob_tutorial.features.transaction_1'.tr(),
      'ob_tutorial.features.transaction_2'.tr(),
      'ob_tutorial.features.transaction_3'.tr()
    ];
  }

  List<TutorialPageData> _getAwareSpenderTutorial() {
    return [
      TutorialPageData(
        title: 'ob_tutorial.titles.end_of_chaos'.tr(),
        description: 'ob_tutorial.descriptions.end_of_chaos'.tr(),
        iconData: Icons.receipt_long,
        color: Color(0xFF4CAF50),
        features: [
          'ob_tutorial.features.transaction_1'.tr(),
          'ob_tutorial.features.transaction_2'.tr(),
          'ob_tutorial.features.transaction_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.add_transaction'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.find_hidden_patterns'.tr(),
        description: 'ob_tutorial.descriptions.find_hidden_patterns'.tr(),
        iconData: Icons.analytics,
        color: Color(0xFF2196F3),
        features: [
          'ob_tutorial.features.analytics_1'.tr(),
          'ob_tutorial.features.analytics_2'.tr(),
          'ob_tutorial.features.analytics_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.view_analytics'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.never_exceed_plan'.tr(),
        description: 'ob_tutorial.descriptions.never_exceed_plan'.tr(),
        iconData: Icons.warning_amber,
        color: Color(0xFFFF9800),
        features: [
          'ob_tutorial.features.limit_1'.tr(),
          'ob_tutorial.features.limit_2'.tr(),
          'ob_tutorial.features.limit_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.set_limit'.tr(),
      ),
    ];
  }

  List<TutorialPageData> _getCommunityDrivenTutorial() {
    return [
      TutorialPageData(
        title: 'ob_tutorial.titles.not_alone'.tr(),
        description: 'ob_tutorial.descriptions.not_alone'.tr(),
        iconData: Icons.people,
        color: Color(0xFF9C27B0),
        features: [
          'ob_tutorial.features.community_1'.tr(),
          'ob_tutorial.features.community_2'.tr(),
          'ob_tutorial.features.community_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.browse_forum'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.reach_goals_playfully'.tr(),
        description: 'ob_tutorial.descriptions.reach_goals_playfully'.tr(),
        iconData: Icons.emoji_events,
        color: Color(0xFFE91E63),
        features: [
          'ob_tutorial.features.challenge_1'.tr(),
          'ob_tutorial.features.challenge_2'.tr(),
          'ob_tutorial.features.challenge_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.choose_challenge'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.stronger_together'.tr(),
        description: 'ob_tutorial.descriptions.stronger_together'.tr(),
        iconData: Icons.trending_up,
        color: Color(0xFF00BCD4),
        features: [
          'ob_tutorial.features.group_1'.tr(),
          'ob_tutorial.features.group_2'.tr(),
          'ob_tutorial.features.group_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.find_group'.tr(),
      ),
    ];
  }

  List<TutorialPageData> _getLearnerTutorial() {
    return [
      TutorialPageData(
        title: 'ob_tutorial.titles.confident_decisions'.tr(),
        description: 'ob_tutorial.descriptions.confident_decisions'.tr(),
        iconData: Icons.school,
        color: Color(0xFF3F51B5),
        features: [
          'ob_tutorial.features.knowledge_1'.tr(),
          'ob_tutorial.features.knowledge_2'.tr(),
          'ob_tutorial.features.knowledge_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.start_lesson'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.test_knowledge'.tr(),
        description: 'ob_tutorial.descriptions.test_knowledge'.tr(),
        iconData: Icons.quiz,
        color: Color(0xFF673AB7),
        features: [
          'ob_tutorial.features.quiz_1'.tr(),
          'ob_tutorial.features.quiz_2'.tr(),
          'ob_tutorial.features.quiz_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.solve_quiz'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.learn_from_community'.tr(),
        description: 'ob_tutorial.descriptions.learn_from_community'.tr(),
        iconData: Icons.people,
        color: Color(0xFFFF5722),
        features: [
          'ob_tutorial.features.forum_1'.tr(),
          'ob_tutorial.features.forum_2'.tr(),
          'ob_tutorial.features.forum_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.explore_forum'.tr(),
      ),
    ];
  }

  List<TutorialPageData> _getAdvancedTutorial() {
    return [
      TutorialPageData(
        title: 'ob_tutorial.titles.automate_life'.tr(),
        description: 'ob_tutorial.descriptions.automate_life'.tr(),
        iconData: Icons.upload_file,
        color: Color(0xFF607D8B),
        features: [
          'ob_tutorial.features.import_1'.tr(),
          'ob_tutorial.features.import_2'.tr(),
          'ob_tutorial.features.import_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.import_data'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.precise_control'.tr(),
        description: 'ob_tutorial.descriptions.precise_control'.tr(),
        iconData: Icons.settings,
        color: Color(0xFF795548),
        features: [
          'ob_tutorial.features.settings_1'.tr(),
          'ob_tutorial.features.settings_2'.tr(),
          'ob_tutorial.features.settings_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.create_rule'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.deep_insight'.tr(),
        description: 'ob_tutorial.descriptions.deep_insight'.tr(),
        iconData: Icons.insights,
        color: Color(0xFF009688),
        features: [
          'ob_tutorial.features.insights_1'.tr(),
          'ob_tutorial.features.insights_2'.tr(),
          'ob_tutorial.features.insights_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.advanced_analytics'.tr(),
      ),
    ];
  }

  List<TutorialPageData> _getCompetitiveTutorial() {
    return [
      TutorialPageData(
        title: 'ob_tutorial.titles.compete_and_grow'.tr(),
        description: 'ob_tutorial.descriptions.compete_and_grow'.tr(),
        iconData: Icons.leaderboard,
        color: Color(0xFFFF6F00),
        features: [
          'ob_tutorial.features.leaderboard_1'.tr(),
          'ob_tutorial.features.leaderboard_2'.tr(),
          'ob_tutorial.features.leaderboard_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.view_challenges'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.measure_yourself'.tr(),
        description: 'ob_tutorial.descriptions.measure_yourself'.tr(),
        iconData: Icons.speed,
        color: Color(0xFFE65100),
        features: [
          'ob_tutorial.features.pti_1'.tr(),
          'ob_tutorial.features.pti_2'.tr(),
          'ob_tutorial.features.pti_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.start_pti_calc'.tr(),
      ),
      TutorialPageData(
        title: 'ob_tutorial.titles.collect_badges'.tr(),
        description: 'ob_tutorial.descriptions.collect_badges'.tr(),
        iconData: Icons.military_tech,
        color: Color(0xFFBF360C),
        features: [
          'ob_tutorial.features.badge_1'.tr(),
          'ob_tutorial.features.badge_2'.tr(),
          'ob_tutorial.features.badge_3'.tr(),
        ],
        actionText: 'ob_tutorial.actions.get_badge'.tr(),
      ),
    ];
  }

  void _nextPage() {
    if (_currentPage < _tutorialPages.length - 1) {
      _analyticsService.trackFeatureUsage('tutorial_page_${_currentPage + 1}_completed');
      _pageController.nextPage(
        duration: Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _completeTutorial();
    }
  }

  void _previousPage() {
    if (_currentPage > 0) {
      _pageController.previousPage(
        duration: Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  void _navigateToFeature(String actionText, String title) {
    _analyticsService.trackFeatureUsage('tutorial_feature_explored_${actionText.toLowerCase().replaceAll(' ', '_')}');

    if (actionText == 'ob_tutorial.actions.add_transaction'.tr()) {
      _navigateToScreenWithUserId(_createAddIncomesScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.view_analytics'.tr()) {
      _navigateToScreenWithUserId(_createAnalysisScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.set_limit'.tr()) {
      _navigateToScreenWithUserId(_createManageLimitsScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.browse_forum'.tr() || actionText == 'ob_tutorial.actions.explore_forum'.tr()) {
      _navigateToScreenWithUserId(_createForumMainScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.choose_challenge'.tr() || actionText == 'ob_tutorial.actions.view_challenges'.tr()) {
      _navigateToScreenWithUserId(_createChallengesMainScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.start_lesson'.tr() || actionText == 'ob_tutorial.actions.solve_quiz'.tr()) {
      _navigateToScreenWithUserId(_createKnowledgeScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.import_data'.tr() || actionText == 'ob_tutorial.actions.create_rule'.tr() || actionText == 'ob_tutorial.actions.advanced_analytics'.tr() || actionText == 'ob_tutorial.actions.find_group'.tr()) {
      _showComingSoonMessage(actionText);
    } else if (actionText == 'ob_tutorial.actions.start_pti_calc'.tr()) {
      _navigateToScreenWithUserId(_createPTIMainScreen, actionText);
    } else if (actionText == 'ob_tutorial.actions.get_badge'.tr()) {
      _navigateToScreenWithUserId(_createBadgesScreen, actionText);
    } else {
      _showComingSoonMessage(actionText);
    }
  }

  void _showComingSoonMessage(String actionText) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('ob_tutorial.loading_message'.tr(namedArgs: {'actionText': actionText})),
        backgroundColor: Color(0xFF00D4A3),
      ),
    );
  }

  void _showErrorMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  Future<void> _completeTutorial() async {
    setState(() => _isLoading = true);

    try {
      await _analyticsService.trackOnboardingProgress(
        stepNumber: 6,
        stepType: 'tutorial_completed',
        additionalData: {
          'user_type': widget.userType.toString().split('.').last,
          'pages_viewed': _currentPage + 1,
          'total_pages': _tutorialPages.length,
        },
      );

      await _onboardingService.completeOnboarding();

      await _analyticsService.trackMultipleFeatures([
        'onboarding_fully_completed',
        'time_to_value_achieved',
        'first_time_user_journey_completed',
      ]);
      
      if (mounted) {
        final username = _currentUsername ?? 'User';
        final userId = _currentUserId ?? 'user_id';
        
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => MainScreen(
              username: username,
              userId: userId,
            ),
          ),
        );

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_tutorial.message_complete'.tr()),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('ob_tutorial.message_error'.tr(namedArgs: {'error': e.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _skipTutorial() {
    _analyticsService.trackOnboardingProgress(
      stepNumber: 3,
      stepType: 'tutorial_skipped',
      additionalData: {
        'skipped_at_page': _currentPage + 1,
        'total_pages': _tutorialPages.length,
      },
    );

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('ob_tutorial.dialog_title'.tr()),
        content: Text('ob_tutorial.dialog_content'.tr()),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('ob_tutorial.dialog_cancel_button'.tr()),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _completeTutorial();
            },
            child: Text('ob_tutorial.dialog_confirm_button'.tr()),
          ),
        ],
      ),
    );
  }

  Future<void> _navigateToScreenWithUserId(Widget Function(String userId) screenBuilder, String actionText) async {
    if (_currentUserId == null) {
      _currentUserId = await _authService.getUserId();
    }
    
    if (_currentUserId == null) {
      _showErrorMessage('ob_tutorial.error_user_data'.tr());
      return;
    }
    
    final targetScreen = screenBuilder(_currentUserId!);
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => targetScreen),
    );
  }

  Widget _createAddIncomesScreen(String userId) => AddIncomesScreen(userId: userId);
  Widget _createForumMainScreen(String userId) => ForumMainScreen(userId: userId);
  Widget _createAnalysisScreen(String userId) => AnalysisScreen(
    userId: userId, 
    fromTutorial: true,
  );
  Widget _createManageLimitsScreen(String userId) => ManageLimitsScreen(userId: userId);
  Widget _createChallengesMainScreen(String userId) => ChallengesMainScreen(userId: userId);
  Widget _createPTIMainScreen(String userId) => PTIMainScreen(userId: userId);
  Widget _createBadgesScreen(String userId) => BadgesScreen(userId: userId);
  Widget _createKnowledgeScreen(String userId) => KnowledgeScreen(userId: userId);

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized) {
      return Scaffold(
        body: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF00D4A3),
                Color(0xFFE8F6F3),
              ],
              stops: [0.0, 0.4],
            ),
          ),
          child: Center(
            child: CircularProgressIndicator(
              color: Colors.white,
            ),
          ),
        ),
      );
    }

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFF00D4A3),
              Color(0xFFE8F6F3),
            ],
            stops: [0.0, 0.4],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.arrow_back, color: Colors.black),
                      onPressed: _currentPage > 0 ? _previousPage : () {
                        Navigator.of(context).pop();
                      },
                    ),
                    SizedBox(width: 30),
                    Expanded(
                      child: Column(
                        children: [
                          Text(
                            'ob_tutorial.step_label'.tr(namedArgs: {'step_number': '4'}),
                            style: TextStyle(
                              color: Colors.black.withOpacity(0.8),
                              fontSize: 14,
                            ),
                          ),
                          Text(
                            'ob_tutorial.screen_title'.tr(),
                            style: TextStyle(
                              color: Colors.black,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                    TextButton(
                      onPressed: _skipTutorial,
                      child: Text(
                        'ob_tutorial.skip_button'.tr(),
                        style: TextStyle(
                          color: Colors.black.withOpacity(0.8),
                          fontSize: 15,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20),
                child: Column(
                  children: [
                    Row(
                      children: List.generate(_tutorialPages.length, (index) {
                        return Expanded(
                          child: Container(
                            height: 4,
                            margin: EdgeInsets.symmetric(horizontal: 2),
                            decoration: BoxDecoration(
                              color: index <= _currentPage 
                                  ? Colors.black 
                                  : Colors.black.withOpacity(0.3),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        );
                      }),
                    ),
                    SizedBox(height: 8),
                    Text(
                      '${_currentPage + 1} / ${_tutorialPages.length}',
                      style: TextStyle(
                        color: Colors.black.withOpacity(0.8),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Container(
                  margin: EdgeInsets.only(top: 24),
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: PageView.builder(
                      controller: _pageController,
                      onPageChanged: (page) {
                        setState(() {
                          _currentPage = page;
                        });
                      },
                      itemCount: _tutorialPages.length,
                      itemBuilder: (context, index) {
                        return _buildTutorialPage(_tutorialPages[index]);
                      },
                    ),
                  ),
                ),
              ),
              Container(
                padding: EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Color(0xFFF5F5F5),
                ),
                child: Row(
                  children: [
                    if (_currentPage > 0) ...[
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _previousPage,
                          style: OutlinedButton.styleFrom(
                            side: BorderSide(color: Color(0xFF00D4A3)),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(28),
                            ),
                            padding: EdgeInsets.symmetric(vertical: 16),
                          ),
                          child: Text(
                            'ob_tutorial.previous_button'.tr(),
                            style: TextStyle(
                              fontSize: 16,
                              color: Color(0xFF00D4A3),
                            ),
                          ),
                        ),
                      ),
                      SizedBox(width: 16),
                    ],
                    Expanded(
                      flex: _currentPage > 0 ? 1 : 2,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _nextPage,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Color(0xFF00D4A3),
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(28),
                          ),
                          padding: EdgeInsets.symmetric(vertical: 16),
                        ),
                        child: _isLoading
                            ? CircularProgressIndicator(color: Colors.white)
                            : Text(
                                _currentPage < _tutorialPages.length - 1 
                                    ? 'ob_tutorial.next_button'.tr() 
                                    : 'ob_tutorial.go_button'.tr(),
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTutorialPage(TutorialPageData pageData) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        children: [
          SizedBox(height: 20),
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              color: pageData.color.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(
              pageData.iconData,
              size: 50,
              color: pageData.color,
            ),
          ),
          SizedBox(height: 32),
          Text(
            pageData.title,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),
          Text(
            pageData.description,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
              height: 1.4,
            ),
          ),
          SizedBox(height: 40),
          Container(
            padding: EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: pageData.features.map((feature) {
                return Container(
                  margin: EdgeInsets.only(bottom: 16),
                  child: Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: pageData.color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      SizedBox(width: 16),
                      Expanded(
                        child: Text(
                          feature,
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
          SizedBox(height: 32),
          Container(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => _navigateToFeature(pageData.actionText, pageData.title),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: pageData.color, width: 2),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                padding: EdgeInsets.symmetric(vertical: 16),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    pageData.actionText,
                    style: TextStyle(
                      fontSize: 16,
                      color: pageData.color,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(width: 8),
                  Icon(
                    Icons.arrow_forward,
                    color: pageData.color,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),
          SizedBox(height: 40),
        ],
      ),
    );
  }
}

class TutorialPageData {
  final String title;
  final String description;
  final IconData iconData;
  final Color color;
  final List<String> features;
  final String actionText;

  TutorialPageData({
    required this.title,
    required this.description,
    required this.iconData,
    required this.color,
    required this.features,
    required this.actionText,
  });
}