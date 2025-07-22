// frontend/screens/add_incomes_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart'; // Import for date formatting

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
  final _titleController = TextEditingController(); // Description is now title
  final _messageController = TextEditingController(); // This seems unused, assuming it's for extra notes or similar, keeping it for now

  DateTime _selectedDate = DateTime.now();
  String _selectedCategory = 'Válassz kategóriát'; // Default or initial value

  Map<String, dynamic>? _accountsData;
  String? _selectedMainAccount;
  String? _selectedSubAccount;
  List<String> _mainAccountKeys = [];
  List<String> _subAccountKeys = [];

  final List<String> _incomeCategories = [
    'Fizetés', 'Ajándék', 'Befektetés', 'Kamat', 'Egyéb bevétel'
  ];

  @override
  void initState() {
    super.initState();
    _fetchAccounts();
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

  Future<void> _saveIncome() async {
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
      'datum': formattedDate,
      'osszeg': amount, // Incomes are positive
      'kategoria': _selectedCategory == 'Válassz kategóriát' ? null : _selectedCategory,
      'leiras': _titleController.text,
      'tipus': 'bevetel',
      'foszamla': _selectedMainAccount,
      'alszamla': _selectedSubAccount,
      'user_id': widget.userId,
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
          SnackBar(content: Text('Bevétel sikeresen mentve!')),
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

  String _getMonthName(int month) {
    switch (month) {
      case 1: return 'Január';
      case 2: return 'Február';
      case 3: return 'Március';
      case 4: return 'Április';
      case 5: return 'Május';
      case 6: return 'Június';
      case 7: return 'Július';
      case 8: return 'Augusztus';
      case 9: return 'Szeptember';
      case 10: return 'Október';
      case 11: return 'November';
      case 12: return 'December';
      default: return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Új Bevétel', style: TextStyle(color: Colors.white)),
        backgroundColor: Color(0xFF00D4AA),
        iconTheme: IconThemeData(color: Colors.white),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextFormField(
                    controller: _amountController,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'Összeg',
                      hintText: 'Pl. 10000',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      prefixIcon: Icon(Icons.attach_money),
                    ),
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
                  SizedBox(height: 20),
                  TextFormField(
                    controller: _titleController,
                    decoration: InputDecoration(
                      labelText: 'Leírás / Megjegyzés',
                      hintText: 'Pl. Fizetés',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      prefixIcon: Icon(Icons.description),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Kérjük, adjon meg egy leírást';
                      }
                      return null;
                    },
                  ),
                  SizedBox(height: 20),
                  ListTile(
                    title: Text('Dátum: ${DateFormat('yyyy. MM. dd.').format(_selectedDate)}'),
                    trailing: Icon(Icons.calendar_today),
                    onTap: () => _selectDate(context),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: BorderSide(color: Colors.grey.shade400),
                    ),
                  ),
                  SizedBox(height: 20),
                  DropdownButtonFormField<String>(
                    value: _selectedCategory == 'Válassz kategóriát' ? null : _selectedCategory,
                    decoration: InputDecoration(
                      labelText: 'Kategória',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      prefixIcon: Icon(Icons.category),
                    ),
                    hint: Text('Válassz kategóriát'),
                    items: _incomeCategories.map((String category) {
                      return DropdownMenuItem<String>(
                        value: category,
                        child: Text(category),
                      );
                    }).toList(),
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
                  SizedBox(height: 20),
                  DropdownButtonFormField<String>(
                    value: _selectedMainAccount,
                    decoration: InputDecoration(
                      labelText: 'Főszámla',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      prefixIcon: Icon(Icons.account_balance),
                    ),
                    hint: Text('Válassz főszámlát'),
                    items: _mainAccountKeys.map((String account) {
                      return DropdownMenuItem<String>(
                        value: account,
                        child: Text(account),
                      );
                    }).toList(),
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
                  SizedBox(height: 20),
                  DropdownButtonFormField<String>(
                    value: _selectedSubAccount,
                    decoration: InputDecoration(
                      labelText: 'Alszámla',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      prefixIcon: Icon(Icons.account_balance_wallet),
                    ),
                    hint: Text('Válassz alszámlát'),
                    items: _subAccountKeys.map((String subAccount) {
                      return DropdownMenuItem<String>(
                        value: subAccount,
                        child: Text(subAccount),
                      );
                    }).toList(),
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
                  SizedBox(height: 40),
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
    );
  }
}