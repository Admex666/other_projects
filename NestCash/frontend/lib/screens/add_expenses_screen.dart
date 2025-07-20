// add_expenses_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/auth_service.dart'; // Add this import
import 'package:http/http.dart' as http; // Add this import
import 'dart:convert'; // Add this import

class AddExpensesScreen extends StatefulWidget {
  @override
  _AddExpensesScreenState createState() => _AddExpensesScreenState();
}

class _AddExpensesScreenState extends State<AddExpensesScreen> {
  final AuthService _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _titleController = TextEditingController();
  final _messageController = TextEditingController();
  
  String _selectedDate = 'April 30, 2024';
  String _selectedCategory = 'Válassz kategóriát';
  String _selectedCurrency = 'HUF';

  Future<void> _saveExpense() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final amountText = _amountController.text.replaceAll(RegExp(r'[^\d.]'), '');
    final double? amount = double.tryParse(amountText);

    if (amount == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Please enter a valid amount.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    final token = await _authService.getToken();
    if (token == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Authentication token not found. Please log in again.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    final transactionData = {
      'datum': DateTime.now().toIso8601String().split('T')[0], // YYYY-MM-DD format
      'osszeg': -amount, // Assuming expenses are negative
      'kategoria': _selectedCategory != 'Select the category' ? _selectedCategory : null,
      'leiras': _messageController.text.isNotEmpty ? _messageController.text : null,
      'tipus': 'kiadas',
      'bev_kiad_tipus': 'kiadas',
      'deviza': _selectedCurrency,
    };

    try {
      final resp = await http.post(
        Uri.parse('${_authService.baseUrl}/transactions/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(transactionData),
      );

      if (resp.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Expense saved successfully!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        // Optionally clear fields or navigate back
        _amountController.clear();
        _titleController.clear();
        _messageController.clear();
        setState(() {
          _selectedCategory = 'Select the category';
          _selectedDate = '${_getMonthName(DateTime.now().month)} ${DateTime.now().day}, ${DateTime.now().year}';
        });
      } else {
        final errorData = jsonDecode(resp.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save expense: ${errorData['detail'] ?? resp.statusCode}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('An error occurred: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  void dispose() {
    _amountController.dispose();
    _titleController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Widget _buildInputField({
    required String label,
    required TextEditingController controller,
    String? hintText,
    Widget? suffixIcon,
    int maxLines = 1,
    bool readOnly = false,
    VoidCallback? onTap,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.black87,
          ),
        ),
        SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Color(0xFFE8F5E8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: TextFormField(
            controller: controller,
            readOnly: readOnly,
            onTap: onTap,
            maxLines: maxLines,
            style: TextStyle(
              fontSize: 16,
              color: Colors.black87,
            ),
            decoration: InputDecoration(
              hintText: hintText,
              hintStyle: TextStyle(
                color: Colors.grey[600],
                fontSize: 16,
              ),
              border: InputBorder.none,
              contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              suffixIcon: suffixIcon,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDropdownField({
    required String label,
    required String value,
    required VoidCallback onTap,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.black87,
          ),
        ),
        SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Color(0xFFE8F5E8),
            borderRadius: BorderRadius.circular(12),
          ),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    value,
                    style: TextStyle(
                      fontSize: 16,
                      color: value == 'Select the category' 
                          ? Colors.grey[600] 
                          : Colors.black87,
                    ),
                  ),
                  Icon(
                    Icons.keyboard_arrow_down,
                    color: Color(0xFF00D4AA),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _selectDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime(2024, 4, 30),
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = '${_getMonthName(picked.month)} ${picked.day}, ${picked.year}';
      });
    }
  }

  void _selectCategory() {
    showModalBottomSheet(
      context: context,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        final categories = [
          'Food & Dining',
          'Transportation',
          'Shopping',
          'Entertainment',
          'Bills & Utilities',
          'Healthcare',
          'Education',
          'Travel',
          'Other'
        ];
        
        return Container(
          padding: EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Select Category',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              ...categories.map((category) => ListTile(
                title: Text(category),
                onTap: () {
                  setState(() {
                    _selectedCategory = category;
                  });
                  Navigator.pop(context);
                },
              )),
            ],
          ),
        );
      },
    );
  }

