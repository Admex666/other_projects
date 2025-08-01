// lib/screens/onboarding/tutorial_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/challenge.dart';
import '../../models/onboarding_model.dart';
import '../../services/onboarding_service.dart';
import '../../services/auth_service.dart'; // ÚJ: AuthService import
import '/main.dart';

import 'package:frontend/screens/add_incomes_screen.dart';
import 'package:frontend/screens/analysis_screen.dart';
import 'package:frontend/screens/manage_limits_screen.dart';
import 'package:frontend/screens/forum/forum_main_screen.dart'; 
import 'package:frontend/screens/challenges/challenges_main_screen.dart';
import 'package:frontend/screens/pti/pti_main_screen.dart';
import 'package:frontend/screens/profile/badges_screen.dart';

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
  final AuthService _authService = AuthService(); // ÚJ: AuthService instance
  final PageController _pageController = PageController();
  
  bool _isLoading = false;
  bool _isInitialized = false;
  int _currentPage = 0;
  List<TutorialPageData> _tutorialPages = [];
  
  // ÚJ: User adatok tárolása
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
    
    _initializeUserDataAndTutorial(); // ÚJ: User adatok + tutorial inicializálása
    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _pageController.dispose();
    super.dispose();
  }

  // ÚJ: User adatok lekérése és tutorial inicializálása
  Future<void> _initializeUserDataAndTutorial() async {
    try {
      // User adatok lekérése az AuthService-ból
      _currentUserId = await _authService.getUserId();
      _currentUsername = await _authService.getCurrentUsername();
      
      // Tutorial tartalom inicializálása
      await _initializeTutorialPages();
    } catch (e) {
      print('Error initializing user data: $e');
      // Ha nincs user adat, fallback-kel folytatjuk
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
              actionText: step.highlightElement ?? 'Tovább',
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
    if (title.contains('Tranzakció') || title.contains('tranzakció')) return Icons.receipt_long;
    if (title.contains('Elemzés') || title.contains('elemzés')) return Icons.analytics;
    if (title.contains('Korlát') || title.contains('korlát')) return Icons.warning_amber;
    if (title.contains('Közösség') || title.contains('közösség')) return Icons.people;
    if (title.contains('Kihívás') || title.contains('kihívás')) return Icons.emoji_events;
    if (title.contains('Tudás') || title.contains('tudás')) return Icons.school;
    if (title.contains('Kvíz') || title.contains('kvíz')) return Icons.quiz;
    if (title.contains('Import') || title.contains('import')) return Icons.upload_file;
    if (title.contains('Szabály') || title.contains('szabály')) return Icons.settings;
    if (title.contains('Ranglista') || title.contains('ranglista')) return Icons.leaderboard;
    if (title.contains('PTI') || title.contains('pont')) return Icons.speed;
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
    if (title.contains('Tranzakció')) return ['Gyors hozzáadás', 'Automatikus kategorizálás', 'Ismétlődő tranzakciók'];
    if (title.contains('Elemzés')) return ['Kategóriánkénti bontás', 'Trendek és előrejelzések', 'Havi összehasonlítás'];
    if (title.contains('Korlát')) return ['Kategóriánkénti korlátok', 'Automatikus figyelmeztetések', 'Havi és heti limitek'];
    if (title.contains('Közösség')) return ['Tippek és tapasztalatok', 'Kérdések és válaszok', 'Motiváció és támogatás'];
    if (title.contains('Kihívás')) return ['Havi kihívások', 'Közös célok', 'Jutalmak és elismerések'];
    if (title.contains('Tudás')) return ['Interaktív leckék', 'Gyakorlati példák', 'Haladás követése'];
    if (title.contains('Import')) return ['CSV és Excel import', 'Banki kapcsolat', 'Automatikus kategorizálás'];
    if (title.contains('Ranglista')) return ['Havi rangsorok', 'Kategória versenyek', 'Regionális összehasonlítás'];
    return ['Hasznos funkciók', 'Személyre szabott élmény', 'Egyszerű használat'];
  }

  List<TutorialPageData> _getAwareSpenderTutorial() {
    return [
      TutorialPageData(
        title: 'Tranzakcióid nyomon követése',
        description: 'Rögzítsd minden bevételedet és kiadásodat egyszerűen',
        iconData: Icons.receipt_long,
        color: Color(0xFF4CAF50),
        features: [
          'Gyors hozzáadás egy érintéssel',
          'Automatikus kategorizálás',
          'Ismétlődő tranzakciók',
        ],
        actionText: 'Első tranzakció hozzáadása',
      ),
      TutorialPageData(
        title: 'Részletes elemzések',
        description: 'Lásd tisztán, mire és mennyit költesz havonta',
        iconData: Icons.analytics,
        color: Color(0xFF2196F3),
        features: [
          'Kategóriánkénti bontás',
          'Trendek és előrejelzések',
          'Havi összehasonlítás',
        ],
        actionText: 'Elemzések megtekintése',
      ),
      TutorialPageData(
        title: 'Költési korlátok',
        description: 'Állíts be havi limiteket és maradj a tervben',
        iconData: Icons.warning_amber,
        color: Color(0xFFFF9800),
        features: [
          'Kategóriánkénti korlátok',
          'Automatikus figyelmeztetések',
          'Havi és heti limitek',
        ],
        actionText: 'Első korlát beállítása',
      ),
    ];
  }

  List<TutorialPageData> _getCommunityDrivenTutorial() {
    return [
      TutorialPageData(
        title: 'Csatlakozz a közösséghez',
        description: 'Oszd meg tapasztalataidat és tanulj másoktól',
        iconData: Icons.people,
        color: Color(0xFF9C27B0),
        features: [
          'Tippek és tapasztalatok',
          'Kérdések és válaszok',
          'Motiváció és támogatás',
        ],
        actionText: 'Fórum böngészése',
      ),
      TutorialPageData(
        title: 'Kihívások és célok',
        description: 'Vegyél részt közös pénzügyi kihívásokban',
        iconData: Icons.emoji_events,
        color: Color(0xFFE91E63),
        features: [
          'Havi megtakarítási kihívások',
          'Közös célok elérése',
          'Jutalmak és elismerések',
        ],
        actionText: 'Kihívás választása',
      ),
      TutorialPageData(
        title: 'Fejlődj együtt másokkal',
        description: 'Motiváld egymást a pénzügyi célok elérésében',
        iconData: Icons.trending_up,
        color: Color(0xFF00BCD4),
        features: [
          'Csoportos kihívások',
          'Tapasztalatok megosztása',
          'Közös sikerek ünneplése',
        ],
        actionText: 'Első csoport keresése',
      ),
    ];
  }

  List<TutorialPageData> _getLearnerTutorial() {
    return [
      TutorialPageData(
        title: 'Pénzügyi tudástár',
        description: 'Tanulj új pénzügyi fogalmakat és stratégiákat',
        iconData: Icons.school,
        color: Color(0xFF3F51B5),
        features: [
          'Interaktív leckék',
          'Gyakorlati példák',
          'Haladás követése',
        ],
        actionText: 'Első lecke indítása',
      ),
      TutorialPageData(
        title: 'Kvízek és tesztek',
        description: 'Teszteld tudásodat és szerezz pontokat',
        iconData: Icons.quiz,
        color: Color(0xFF673AB7),
        features: [
          'Különböző nehézségi szintek',
          'Azonnali visszajelzés',
          'Pontszerzés és szintek',
        ],
        actionText: 'Első kvíz megoldása',
      ),
      TutorialPageData(
        title: 'Személyre szabott tanulás',
        description: 'Az app megtanulja, mi érdekel és ajánl új tartalmakat',
        iconData: Icons.lightbulb,
        color: Color(0xFFFF5722),
        features: [
          'Intelligens ajánlások',
          'Fejlődési terv',
          'Tanulási statisztikák',
        ],
        actionText: 'Tanulási preferenciák',
      ),
    ];
  }

  List<TutorialPageData> _getAdvancedTutorial() {
    return [
      TutorialPageData(
        title: 'Adatimport és automatizálás',
        description: 'Importálj banki adatokat és automatizáld a folyamatokat',
        iconData: Icons.upload_file,
        color: Color(0xFF607D8B),
        features: [
          'CSV és Excel import',
          'Banki kapcsolat (jövőbeli)',
          'Automatikus kategorizálás',
        ],
        actionText: 'Adatok importálása',
      ),
      TutorialPageData(
        title: 'Szabályok és automatizmusok',
        description: 'Hozz létre intelligens szabályokat a tranzakciókhoz',
        iconData: Icons.settings,
        color: Color(0xFF795548),
        features: [
          'Automatikus kategorizálás',
          'Ismétlődő tranzakciók',
          'Feltételes műveletvégzés',
        ],
        actionText: 'Első szabály létrehozása',
      ),
      TutorialPageData(
        title: 'Haladó elemzések',
        description: 'Mélyebb betekintés a pénzügyi szokásaidba',
        iconData: Icons.insights,
        color: Color(0xFF009688),
        features: [
          'Cashflow előrejelzés',
          'Trend analízis',
          'Részletes riportok',
        ],
        actionText: 'Haladó elemzések',
      ),
    ];
  }

  List<TutorialPageData> _getCompetitiveTutorial() {
    return [
      TutorialPageData(
        title: 'Ranglisták és versenyek',
        description: 'Nézd meg, hogyan állsz másokhoz képest',
        iconData: Icons.leaderboard,
        color: Color(0xFFFF6F00),
        features: [
          'Havi rangsorok',
          'Kategória versenyek',
          'Regionális összehasonlítás',
        ],
        actionText: 'Ranglisták megtekintése',
      ),
      TutorialPageData(
        title: 'PTI Index és pontszámok',
        description: 'Kövesd nyomon a pénzügyi teljesítményedet',
        iconData: Icons.speed,
        color: Color(0xFFE65100),
        features: [
          'Személyes PTI pontszám',
          'Havi fejlődés tracking',
          'Benchmarking másokkal',
        ],
        actionText: 'PTI számítás indítása',
      ),
      TutorialPageData(
        title: 'Kihívások és trófeák',
        description: 'Szerezz el különleges elismeréseket',
        iconData: Icons.military_tech,
        color: Color(0xFFBF360C),
        features: [
          'Különleges kihívások',
          'Ritka trófeák',
          'Exkluzív címek',
        ],
        actionText: 'Első trófea szerzése',
      ),
    ];
  }

  void _nextPage() {
    if (_currentPage < _tutorialPages.length - 1) {
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

  // MÓDOSÍTOTT: userId átadása az AddIncomesScreen-nek
  void _navigateToFeature(String actionText, String title) {
    // Képernyő mapping actionText alapján
    if (actionText.contains('tranzakció hozzáadása') || 
        actionText.contains('Első tranzakció')) {
      _navigateToScreenWithUserId(_createAddIncomesScreen, actionText);
      
    } else if (actionText.contains('Elemzések megtekintése') || 
              actionText.contains('elemzések')) {
      // _navigateToScreenWithUserId(_createAnalysisScreen, actionText);
      _navigateToScreenWithUserId(_createAnalysisScreen, actionText);
      
    } else if (actionText.contains('korlát beállítása') || 
              actionText.contains('Első korlát')) {
      // _navigateToScreenWithUserId(_createManageLimitsScreen, actionText);
      _navigateToScreenWithUserId(_createManageLimitsScreen, actionText);
      
    } else if (actionText.contains('Fórum böngészése')) {
      // _navigateToScreenWithUserId(_createForumMainScreen, actionText);
      _navigateToScreenWithUserId(_createForumMainScreen, actionText);
      
    } else if (actionText.contains('Kihívás választása')) {
      // _navigateToScreenWithUserId(_createChallengesScreen, actionText);
      _showComingSoonMessage(actionText);
      
    } else if (actionText.contains('lecke indítása') || 
              actionText.contains('kvíz megoldása') || 
              actionText.contains('Tanulási preferenciák')) {
      // _navigateToScreenWithUserId(_createLearningScreen, actionText);
      _showComingSoonMessage(actionText);
      
    } else if (actionText.contains('Adatok importálása') || 
              actionText.contains('szabály létrehozása') || 
              actionText.contains('Haladó elemzések')) {
      // _navigateToScreenWithUserId(_createAdvancedScreen, actionText);
      _showComingSoonMessage(actionText);
      
    } else if (actionText.contains('Ranglisták') || 
              actionText.contains('PTI számítás') || 
              actionText.contains('trófea szerzése')) {
      // _navigateToScreenWithUserId(_createCompetitiveScreen, actionText);
      _showComingSoonMessage(actionText);
      
    } else {
      _showComingSoonMessage(actionText);
    }
  }

  void _showComingSoonMessage(String actionText) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('$actionText - Hamarosan elérhető!'),
        backgroundColor: Color(0xFF00D4A3),
      ),
    );
  }

  // ÚJ: Hibaüzenet megjelenítése
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
      await _onboardingService.completeOnboarding();
      
      if (mounted) {
        // MÓDOSÍTOTT: Lekért felhasználói adatok használata
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
            content: Text('Bevezetés befejezve! Üdvözlünk a NestCash-ben!'),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba történt: ${e.toString()}'),
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
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Biztos kihagyod?'),
        content: Text('A bevezetés segít megismerni az alkalmazást. Később is elérhető lesz a beállításokban.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Mégse'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              _completeTutorial();
            },
            child: Text('Kihagyom'),
          ),
        ],
      ),
    );
  }

  // Általános navigációs függvény userId-val
  Future<void> _navigateToScreenWithUserId(Widget Function(String userId) screenBuilder, String actionText) async {
    // Ha nincs userId, próbáljuk újra lekérni
    if (_currentUserId == null) {
      _currentUserId = await _authService.getUserId();
    }
    
    // Ha még mindig nincs, hibaüzenet
    if (_currentUserId == null) {
      _showErrorMessage('Nem sikerült betölteni a felhasználói adatokat');
      return;
    }
    
    // Navigálás a képernyőre userId-val
    final targetScreen = screenBuilder(_currentUserId!);
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => targetScreen),
    );
  }

  // Screen factory függvények
  Widget _createAddIncomesScreen(String userId) => AddIncomesScreen(userId: userId);
  Widget _createForumMainScreen(String userId) => ForumMainScreen(userId: userId);
  Widget _createAnalysisScreen(String userId) => AnalysisScreen(
    userId: userId, 
    fromTutorial: true, // ÚJ paraméter
  );
  Widget _createManageLimitsScreen(String userId) => ManageLimitsScreen(userId: userId);
  Widget _createChallengesMainScreen(String userId) => ChallengesMainScreen(userId: userId);
  Widget _createPTIMainScreen(String userId) => PTIMainScreen(userId: userId);
  Widget _createBadgesScreen(String userId) => BadgesScreen(userId: userId);

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
              // Header
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: Icon(Icons.arrow_back, color: Colors.white),
                      onPressed: _currentPage > 0 ? _previousPage : () {
                        Navigator.of(context).pop();
                      },
                    ),
                    Expanded(
                      child: Column(
                        children: [
                          Text(
                            '3. lépés',
                            style: TextStyle(
                              color: Colors.white.withOpacity(0.8),
                              fontSize: 14,
                            ),
                          ),
                          Text(
                            'Bemutató - ${widget.userType.displayName}',
                            style: TextStyle(
                              color: Colors.white,
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
                        'Kihagyás',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.8),
                          fontSize: 16,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Progress Indicator
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
                                  ? Colors.white 
                                  : Colors.white.withOpacity(0.3),
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
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),

              // Content
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

              // Bottom Navigation
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
                            'Vissza',
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
                                    ? 'Következő' 
                                    : 'Indulás!',
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
          
          // Icon
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
          
          // Title
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
          
          // Description
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
          
          // Features
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
          
          // Action Button
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