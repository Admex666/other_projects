// lib/screens/knowledge/lesson_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/services/auth_service.dart';

class LessonDetailScreen extends StatefulWidget {
  final String lessonId;
  final String userId;

  const LessonDetailScreen({
    Key? key,
    required this.lessonId,
    required this.userId,
  }) : super(key: key);

  @override
  _LessonDetailScreenState createState() => _LessonDetailScreenState();
}

class _LessonDetailScreenState extends State<LessonDetailScreen> {
  final AuthService _authService = const AuthService();
  LessonDetail? lesson;
  LessonCompletion? completion;
  bool isLoading = true;
  PageController pageController = PageController();
  int currentPageIndex = 0;
  bool showQuiz = false;
  List<List<int>> quizAnswers = [];

  @override
  void initState() {
    super.initState();
    _loadLessonDetail();
  }

  Future<void> _loadLessonDetail() async {
    setState(() => isLoading = true);
    
    try {
      final token = await _authService.getToken();

      final response = await http.get(
        Uri.parse('${_authService.baseUrl}/knowledge/lessons/${widget.lessonId}'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        print('Raw response: ${response.body}'); // ÚJ SOR - ez mutatja a tényleges választ
        final data = json.decode(response.body);
        print('Parsed data keys: ${data.keys}'); // ÚJ SOR - ez mutatja a kulcsokat
        setState(() {
          lesson = LessonDetail.fromJson(data['lesson']);
          completion = data['completion'] != null 
              ? LessonCompletion.fromJson(data['completion'])
              : null;
          
          // Kvíz válaszok inicializálása
          if (lesson!.quizQuestions.isNotEmpty) {
            quizAnswers = List.generate(
              lesson!.quizQuestions.length,
              (index) => <int>[],
            );
          }
        });
      } else {
        throw Exception('Failed to load lesson');
      }
    } catch (e) {
      print('Error loading lesson: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Hiba a lecke betöltésekor')),
      );
    } finally {
      setState(() => isLoading = false);
    }
  }

  Future<void> _updateProgress() async {
    if (lesson == null) return;

    final token = await _authService.getToken();

    final progressData = {
      'pages_completed': showQuiz ? lesson!.pages.length : currentPageIndex + 1,
      'total_pages': lesson!.pages.length,
    };

    await http.post(
      Uri.parse('${_authService.baseUrl}/knowledge/lessons/${widget.lessonId}/progress'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: json.encode(progressData),
    );
  }

  Future<void> _submitQuiz() async {
    if (lesson == null || quizAnswers.isEmpty) return;

    final token = await _authService.getToken();

    final quizData = {
      'answers': quizAnswers,
    };

    try {
      final response = await http.post(
        Uri.parse('${_authService.baseUrl}/knowledge/lessons/${widget.lessonId}/quiz'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: json.encode(quizData),
      );

      if (response.statusCode == 200) {
        final result = QuizResult.fromJson(json.decode(response.body));
        _showQuizResult(result);
      } else {
        throw Exception('Failed to submit quiz');
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Hiba a kvíz beküldésekor')),
      );
    }
  }

  void _showQuizResult(QuizResult result) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Column(
          children: [
            Icon(
              result.score >= 70 ? Icons.celebration : Icons.sentiment_dissatisfied,
              size: 64,
              color: result.score >= 70 ? Colors.green : Colors.orange,
            ),
            const SizedBox(height: 8),
            Text(
              result.score >= 70 ? 'Szuper!' : 'Folytatni kell!',
              style: TextStyle(
                color: result.score >= 70 ? Colors.green : Colors.orange,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Eredményed: ${result.score}%',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '${result.correctAnswers}/${result.totalQuestions} helyes válasz',
              style: const TextStyle(fontSize: 16),
            ),
            if (result.feedback != null) ...[
              const SizedBox(height: 16),
              Text(
                result.feedback!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14, color: Colors.grey),
              ),
            ],
          ],
        ),
        actions: [
          if (result.score < 70)
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                setState(() {
                  showQuiz = false;
                  currentPageIndex = 0;
                  quizAnswers = List.generate(
                    lesson!.quizQuestions.length,
                    (index) => <int>[],
                  );
                });
                pageController.animateToPage(
                  0,
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeInOut,
                );
              },
              child: const Text('Újra tanulás'),
            ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00D4A3),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Text(
              'Befejezés',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        backgroundColor: const Color(0xFFF5F7FA),
        appBar: AppBar(
          backgroundColor: const Color(0xFF00D4A3),
          elevation: 0,
          title: const Text( // Changed to a static title or a loading indicator
            'Lecke betöltése...', // Or an empty Text('')
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: const Center(
          child: CircularProgressIndicator(color: Color(0xFF00D4A3)),
        ),
      );
    }

    if (lesson == null) {
      return Scaffold(
        backgroundColor: const Color(0xFFF5F7FA),
        appBar: AppBar(
          backgroundColor: const Color(0xFF00D4A3),
          title: const Text('Hiba', style: TextStyle(color: Colors.white)),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        body: const Center(
          child: Text('Nem sikerült betölteni a leckét'),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFF00D4A3),
        title: Center(
          child: Text(
            lesson!.title,
            style: const TextStyle(color: Colors.black87, fontSize: 20),
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          if (!showQuiz)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Text(
                  '${currentPageIndex + 1}/${lesson!.pages.length}',
                  style: const TextStyle(color: Colors.black87, fontSize: 16),
                ),
              ),
            ),
        ],
      ),
      body: showQuiz ? _buildQuizView() : _buildLessonView(),
      bottomNavigationBar: _buildBottomNavigation(),
    );
  }

  Widget _buildLessonView() {
    return PageView.builder(
      controller: pageController,
      onPageChanged: (index) {
        setState(() {
          currentPageIndex = index;
        });
        _updateProgress();
      },
      itemCount: lesson!.pages.length,
      itemBuilder: (context, index) {
        final page = lesson!.pages[index];
        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progress indicator
              Container(
                margin: const EdgeInsets.only(bottom: 20),
                child: LinearProgressIndicator(
                  value: (currentPageIndex + 1) / lesson!.pages.length,
                  backgroundColor: Colors.grey[200],
                  valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
                  minHeight: 6,
                ),
              ),
              
              // Page content card
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.08),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header with page info
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
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              'Oldal ${index + 1}/${lesson!.pages.length}',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                          ),
                          const Spacer(),
                          Icon(
                            lesson!.difficulty == 'beginner' ? Icons.school : Icons.psychology,
                            color: Colors.white,
                            size: 20,
                          ),
                        ],
                      ),
                    ),
                    
                    // Content
                    Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (page.title != null) ...[
                            Text(
                              page.title!,
                              style: const TextStyle(
                                fontSize: 28,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1A202C),
                                height: 1.2,
                              ),
                            ),
                            const SizedBox(height: 20),
                            Container(
                              height: 3,
                              width: 60,
                              decoration: BoxDecoration(
                                color: const Color(0xFF00D4A3),
                                borderRadius: BorderRadius.circular(2),
                              ),
                            ),
                            const SizedBox(height: 24),
                          ],
                          
                          // Formatted content
                          _buildFormattedContent(page.content),
                          
                          if (page.imageUrl != null) ...[
                            const SizedBox(height: 24),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(16),
                              child: Container(
                                decoration: BoxDecoration(
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.1),
                                      blurRadius: 10,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                                ),
                                child: Image.network(
                                  page.imageUrl!,
                                  width: double.infinity,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) => Container(
                                    height: 200,
                                    decoration: BoxDecoration(
                                      color: Colors.grey[100],
                                      borderRadius: BorderRadius.circular(16),
                                    ),
                                    child: Column(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Icon(
                                          Icons.image_not_supported_outlined,
                                          size: 48,
                                          color: Colors.grey[400],
                                        ),
                                        const SizedBox(height: 8),
                                        Text(
                                          'Kép nem tölthető be',
                                          style: TextStyle(
                                            color: Colors.grey[600],
                                            fontSize: 14,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              
              // Reading time estimate
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: const Color(0xFF00D4A3).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: const Color(0xFF00D4A3).withOpacity(0.3),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.schedule,
                      size: 16,
                      color: Color(0xFF00D4A3),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Becsült olvasási idő: ${_estimateReadingTime(page.content)} perc',
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFF00D4A3),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildFormattedContent(String content) {
  // Egyszerű formázás - bekezdések és felsorolások kezelése
  final paragraphs = content.split('\n\n');
  
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: paragraphs.map((paragraph) {
      if (paragraph.trim().isEmpty) return const SizedBox.shrink();
      
      // Lista elemek kezelése
      if (paragraph.startsWith('•') || paragraph.startsWith('-') || paragraph.startsWith('*')) {
        return _buildListItem(paragraph);
      }
      
      // Címek kezelése (ha # jellel kezdődik)
      if (paragraph.startsWith('#')) {
        return _buildHeading(paragraph);
      }
      
      // Normál bekezdés
      return Container(
        margin: const EdgeInsets.only(bottom: 16),
        child: Text(
          paragraph.trim(),
          style: const TextStyle(
            fontSize: 16,
            height: 1.7,
            color: Color(0xFF2D3748),
            letterSpacing: 0.3,
          ),
          textAlign: TextAlign.justify,
        ),
      );
    }).toList(),
  );
}

Widget _buildListItem(String item) {
    final cleanItem = item.replaceFirst(RegExp(r'^[•\-*]\s*'), '');
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 6, right: 12),
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              color: Color(0xFF00D4A3),
              shape: BoxShape.circle,
            ),
          ),
          Expanded(
            child: Text(
              cleanItem,
              style: const TextStyle(
                fontSize: 16,
                height: 1.6,
                color: Color(0xFF2D3748),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeading(String heading) {
    final cleanHeading = heading.replaceFirst(RegExp(r'^#+\s*'), '');
    final level = heading.indexOf(' ');
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16, top: 8),
      child: Text(
        cleanHeading,
        style: TextStyle(
          fontSize: level <= 2 ? 22 : 18,
          fontWeight: FontWeight.bold,
          color: const Color(0xFF1A202C),
          height: 1.3,
        ),
      ),
    );
  }

  int _estimateReadingTime(String content) {
    final wordCount = content.split(RegExp(r'\s+')).length;
    final readingTime = (wordCount / 200).ceil(); // 200 szó/perc átlag
    return readingTime < 1 ? 1 : readingTime;
  }

  Widget _buildQuizView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF00D4A3), Color(0xFF00B894)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Column(
              children: [
                Icon(Icons.quiz, size: 48, color: Colors.white),
                SizedBox(height: 8),
                Text(
                  'Kvíz ideje!',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Text(
                  'Teszteld a tudásod!',
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.white70,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          ...lesson!.quizQuestions.asMap().entries.map((entry) {
            final index = entry.key;
            final question = entry.value;
            return _buildQuizQuestion(question, index);
          }).toList(),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _canSubmitQuiz() ? _submitQuiz : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00D4A3),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(15),
                ),
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text(
                'Kvíz beküldése',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuizQuestion(QuizQuestion question, int questionIndex) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
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
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: const BoxDecoration(
                  color: Color(0xFF00D4A3),
                  shape: BoxShape.circle,
                ),
                child: Text(
                  '${questionIndex + 1}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  question.question,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF2D3748),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...question.options.asMap().entries.map((entry) {
            final optionIndex = entry.key;
            final option = entry.value;
            final isSelected = quizAnswers[questionIndex].contains(optionIndex);
            
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  borderRadius: BorderRadius.circular(10),
                  onTap: () {
                    setState(() {
                      if (question.isMultipleChoice) {
                        if (isSelected) {
                          quizAnswers[questionIndex].remove(optionIndex);
                        } else {
                          quizAnswers[questionIndex].add(optionIndex);
                        }
                      } else {
                        quizAnswers[questionIndex] = [optionIndex];
                      }
                    });
                  },
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: isSelected ? const Color(0xFF00D4A3) : Colors.grey[300]!,
                        width: 2,
                      ),
                      borderRadius: BorderRadius.circular(10),
                      color: isSelected ? const Color(0xFF00D4A3).withOpacity(0.1) : Colors.transparent,
                    ),
                    child: Row(
                      children: [
                        Icon(
                          question.isMultipleChoice 
                              ? (isSelected ? Icons.check_box : Icons.check_box_outline_blank)
                              : (isSelected ? Icons.radio_button_checked : Icons.radio_button_unchecked),
                          color: isSelected ? const Color(0xFF00D4A3) : Colors.grey[600],
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            option,
                            style: TextStyle(
                              fontSize: 16,
                              color: isSelected ? const Color(0xFF00D4A3) : const Color(0xFF2D3748),
                              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildBottomNavigation() {
    if (showQuiz) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, -8),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            if (currentPageIndex > 0) ...[
              Expanded(
                flex: 1,
                child: ElevatedButton.icon(
                  onPressed: () {
                    pageController.previousPage(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeInOut,
                    );
                  },
                  icon: const Icon(Icons.arrow_back_ios, color: Colors.white, size: 18),
                  label: const Text('Előző', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.grey[400],
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    elevation: 0,
                  ),
                ),
              ),
              const SizedBox(width: 12),
            ],
            Expanded(
              flex: 2,
              child: ElevatedButton.icon(
                onPressed: _getNextButtonAction(),
                icon: Icon(_getNextButtonIcon(), color: Colors.white, size: 18),
                label: Text(
                  _getNextButtonText(),
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00D4A3),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  elevation: 0,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  VoidCallback? _getNextButtonAction() {
    if (currentPageIndex < lesson!.pages.length - 1) {
      return () {
        pageController.nextPage(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
      };
    } else if (lesson!.quizQuestions.isNotEmpty) {
      return () {
        setState(() {
          showQuiz = true;
        });
      };
    } else {
      return () {
        Navigator.pop(context);
      };
    }
  }

  IconData _getNextButtonIcon() {
    if (currentPageIndex < lesson!.pages.length - 1) {
      return Icons.arrow_forward;
    } else if (lesson!.quizQuestions.isNotEmpty) {
      return Icons.quiz;
    } else {
      return Icons.check;
    }
  }

  String _getNextButtonText() {
    if (currentPageIndex < lesson!.pages.length - 1) {
      return 'Következő';
    } else if (lesson!.quizQuestions.isNotEmpty) {
      return 'Kvíz';
    } else {
      return 'Befejezés';
    }
  }

  bool _canSubmitQuiz() {
    for (int i = 0; i < lesson!.quizQuestions.length; i++) {
      if (quizAnswers[i].isEmpty) {
        return false;
      }
    }
    return true;
  }
}

// Model osztályok - javított verzió
class LessonDetail {
  final String id;
  final String title;
  final String? description;
  final String difficulty;
  final int estimatedMinutes;
  final List<LessonPage> pages;
  final List<QuizQuestion> quizQuestions;
  final String categoryName;

  LessonDetail({
    required this.id,
    required this.title,
    this.description,
    required this.difficulty,
    required this.estimatedMinutes,
    required this.pages,
    required this.quizQuestions,
    required this.categoryName,
  });

  factory LessonDetail.fromJson(Map<String, dynamic> json) {
    return LessonDetail(
      id: _parseId(json['id']),
      title: json['title'] ?? '',
      description: json['description'],
      difficulty: json['difficulty'] ?? 'beginner',
      estimatedMinutes: _parseInt(json['estimated_minutes']),
      pages: (json['pages'] as List? ?? [])
          .map((page) => LessonPage.fromJson(page))
          .toList(),
      quizQuestions: (json['quiz_questions'] as List? ?? [])
          .map((question) => QuizQuestion.fromJson(question))
          .toList(),
      categoryName: json['category_name'] ?? '',
    );
  }

  static String _parseId(dynamic id) {
    if (id == null) return '';
    if (id is String) return id;
    if (id is Map && id.isEmpty) return '';
    if (id is Map && id.containsKey('\$oid')) return id['\$oid'];
    return id.toString();
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
}

class LessonPage {
  final int pageNumber;
  final String? title;
  final String content;
  final String? imageUrl;

  LessonPage({
    required this.pageNumber,
    this.title,
    required this.content,
    this.imageUrl,
  });

  factory LessonPage.fromJson(Map<String, dynamic> json) {
    return LessonPage(
      pageNumber: _parseInt(json['page_number'] ?? json['order']),
      title: json['title'],
      content: json['content'] ?? '',
      imageUrl: json['image_url'],
    );
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
}

class QuizQuestion {
  final String question;
  final List<String> options;
  final bool isMultipleChoice;

  QuizQuestion({
    required this.question,
    required this.options,
    required this.isMultipleChoice,
  });

  factory QuizQuestion.fromJson(Map<String, dynamic> json) {
    return QuizQuestion(
      question: json['question'] ?? '',
      options: _parseStringList(json['options']),
      isMultipleChoice: _parseMultipleChoice(json),
    );
  }

  static List<String> _parseStringList(dynamic value) {
    if (value == null) return [];
    if (value is List) {
      return value.map((item) => item?.toString() ?? '').toList();
    }
    return [];
  }

  static bool _parseMultipleChoice(Map<String, dynamic> json) {
    // Ha van is_multiple_choice mező, használjuk azt
    if (json.containsKey('is_multiple_choice')) {
      return json['is_multiple_choice'] == true;
    }
    
    // Ha nincs, akkor a type alapján döntünk
    if (json.containsKey('type')) {
      return json['type'] == 'multiple_choice';
    }
    
    // Alapértelmezett: egyszeres választás
    return false;
  }
}

class LessonCompletion {
  final bool isCompleted;
  final int pagesCompleted;
  final int? quizScore;
  final DateTime? completedAt;

  LessonCompletion({
    required this.isCompleted,
    required this.pagesCompleted,
    this.quizScore,
    this.completedAt,
  });

  factory LessonCompletion.fromJson(Map<String, dynamic> json) {
    return LessonCompletion(
      isCompleted: json['is_completed'] == true,
      pagesCompleted: _parseInt(json['pages_completed']),
      quizScore: json['quiz_score'] != null ? _parseInt(json['quiz_score']) : null,
      completedAt: json['completed_at'] != null 
          ? DateTime.tryParse(json['completed_at'].toString())
          : null,
    );
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
}

class QuizResult {
  final int score;
  final int correctAnswers;
  final int totalQuestions;
  final String? feedback;
  final bool passed;

  QuizResult({
    required this.score,
    required this.correctAnswers,
    required this.totalQuestions,
    this.feedback,
    required this.passed,
  });

  factory QuizResult.fromJson(Map<String, dynamic> json) {
    return QuizResult(
      score: _parseInt(json['score']),
      correctAnswers: _parseInt(json['correct_answers']),
      totalQuestions: _parseInt(json['total_questions']),
      feedback: json['feedback'],
      passed: json['passed'] == true,
    );
  }

  static int _parseInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
}