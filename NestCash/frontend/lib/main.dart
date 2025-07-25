import 'package:flutter/material.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:frontend/screens/dashboard_screen.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/profile/profile_screen.dart';
import 'package:frontend/screens/add_incomes_screen.dart';
import 'package:frontend/screens/manage_accounts_screen.dart'; 
import 'package:frontend/screens/manage_categories_screen.dart';
import 'package:frontend/screens/knowledge/knowledge_screen.dart';
import 'package:frontend/screens/analysis_screen.dart';
import 'package:frontend/screens/forum/forum_main_screen.dart';
import 'package:frontend/widgets/notification_badge.dart';
import 'package:frontend/screens/manage_limits_screen.dart';
import 'package:frontend/screens/challenges/challenges_main_screen.dart';
import 'package:frontend/screens/habits/habits_main_screen.dart';

void main() {
  runApp(NestCashApp());
}

class NestCashApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NestCash',
      theme: ThemeData(primarySwatch: Colors.teal),
      home: AuthWrapper(),
    );
  }
}

// Global navigation
class MainScreen extends StatefulWidget {
  final String username;
  final String userId;

  const MainScreen({required this.username, required this.userId});

  @override
  _MainScreenState createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;

  late final List<Widget> _widgetOptions;

  @override
  void initState() {
    super.initState();
    _widgetOptions = <Widget>[
      DashboardScreen(username: widget.username),
      AnalysisScreen(userId: widget.userId),
      const SizedBox.shrink(),
      ForumMainScreen(userId: widget.userId, username: widget.username,),
      KnowledgeScreen(userId: widget.userId),
      ProfileScreen(username: widget.username, userId: widget.userId),
    ];
  }

  void _onItemTapped(int index) {
    if (index == 2) {
      _showAddTransactionOptions(context);
    } else if (index == 3) {
      _showForumChallengesOptions(context);
    } else {
      setState(() {
        _selectedIndex = index;
      });
    }
  }

  // Módosítsd a _showAddTransactionOptions metódust a main.dart fájlban
void _showAddTransactionOptions(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (BuildContext bc) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            // Bevétel gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => AddIncomesScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.add, color: Colors.white),
                label: const Text(
                  'Bevétel hozzáadása',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00D4A3),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Költség gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => AddExpensesScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.remove, color: Colors.white),
                label: const Text(
                  'Kiadás hozzáadása',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.redAccent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Számlák kezelése gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ManageAccountsScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.account_balance_wallet, color: Colors.white),
                label: const Text(
                  'Számlák kezelése',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blueAccent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Kategóriák kezelése gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ManageCategoriesScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.category, color: Colors.white),
                label: const Text(
                  'Kategóriák kezelése',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purpleAccent,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Limitek kezelése gomb (ÚJ)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ManageLimitsScreen(userId: widget.userId),
                    ),
                  );
                },
                icon: const Icon(Icons.speed, color: Colors.white),
                label: const Text(
                  'Limitek kezelése',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            
            const SizedBox(height: 15),
            // Szokások gomb (ÚJ)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => HabitsMainScreen(
                        userId: widget.userId,
                        username: widget.username,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.psychology, color: Colors.white),
                label: const Text(
                  'Szokások kezelése',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.teal,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
          ],
        ),
      );
    },
  );
}

void _showForumChallengesOptions(BuildContext context) {
  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (BuildContext bc) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            // Fórum gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  setState(() {
                    _selectedIndex = 3;
                  });
                },
                icon: const Icon(Icons.forum, color: Colors.white),
                label: const Text(
                  'Fórum',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00D4A3),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
            const SizedBox(height: 15),
            // Kihívások gomb
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ChallengesMainScreen(
                        userId: widget.userId,
                        username: widget.username,
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.emoji_events, color: Colors.white),
                label: const Text(
                  'Kihívások',
                  style: TextStyle(fontSize: 18, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),
          ],
        ),
      );
    },
  );
}

@override
Widget build(BuildContext context) {
  return Scaffold(
    appBar: _selectedIndex != 2 ? AppBar(
      backgroundColor: const Color(0xFF00D4A3),
      elevation: 0,
      automaticallyImplyLeading: false,
      title: Text(
        _getScreenTitle(_selectedIndex),
        style: const TextStyle(
          color: Colors.black,
          fontWeight: FontWeight.bold,
        ),
      ),
      actions: [
        AppBarNotificationBadge(userId: widget.userId),
      ],
    ) : null,
    body: _widgetOptions.elementAt(_selectedIndex),
      bottomNavigationBar: Container(
        padding: EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: Color(0xFFF0F8F0),
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(20),
            topRight: Radius.circular(20),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _buildNavItem(Icons.home_outlined, 0),
            _buildNavItem(Icons.bar_chart_outlined, 1),
            _buildNavItem(Icons.swap_horiz_outlined, 2),
            _buildNavItem(Icons.forum_outlined, 3),
            _buildNavItem(Icons.school_outlined, 4),
            _buildNavItem(Icons.person_outline, 5),
          ],
        ),
      ),
    );
  }

  // Helper method hozzáadása a screen címekhez:
String _getScreenTitle(int index) {
    switch (index) {
      case 0:
        return 'Üdv újra, ${widget.username}!';
      case 1:
        return 'Elemzések';
      case 3:
        return 'Fórum';
      case 4:
        return 'Tudástár';
      case 5:
        return 'Profil';
      default:
        return 'NestCash';
    }
  }

  Widget _buildNavItem(IconData icon, int index) {
    bool isSelected = index == _selectedIndex;
    return GestureDetector(
      onTap: () => _onItemTapped(index),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected && index != 2 ? const Color(0xFF00D4A3) : Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: isSelected && index != 2 ? Colors.white : Colors.grey[600],
          size: 26,
        ),
      ),
    );
  }
}