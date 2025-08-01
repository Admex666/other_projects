// lib/screens/edit_transaction_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/services/transaction_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/models/category.dart';
import 'package:frontend/services/category_service.dart';
import 'package:intl/intl.dart';

class EditTransactionScreen extends StatefulWidget {
  final String userId;
  final Map<String, dynamic> transaction;
  final bool isExpense;

  const EditTransactionScreen({
    Key? key,
    required this.userId,
    required this.transaction,
    required this.isExpense,
  }) : super(key: key);

  @override
  _EditTransactionScreenState createState() => _EditTransactionScreenState();
}

class _EditTransactionScreenState extends State<EditTransactionScreen> {
  final AuthService _authService = AuthService();
  final TransactionService _transactionService = TransactionService();
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _titleController = TextEditingController();

  late DateTime _selectedDate;
  
  Map<String, dynamic>? _accountsData;
  String? _selectedMainAccount;
  String? _selectedSubAccount;
  List<String> _mainAccountKeys = [];
  List<String> _subAccountKeys = [];

  final CategoryService _categoryService = CategoryService();
  List<Category> _categories = [];
  String? _selectedCategory;

  @override
  void initState() {
    super.initState();
    _initializeWithTransaction();
    _fetchAccounts();
    _fetchCategories();
  }

  void _initializeWithTransaction() {
    // Initialize form with existing transaction data
    final amount = widget.transaction['amount'] as double;
    _amountController.text = amount.abs().toString();
    _titleController.text = widget.transaction['title'] ?? '';
    
    // Parse date
    try {
      final dateValue = widget.transaction['date'];
      if (dateValue is DateTime) {
        _selectedDate = dateValue;
      } else if (dateValue is String) {
        _selectedDate = DateTime.parse(dateValue);
      } else {
        _selectedDate = DateTime.now();
      }
    } catch (e) {
      _selectedDate = DateTime.now();
    }

    _selectedMainAccount = widget.transaction['main_account'];
    _selectedSubAccount = widget.transaction['sub_account_name'];
    _selectedCategory = widget.transaction['category'];
  }

