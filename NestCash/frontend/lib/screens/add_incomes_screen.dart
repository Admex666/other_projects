// frontend/screens/add_incomes_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/services/category_service.dart';
import 'package:frontend/models/category.dart';
import 'package:intl/intl.dart'; 
import 'package:frontend/config/config.dart';
import 'package:easy_localization/easy_localization.dart';

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

  DateTime _selectedDate = DateTime.now();

  Map<String, dynamic>? _accountsData;
  String? _selectedMainAccount;
  String? _selectedSubAccount;
  List<String> _mainAccountKeys = [];
  List<String> _subAccountKeys = [];

  final CategoryService _categoryService = CategoryService();
  List<Category> _incomeCategories = [];
  String? _selectedCategory;

  @override
  void initState() {
    super.initState();
    _fetchAccounts();
    _fetchCategories();
  }

  Future<void> _fetchAccounts() async {
    try {
      final token = await _authService.getToken();
      if (token == null) {
        return;
      }

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          _accountsData = json.decode(response.body);
          _mainAccountKeys = _accountsData!.keys.toList();
          if (_mainAccountKeys.isNotEmpty) {
            _selectedMainAccount = _mainAccountKeys.first;
            _updateSubAccounts();
          }
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('error_failed_to_load_accounts'.tr(namedArgs: {'error': response.body}))),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_fetching_accounts'.tr(namedArgs: {'error': e.toString()}))),
      );
    }
  }

  void _updateSubAccounts() {
    if (_selectedMainAccount != null && _accountsData != null && _accountsData![_selectedMainAccount!] != null) {
      setState(() {
        _subAccountKeys = (_accountsData![_selectedMainAccount!]['alszamlak'] as Map<String, dynamic>).keys.toList();
        _selectedSubAccount = _subAccountKeys.isNotEmpty ? _subAccountKeys.first : null;
      });
    } else {
      setState(() {
        _subAccountKeys = [];
        _selectedSubAccount = null;
      });
    }
  }

  Future<void> _fetchCategories() async {
    try {
      final fetchedCategories = await _categoryService.getCategories(type: 'income');
      setState(() {
        _incomeCategories = fetchedCategories;
        if (_incomeCategories.isNotEmpty) {
          _selectedCategory = _incomeCategories.first.name;
        }
      });
    } catch (e) {
      print('Error fetching income categories: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_fetching_categories'.tr(namedArgs: {'error': e.toString()}))),
      );
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

  Future<void> _saveIncome() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    if (_selectedMainAccount == null || _selectedSubAccount == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_select_main_sub_account'.tr())),
      );
      return;
    }

    final amountText = _amountController.text.replaceAll(RegExp(r'[^\d.]'), '');
    final double? amount = double.tryParse(amountText);

    if (amount == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_invalid_amount'.tr())),
      );
      return;
    }

    final String formattedDate = DateFormat('yyyy-MM-dd').format(_selectedDate);

    final payload = {
      'date': formattedDate,
      'amount': amount,
      'kategoria': _selectedCategory == 'Válassz kategóriát' ? null : _selectedCategory,
      'description': _titleController.text,
      'type': 'income',
      'main_account': _selectedMainAccount,
      'sub_account_name': _selectedSubAccount,
      'user_id': widget.userId,
    };

    try {
      final token = await _authService.getToken();
      if (token == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('error_missing_token'.tr())),
        );
        return;
      }

      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/transactions/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(payload),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('success_income_saved'.tr()),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        _amountController.clear();
        _titleController.clear();
        setState(() {
          _selectedCategory = _incomeCategories.isNotEmpty ? _incomeCategories.first.name : null;
          _selectedMainAccount = _mainAccountKeys.isNotEmpty ? _mainAccountKeys.first : null;
          _updateSubAccounts();
        });
      } else {
        final errorDetail = json.decode(response.body)['detail'] ?? 'unknown_error'.tr();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('error_saving_failed'.tr(namedArgs: {'error': errorDetail}))),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('error_network'.tr(namedArgs: {'error': e.toString()}))),
      );
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
          hintText ?? 'select_category_hint'.tr(),
          style: TextStyle(
            color: Colors.grey[400],
            fontSize: 14,
          ),
        ),
        items: items.map((String item) {
          return DropdownMenuItem<String>(
            value: item,
            child: Text(item.tr()),
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
                      'date_label'.tr(),
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
                      'new_income_title'.tr(),
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
                            labelText: 'amount_label'.tr(),
                            hintText: 'amount_hint'.tr(),
                            icon: Icons.attach_money,
                            keyboardType: TextInputType.number,
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'error_missing_amount'.tr();
                              }
                              final cleaned = value
                                  .replaceAll(' ', '')
                                  .replaceAll(',', '.');
                              if (double.tryParse(cleaned) == null) {
                                return 'error_invalid_amount'.tr();
                              }
                              return null;
                            },
                          ),
                          
                          _buildDateSelector(),
                          
                          _buildDropdownField(
                            labelText: 'category_label'.tr(),
                            icon: Icons.category,
                            value: _selectedCategory == 'Válassz kategóriát' ? null : _selectedCategory,
                            items: _incomeCategories.map((category) => category.name).toList(),
                            hintText: 'select_category_hint'.tr(),
                            onChanged: (String? newValue) {
                              setState(() {
                                _selectedCategory = newValue;
                              });
                            },
                            validator: (value) {
                              if (value == null || value == 'select_category_hint'.tr()) {
                                return 'error_select_category'.tr();
                              }
                              return null;
                            },
                          ),
                          
                          _buildDropdownField(
                            labelText: 'main_account_label'.tr(),
                            icon: Icons.account_balance,
                            value: _selectedMainAccount,
                            items: _mainAccountKeys,
                            hintText: 'select_main_account_hint'.tr(),
                            onChanged: (String? newValue) {
                              setState(() {
                                _selectedMainAccount = newValue;
                                _updateSubAccounts();
                              });
                            },
                            validator: (value) {
                              if (value == null) {
                                return 'error_select_main_account'.tr();
                              }
                              return null;
                            },
                          ),
                          
                          _buildDropdownField(
                            labelText: 'sub_account_label'.tr(),
                            icon: Icons.account_balance_wallet,
                            value: _selectedSubAccount,
                            items: _subAccountKeys,
                            hintText: 'select_sub_account_hint'.tr(),
                            onChanged: (String? newValue) {
                              setState(() {
                                _selectedSubAccount = newValue;
                              });
                            },
                            validator: (value) {
                              if (value == null) {
                                return 'error_select_sub_account'.tr();
                              }
                              return null;
                            },
                          ),
                          
                          _buildInputField(
                            controller: _titleController,
                            labelText: 'description_label'.tr(),
                            hintText: 'description_hint_incomes'.tr(),
                            icon: Icons.description,
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'error_missing_description'.tr();
                              }
                              return null;
                            },
                          ),

                          SizedBox(height: 24),
                          
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
                                'save_button'.tr(),
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