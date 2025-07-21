import 'package:flutter/material.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:frontend/screens/dashboard_screen.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/profile/profile_screen.dart';  
import 'package:frontend/screens/add_incomes_screen.dart';

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
      const SizedBox.shrink(), // Your Add Expenses Screen
      Text('Layers Screen'), // Placeholder for Layers
      ProfileScreen(username: widget.username, userId: widget.userId), // Your Profile Screen
    ];
  }

  void _onItemTapped(int index) {
    if (index == 2) { // Ha a "swap_horiz" ikonra kattintott
      _showAddTransactionOptions(context);
    } else {
      setState(() {
        _selectedIndex = index;
      });
    }
  }

  void _showAddTransactionOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent, // Átlátszó háttér a lekerekített sarkokhoz
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
            mainAxisSize: MainAxisSize.min, // A tartalomhoz igazodik
            children: <Widget>[
              // Bevétel gomb
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(context); // Bezárjuk a bottom sheet-et
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
                    backgroundColor: const Color(0xFF00D4A3), // Zöld szín
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
                    Navigator.pop(context); // Bezárjuk a bottom sheet-et
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
                    backgroundColor: Colors.redAccent, // Piros szín
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
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected && index != 2 ? const Color(0xFF00D4A3) : Colors.transparent,
          // A "swap_horiz" ikon ne legyen zölden kiemelve, ha rákattintunk,
          // mert az nem egy képernyőre visz, hanem egy felugró menüt nyit meg.
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