  Future<void> _fetchCategories() async {
    try {
      final type = widget.isExpense ? 'expense' : 'income';
      final fetchedCategories = await _categoryService.getCategories(type: type);
      setState(() {
        _categories = fetchedCategories;
        // Ellenőrizzük, hogy a jelenlegi kategória benne van-e a listában
        if (_selectedCategory != null && !_categories.any((cat) => cat.name == _selectedCategory)) {
          _selectedCategory = _categories.isNotEmpty ? _categories.first.name : null;
        }
      });
    } catch (e) {
      print('Error fetching categories: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kategóriák betöltésekor: $e')),
      );
    }
  }

  Future<void> _fetchAccounts() async {
    try {
      final token = await _authService.getToken();
      if (token == null) {
        return;
      }

      final response = await http.get(
        Uri.parse('http://10.0.2.2:8000/accounts/me'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          _accountsData = json.decode(response.body);
          _mainAccountKeys = _accountsData!.keys.toList();
          if (_selectedMainAccount != null && _mainAccountKeys.contains(_selectedMainAccount)) {
            _updateSubAccounts();
          } else if (_mainAccountKeys.isNotEmpty) {
            _selectedMainAccount = _mainAccountKeys.first;
            _updateSubAccounts();
          }
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load accounts: ${response.body}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error fetching accounts: $e')),
      );
    }
  }

  void _updateSubAccounts() {
    if (_selectedMainAccount != null && _accountsData != null && _accountsData![_selectedMainAccount!] != null) {
      setState(() {
        _subAccountKeys = (_accountsData![_selectedMainAccount!]['alszamlak'] as Map<String, dynamic>).keys.toList();
        // Ellenőrizzük, hogy a jelenlegi alszámla benne van-e a listában
        if (_selectedSubAccount != null && !_subAccountKeys.contains(_selectedSubAccount)) {
          _selectedSubAccount = _subAccountKeys.isNotEmpty ? _subAccountKeys.first : null;
        }
      });
    } else {
      setState(() {
        _subAccountKeys = [];
        _selectedSubAccount = null;
      });
    }
  }

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2101),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  Future<void> _updateTransaction() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    if (_selectedMainAccount == null || _selectedSubAccount == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select both main and sub-account.')),
      );
      return;
    }

    final amountText = _amountController.text.replaceAll(RegExp(r'[^\d.]'), '');
    final double? amount = double.tryParse(amountText);

    if (amount == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Kérjük, érvényes összeget adjon meg.')),
      );
      return;
    }

    final String formattedDate = DateFormat('yyyy-MM-dd').format(_selectedDate);

    final payload = {
      'date': formattedDate,
      'amount': amount,
      'kategoria': _selectedCategory,
      'description': _titleController.text,
      'type': widget.isExpense ? 'expense' : 'income',
      'main_account': _selectedMainAccount,
      'sub_account_name': _selectedSubAccount,
    };

    try {
      await _transactionService.updateTransaction(widget.transaction['id'], payload);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Tranzakció sikeresen frissítve!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context, true); // true jelzi, hogy sikeres volt a frissítés
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hiba a frissítés során: $e')),
        );
      }
    }
  }

  Widget _buildInputField({
    required TextEditingController controller,
    required String labelText,
    required String hintText,
    required IconData icon,
    TextInputType keyboardType = TextInputType.text,
    String? Function(String?)? validator,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        style: TextStyle(
          fontSize: 16,
          color: Colors.black87,
        ),
        decoration: InputDecoration(
          labelText: labelText,
          hintText: hintText,
          labelStyle: TextStyle(
            color: Colors.grey[600],
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
          hintStyle: TextStyle(
            color: Colors.grey[400],
            fontSize: 14,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Color(0xFF00D4AA), width: 2),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          filled: true,
          fillColor: Colors.white,
          prefixIcon: Icon(icon, color: Colors.grey[600]),
          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        validator: validator,
      ),
    );
  }

  Widget _buildDropdownField({
    required String labelText,
    required IconData icon,
    required String? value,
    required List<String> items,
    required void Function(String?) onChanged,
    String? Function(String?)? validator,
    String? hintText,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: DropdownButtonFormField<String>(
        value: value,
        style: TextStyle(
          fontSize: 16,
          color: Colors.black87,
        ),
        decoration: InputDecoration(
          labelText: labelText,
          labelStyle: TextStyle(
            color: Colors.grey[600],
            fontSize: 16,
            fontWeight: FontWeight.w500,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Color(0xFF00D4AA), width: 2),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          filled: true,
          fillColor: Colors.white,
          prefixIcon: Icon(icon, color: Colors.grey[600]),
          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        hint: Text(
          hintText ?? 'Válasszon',
          style: TextStyle(
            color: Colors.grey[400],
            fontSize: 14,
          ),
        ),
        items: items.map((String item) {
          return DropdownMenuItem<String>(
            value: item,
            child: Text(item),
          );
        }).toList(),
        onChanged: onChanged,
        validator: validator,
      ),
    );
  }

  Widget _buildDateSelector() {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: () => _selectDate(context),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey[300]!),
          ),
          child: Row(
            children: [
              Icon(Icons.calendar_today, color: Colors.grey[600]),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Dátum',
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      DateFormat('yyyy. MM. dd.').format(_selectedDate),
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.arrow_forward_ios, color: Colors.grey[400], size: 16),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenTitle = widget.isExpense ? 'Kiadás módosítása' : 'Bevétel módosítása';
    final buttonColor = widget.isExpense ? Colors.redAccent : Color(0xFF00D4AA);

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
                      screenTitle,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  SizedBox(width: 48), // Balance the back button
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
                child: SingleChildScrollView(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(height: 10),
                          
                          _buildInputField(
                            controller: _amountController,
                            labelText: 'Összeg',
                            hintText: 'Pl. 10000',
                            icon: Icons.attach_money,
                            keyboardType: TextInputType.number,
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Kérjük, adja meg az összeget';
                              }
                              final cleaned = value
                                  .replaceAll(' ', '')      // szóköz eltávolítása
                                  .replaceAll(',', '.');    // vesszőből pont
                              if (double.tryParse(cleaned) == null) {
                                return 'Kérjük, érvényes számot adjon meg';
                              }
                              return null;
                            },
                          ),
                          
                          _buildDateSelector(),
                          
                          if (_categories.isNotEmpty)
                            _buildDropdownField(
                              labelText: 'Kategória',
                              icon: Icons.category,
                              value: _selectedCategory,
                              items: _categories.map((category) => category.name).toList(),
                              hintText: 'Válassz kategóriát',
                              onChanged: (String? newValue) {
                                setState(() {
                                  _selectedCategory = newValue;
                                });
                              },
                              validator: (value) {
                                if (value == null) {
                                  return 'Kérjük, válasszon kategóriát';
                                }
                                return null;
                              },
                            ),
                          
                          if (_mainAccountKeys.isNotEmpty)
                            _buildDropdownField(
                              labelText: 'Főszámla',
                              icon: Icons.account_balance,
                              value: _selectedMainAccount,
                              items: _mainAccountKeys,
                              hintText: 'Válassz főszámlát',
                              onChanged: (String? newValue) {
                                setState(() {
                                  _selectedMainAccount = newValue;
                                  _updateSubAccounts();
                                });
                              },
                              validator: (value) {
                                if (value == null) {
                                  return 'Kérjük, válasszon főszámlát';
                                }
                                return null;
                              },
                            ),
                          
                          if (_subAccountKeys.isNotEmpty)
                            _buildDropdownField(
                              labelText: 'Alszámla',
                              icon: Icons.account_balance_wallet,
                              value: _selectedSubAccount,
                              items: _subAccountKeys,
                              hintText: 'Válassz alszámlát',
                              onChanged: (String? newValue) {
                                setState(() {
                                  _selectedSubAccount = newValue;
                                });
                              },
                              validator: (value) {
                                if (value == null) {
                                  return 'Kérjük, válasszon alszámlát';
                                }
                                return null;
                              },
                            ),
                          
                          _buildInputField(
                            controller: _titleController,
                            labelText: 'Leírás / Megjegyzés',
                            hintText: widget.isExpense ? 'Pl. Heti bevásárlás' : 'Pl. Fizetés',
                            icon: Icons.description,
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Kérjük, adjon meg egy leírást';
                              }
                              return null;
                            },
                          ),

                          SizedBox(height: 24),
                          
                          Container(
                            width: double.infinity,
                            height: 56,
                            child: ElevatedButton(
                              onPressed: _updateTransaction,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: buttonColor,
                                foregroundColor: Colors.white,
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                              ),
                              child: Text(
                                'Frissítés',
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
            ),
          ],
        ),
      ),
    );
  }
}