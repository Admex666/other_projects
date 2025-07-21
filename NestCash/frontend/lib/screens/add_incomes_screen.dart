// frontend/screens/add_incomes_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class AddIncomesScreen extends StatefulWidget {
  final String userId;

  const AddIncomesScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _AddIncomesScreenState createState() => _AddIncomesScreenState();
}

class _AddIncomesScreenState extends State<AddIncomesScreen> {
  final AuthService _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _titleController = TextEditingController();
  final _messageController = TextEditingController();

  String _selectedDate = 'April 30, 2024';
  String _selectedCategory = 'Válassz kategóriát';
  String _selectedCurrency = 'HUF';

  final List<String> _incomeCategories = [
    'Fizetés', 
    'Ajándék', 
    'Befektetés', 
    'Kamat', 
    'Egyéb bevétel'
  ];

  @override
  void initState() {
    super.initState();
    _selectedDate = '${_getMonthName(DateTime.now().month)} ${DateTime.now().day}, ${DateTime.now().year}';
  }

  @override
  void dispose() {
    _amountController.dispose();
    _titleController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _saveIncome() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final amountText = _amountController.text.replaceAll(RegExp(r'[^\d.]'), '');
    final double? amount = double.tryParse(amountText);

    if (amount == null || amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Kérjük érvényes, pozitív összeget adjon meg.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    if (_selectedCategory == 'Válassz kategóriát') {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Kérjük válasszon kategóriát.'),
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
      'osszeg': amount, // Bevételnél pozitív összeg
      'kategoria': _selectedCategory != 'Válassz kategóriát' ? _selectedCategory : null,
      'leiras': _messageController.text.isNotEmpty ? _messageController.text : null,
      'tipus': 'bevetel',
      'bev_kiad_tipus': 'bevetel',
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
            content: Text('Bevétel sikeresen elmentve!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        // Clear fields
        _amountController.clear();
        _titleController.clear();
        _messageController.clear();
        setState(() {
          _selectedCategory = 'Válassz kategóriát';
          _selectedDate = '${_getMonthName(DateTime.now().month)} ${DateTime.now().day}, ${DateTime.now().year}';
        });
      } else {
        final errorData = jsonDecode(resp.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save income: ${errorData['detail'] ?? resp.statusCode}'),
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
                      color: value == 'Válassz kategóriát' 
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
      initialDate: DateTime.now(),
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
        return Container(
          padding: EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Kategória kiválasztása',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              ..._incomeCategories.map((category) => ListTile(
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
                'Deviza kiválasztása',
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
            mainAxisSize: MainAxisSize.max,
            children: [
              // Header rész (ez marad a gradiens háttéren)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back, color: Colors.black87),
                      onPressed: () {
                        Navigator.pop(context);
                      },
                    ),
                    Expanded(
                      child: Text(
                        'Bevétel hozzáadása',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),

              // Form Container (ez lesz a fehér, lekerekített sarkú rész)
              Expanded(
                child: Container(
                  margin: EdgeInsets.symmetric(horizontal: 0),
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

                          // Currency Dropdown
                          _buildDropdownField(
                            label: 'Deviza',
                            value: _selectedCurrency,
                            onTap: _selectCurrency,
                          ),

                          SizedBox(height: 16),

                          // Income Title Field
                          _buildInputField(
                            label: 'Bevétel neve',
                            controller: _titleController,
                            hintText: 'Fizetés',
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
                                    hintText: 'Adj megjegyzést ehhez a bevételhez...',
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
                              onPressed: _saveIncome,
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