// add_expenses_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/models/category.dart';
import 'package:frontend/services/category_service.dart';
import 'package:intl/intl.dart'; // Import for date formatting
import '../services/limit_service.dart';
import '../models/limit.dart';

class AddExpensesScreen extends StatefulWidget {
  final String userId;

  const AddExpensesScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _AddExpensesScreenState createState() => _AddExpensesScreenState();
}

class _AddExpensesScreenState extends State<AddExpensesScreen> {
  final AuthService _authService = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _titleController = TextEditingController(); // Description is now title
  final LimitService _limitService = LimitService();

  DateTime _selectedDate = DateTime.now();
    
  Map<String, dynamic>? _accountsData;
  String? _selectedMainAccount;
  String? _selectedSubAccount;
  List<String> _mainAccountKeys = [];
  List<String> _subAccountKeys = [];

  final CategoryService _categoryService = CategoryService();
  List<Category> _expenseCategories = [];
  String? _selectedCategory; // Mostantól nullable, mivel dinamikusan töltődik be

  @override
  void initState() {
    super.initState();
    _fetchAccounts();
    _fetchCategories();
  }

  Future<void> _fetchCategories() async {
    try {
      final fetchedCategories = await _categoryService.getCategories(type: 'expense');
      setState(() {
        _expenseCategories = fetchedCategories;
        if (_expenseCategories.isNotEmpty) {
          _selectedCategory = _expenseCategories.first.name; // Az első kategória beállítása alapértelmezettnek
        }
      });
    } catch (e) {
      print('Error fetching expense categories: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a kategóriák betöltésekor: $e')),
      );
    }
  }

  Future<void> _fetchAccounts() async {
    try {
      final token = await _authService.getToken();
      if (token == null) {
        // Handle no token
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
          if (_mainAccountKeys.isNotEmpty) {
            _selectedMainAccount = _mainAccountKeys.first;
            _updateSubAccounts();
          }
        });
      } else {
        // Handle error
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
        _selectedSubAccount = _subAccountKeys.isNotEmpty ? _subAccountKeys.first : null;
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

  Future<void> _saveExpense() async {
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
      'date': formattedDate, // Módosítva: datum helyett date
      'amount': -amount, // Módosítva: osszeg helyett amount
      'kategoria': _selectedCategory == 'Válassz kategóriát' ? null : _selectedCategory,
      'description': _titleController.text, // Módosítva: leiras helyett description
      'type': 'expense', // Módosítva: tipus helyett type
      'main_account': _selectedMainAccount, // Módosítva: foszamla helyett main_account
      'sub_account_name': _selectedSubAccount, // Módosítva: alszamla helyett sub_account_name
      'user_id': widget.userId, // Ez a mező valószínűleg nem kell a TransactionCreate sémába, a backend hozzáadja. Lásd lentebb.
    };

    try {
      final token = await _authService.getToken();
      if (token == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Autentikációs token hiányzik.')),
        );
        return;
      }

      final response = await http.post(
        Uri.parse('http://10.0.2.2:8000/transactions/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(payload),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Kiadás sikeresen mentve!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        _amountController.clear();
        _titleController.clear();
        setState(() {
          _selectedCategory = 'Válassz kategóriát';
          _selectedDate = DateTime.now();
          _selectedMainAccount = _mainAccountKeys.isNotEmpty ? _mainAccountKeys.first : null;
          _updateSubAccounts();
        });
      } else {
        final errorDetail = json.decode(response.body)['detail'] ?? 'Ismeretlen hiba történt.';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hiba a mentés során: $errorDetail')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hálózati hiba: $e')),
      );
    }
  }

  Future<bool> _checkLimits(double amount, String? category, String mainAccount, String subAccount) async {
    try {
      final result = await _limitService.checkLimits(
        amount: -amount, // Negatív, mert kiadás
        category: category,
        mainAccount: mainAccount,
        subAccountName: subAccount,
      );
      
      if (!result.isAllowed) {
        // Megerősítő dialógus megjelenítése
        final confirm = await showDialog<bool>(
          context: context,
          builder: (BuildContext context) {
            return AlertDialog(
              title: const Text('Limit figyelmeztetés'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(result.message ?? 'Egy vagy több limit túllépne.'),
                  if (result.exceededLimits.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    const Text('Túllépett limitek:', style: TextStyle(fontWeight: FontWeight.bold)),
                    ...result.exceededLimits.map((limit) => Text('• $limit')),
                  ],
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(false),
                  child: const Text('Mégse'),
                ),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(true),
                  style: TextButton.styleFrom(foregroundColor: Colors.red),
                  child: const Text('Folytatás'),
                ),
              ],
            );
          },
        );
        
        return confirm ?? false;
      } else if (result.warnings.isNotEmpty) {
        // Figyelmeztetés megjelenítése, de engedélyezés
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.message ?? 'Figyelem: közel vagy a limithez'),
            backgroundColor: Colors.orange,
          ),
        );
      }
      
      return true;
    } catch (e) {
      // Hiba esetén engedjük a tranzakciót
      return true;
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
      decoration: InputDecoration(
        labelText: labelText,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
          borderSide: BorderSide(color: Color(0xFFD3D3D3)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(15),
          borderSide: BorderSide(color: Color(0xFF00D4AA), width: 2),
        ),
        filled: true,
        fillColor: Colors.white,
      ),
      items: items.map((String value) {
        return DropdownMenuItem<String>(
          value: value,
          child: Text(value),
        );
      }).toList(),
      value: value,
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
                      'Új Kiadás rögzítése',
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
                          
                          _buildDropdownField(
                            labelText: 'Kategória',
                            icon: Icons.category,
                            value: _selectedCategory == 'Válassz kategóriát' ? null : _selectedCategory,
                            items: _expenseCategories.map((category) => category.name).toList(),
                            hintText: 'Válassz kategóriát',
                            onChanged: (String? newValue) {
                              setState(() {
                                _selectedCategory = newValue!;
                              });
                            },
                            validator: (value) {
                              if (value == null || value == 'Válassz kategóriát') {
                                return 'Kérjük, válasszon kategóriát';
                              }
                              return null;
                            },
                          ),
                          
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
                            hintText: 'Pl. Heti bevásárlás',
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
            ),
          ],
        ),
      ),
    );
  }
}