  void _selectCurrency() {
    showModalBottomSheet(
      context: context,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        final currencies = [
          'HUF',
          'EUR',
          'USD', 
        ];
        
        return Container(
          padding: EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Select Currency',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              ...currencies.map((currency) => ListTile(
                title: Text(currency),
                onTap: () {
                  setState(() {
                    _selectedCurrency = currency;
                  });
                  Navigator.pop(context);
                },
              )),
            ],
          ),
        );
      },
    );
  }

  String _getMonthName(int month) {
    const months = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months[month - 1];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // A Scaffold háttérszíne most már nem szükséges, mivel a body egy gradiens Container lesz
      // backgroundColor: Color(0xFF00D4AA), // Ezt a sort töröld vagy kommenteld ki

      body: SafeArea(
        child: Container(
          decoration: BoxDecoration(
            // Gradiens háttér, mint a Dashboard tetején
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xFF00D4A3), // A Dashboard tetejének színe
                Color(0xFFE8F6F3), // A Dashboard aljának színe
              ],
              stops: [0.0, 0.4],
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.max, // Fontos: a Column kitölti a rendelkezésre álló magasságot
            children: [
              // Header rész (ez marad a gradiens háttéren)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Költés hozzáadása',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87, // Marad fekete, vagy változtatható fehérre
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),

              // Form Container (ez lesz a fehér, lekerekített sarkú rész)
              Expanded( // Expanded-be tesszük, hogy kitöltse a maradék helyet
                child: Container(
                  margin: EdgeInsets.symmetric(horizontal: 0), // Eltávolítjuk a margin-t
                  decoration: BoxDecoration(
                    color: Color(0xFFF5F5F5), // Fehér vagy világosszürke háttér
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(30),
                      topRight: Radius.circular(30),
                    ),
                  ),
                  child: SingleChildScrollView(
                    padding: EdgeInsets.all(24),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          SizedBox(height: 16),

                          // Date Field
                          _buildInputField(
                            label: 'Dátum',
                            controller: TextEditingController(text: _selectedDate),
                            readOnly: true,
                            onTap: _selectDate,
                            suffixIcon: Icon(
                              Icons.calendar_today,
                              color: Color(0xFF00D4AA),
                              size: 20,
                            ),
                          ),

                          SizedBox(height: 16),

                          // Category Dropdown
                          _buildDropdownField(
                            label: 'Kategória',
                            value: _selectedCategory,
                            onTap: _selectCategory,
                          ),

                          SizedBox(height: 16),

                          // Amount Field
                          _buildInputField(
                            label: 'Összeg',
                            controller: _amountController,
                            hintText: '0.00',
                          ),

                          SizedBox(height: 16),

                          // Deviza Dropdown (feltételezve, hogy már hozzáadtad a _buildDropdownField-et a deviza kezeléséhez)
                          _buildDropdownField(
                            label: 'Deviza',
                            value: _selectedCurrency,
                            onTap: _selectCurrency,
                          ),

                          SizedBox(height: 16),

                          // Expense Title Field
                          _buildInputField(
                            label: 'Költség neve',
                            controller: _titleController,
                            hintText: 'Vacsora',
                          ),

                          SizedBox(height: 16),

                          // Message Field
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Megjegyzés',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                  color: Color(0xFF00D4AA),
                                ),
                              ),
                              SizedBox(height: 8),
                              Container(
                                height: 70,
                                decoration: BoxDecoration(
                                  color: Color(0xFFE8F5E8),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: TextFormField(
                                  controller: _messageController,
                                  maxLines: 6,
                                  style: TextStyle(
                                    fontSize: 16,
                                    color: Colors.black87,
                                  ),
                                  decoration: InputDecoration(
                                    hintText: 'Adj megjegyzést ehhez a költéshez...',
                                    hintStyle: TextStyle(
                                      color: Colors.grey[600],
                                      fontSize: 16,
                                    ),
                                    border: InputBorder.none,
                                    contentPadding: EdgeInsets.all(16),
                                  ),
                                ),
                              ),
                            ],
                          ),

                          SizedBox(height: 40),

                          // Save Button
                          Container(
                            width: double.infinity,
                            height: 56,
                            child: ElevatedButton(
                              onPressed: _saveExpense,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Color(0xFF00D4AA),
                                foregroundColor: Colors.white,
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                              ),
                              child: Text(
                                'Mentés',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),

                          SizedBox(height: 30),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}