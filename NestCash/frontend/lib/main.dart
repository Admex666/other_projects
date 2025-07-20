import 'package:flutter/material.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:frontend/screens/auth/login_screen.dart';
import 'package:frontend/screens/dashboard_screen.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/profile/profile_screen.dart';  

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

  // List of widgets to display in the body
  late final List<Widget> _widgetOptions;

  @override
  void initState() {
    super.initState();
    _widgetOptions = <Widget>[
      DashboardScreen(username: widget.username),
      Text('Statistics Screen'), // Placeholder for Statistics
      AddExpensesScreen(), // Your Add Expenses Screen
      Text('Layers Screen'), // Placeholder for Layers
      ProfileScreen(username: widget.username, userId: widget.userId), // Your Profile Screen
    ];
  }

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _widgetOptions.elementAt(_selectedIndex), // Display the selected screen
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
            _buildNavItem(Icons.layers_outlined, 3),
            _buildNavItem(Icons.person_outline, 4),
          ],
        ),
      ),
    );
  }

  Widget _buildNavItem(IconData icon, int index) {
    bool isSelected = index == _selectedIndex;
    return GestureDetector(
      onTap: () => _onItemTapped(index),
      child: Container(
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected ? Color(0xFF00D4A3) : Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: isSelected ? Colors.white : Colors.grey[600],
          size: 24,
        ),
      ),
    );
  }
}