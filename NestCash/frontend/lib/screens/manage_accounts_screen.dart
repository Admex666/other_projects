import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/services/sunburst_chart.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/add_incomes_screen.dart';
import 'package:frontend/config/config.dart';
import 'package:easy_localization/easy_localization.dart';

class ManageAccountsScreen extends StatefulWidget {
  final String userId;

  const ManageAccountsScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _ManageAccountsScreenState createState() => _ManageAccountsScreenState();
}

class _ManageAccountsScreenState extends State<ManageAccountsScreen> {
  Map<String, dynamic>? _accountsData;
  bool _isLoading = false;
  String? _errorMessage;
  final AuthService _authService = AuthService();

  @override
  void initState() {
    super.initState();
    _fetchAccounts();
  }

  // Segédfüggvény a hiba részleteinek kinyerésére a válasz törzséből
  String _extractErrorMessage(http.Response response, String defaultMessage) {
    try {
      final Map<String, dynamic> responseBody = json.decode(response.body);
      return responseBody['detail'] ?? defaultMessage;
    } catch (e) {
      return defaultMessage;
    }
  }

  // API hívás a számlák lekérdezéséhez
  Future<void> _fetchAccounts() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final token = await _authService.getToken();
      if (token == null) {
        setState(() {
          _errorMessage = 'error.auth_token_missing'.tr();
          _isLoading = false;
        });
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
        });
      } else if (response.statusCode == 404) { // Specifikus 404 kezelés
        setState(() {
          _errorMessage = 'error_.account_not_found'.tr();
        });
      } else {
        setState(() {
          // Próbáljuk meg kinyerni a 'detail' üzenetet a backendről
          _errorMessage = _extractErrorMessage(
            response,
            'error_.fetch_accounts_error'.tr(namedArgs: {'statusCode': response.statusCode.toString()})
          );
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'error_.network_error'.tr(namedArgs: {'error': e.toString()});
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // Dialógus új alszámla hozzáadásához
  void _showAddSubAccountDialog() {
    final _formKey = GlobalKey<FormState>();
    String? _mainAccount;
    String? _subAccountName;
    double? _balance;
    String _currency = "HUF";

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('accounts_.new_subaccount_title'.tr()),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: _mainAccount,
                hint: Text('accounts_.select_main_account'.tr()),
                onChanged: (value) => _mainAccount = value,
                items: ['likvid', 'befektetes', 'megtakaritas']
                    .map((label) => DropdownMenuItem(child: Text(label), value: label))
                    .toList(),
                validator: (value) => value == null ? 'validation.required_field'.tr() : null,
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'accounts_.subaccount_name'.tr()),
                onSaved: (value) => _subAccountName = value,
                validator: (value) => value == null || value.isEmpty ? 'validation.required_field'.tr() : null,
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'accounts_.balance'.tr()),
                keyboardType: TextInputType.number,
                onSaved: (value) => _balance = double.tryParse(value ?? ''),
                validator: (value) {
                  if (value == null || double.tryParse(value) == null) {
                    return 'validation.invalid_number'.tr();
                  }
                  return null;
                },
              ),
              TextFormField(
                initialValue: _currency,
                decoration: InputDecoration(labelText: 'accounts_.currency'.tr()),
                onSaved: (value) => _currency = value ?? 'HUF',
                validator: (value) => value == null || value.isEmpty ? 'validation.required_field'.tr() : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('button.cancel'.tr())),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _formKey.currentState!.save();
                _addSubAccount(_mainAccount!, _subAccountName!, _balance!, _currency);
                Navigator.pop(context);
              }
            },
            child: Text('button.add'.tr()),
          ),
        ],
      ),
    );
  }

  // API hívás alszámla hozzáadásához
  Future<void> _addSubAccount(String mainAccount, String subAccountName, double balance, String currency) async {
    setState(() => _isLoading = true);
    try {
      final token = await _authService.getToken();
      if (token == null) {
        setState(() {
          _errorMessage = 'error_.auth_token_missing'.tr();
          _isLoading = false;
        });
        return;
      }

      final response = await http.put(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me/$mainAccount/$subAccountName'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode({'balance': balance, 'currency': currency}),
      );
      if (response.statusCode == 200) {
        _fetchAccounts();
      } else {
        setState(() {
          _errorMessage = _extractErrorMessage(
            response,
            'error_.add_error'.tr(namedArgs: {'statusCode': response.statusCode.toString()})
          );
        });
      }
    } catch (e) {
      setState(() => _errorMessage = 'error_.network_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Dialógus alszámla törléséhez
  void _showDeleteSubAccountDialog() {
    final _formKey = GlobalKey<FormState>();
    String? _mainAccount;
    String? _subAccountName;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('accounts_.delete_subaccount_title'.tr()),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: _mainAccount,
                hint: Text('accounts_.select_main_account'.tr()),
                onChanged: (value) => _mainAccount = value,
                items: ['likvid', 'befektetes', 'megtakaritas']
                    .map((label) => DropdownMenuItem(child: Text(label), value: label))
                    .toList(),
                validator: (value) => value == null ? 'validation.required_field'.tr() : null,
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'accounts_.subaccount_name'.tr()),
                onSaved: (value) => _subAccountName = value,
                validator: (value) => value == null || value.isEmpty ? 'validation.required_field'.tr() : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('button.cancel'.tr())),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _formKey.currentState!.save();
                _deleteSubAccount(_mainAccount!, _subAccountName!);
                Navigator.pop(context);
              }
            },
            child: Text('button.delete'.tr()),
          ),
        ],
      ),
    );
  }

  // API hívás alszámla törléséhez
  Future<void> _deleteSubAccount(String mainAccount, String subAccountName) async {
    setState(() => _isLoading = true);
    try {
      final token = await _authService.getToken();
      if (token == null) {
        setState(() {
          _errorMessage = 'error_.auth_token_missing'.tr();
          _isLoading = false;
        });
        return;
      }

      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/accounts/me/$mainAccount/$subAccountName'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
      if (response.statusCode == 200) {
        _fetchAccounts();
      } else if (response.statusCode == 404) { // Specifikus 404 kezelés
        setState(() {
          _errorMessage = 'error.subaccount_not_found'.tr(); // Pontosabb üzenet törléskor
        });
      }
      else {
        setState(() {
          _errorMessage = _extractErrorMessage(
            response,
            'error_.delete_error'.tr(namedArgs: {'statusCode': response.statusCode.toString()})
          );
        });
      }
    } catch (e) {
      setState(() => _errorMessage = 'error_.network_error'.tr(namedArgs: {'error': e.toString()}));
    } finally {
      setState(() => _isLoading = false);
    }
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
            mainAxisSize: MainAxisSize.max, // A Column kitölti a rendelkezésre álló magasságot
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
                        'accounts_.manage_accounts_title'.tr(),
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    // ÚJ KÓD: Egy átlátszó IconButton a jobb oldalon a vizuális középre igazításért
                    // Ez a widget ugyanannyi helyet foglal el, mint a bal oldali nyíl ikon.
                    Opacity( //
                      opacity: 0.0, // Láthatatlanná teszi a widgetet
                      child: IconButton( //
                        icon: const Icon(Icons.arrow_back, color: Colors.transparent), // Átlátszó ikon
                        onPressed: () {}, // Üres onPressed, nincs funkcionalitása
                      ),
                    ),
                  ],
                ),
              ),

              // Content Container (ez lesz a fehér, lekerekített sarkú rész)
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
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        SizedBox(height: 8),

                        Container(
                            height: 100, // Fix magasság a 4 gombnak
                            child: Column(
                              children: [
                                // Első sor
                                Row(
                                  children: [
                                    // Bevétel hozzáadása
                                    Expanded(
                                      child: Container(
                                        height: 44, // Csökkentett magasság
                                        margin: EdgeInsets.only(right: 6),
                                        child: ElevatedButton.icon(
                                          onPressed: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                builder: (context) => AddIncomesScreen(userId: widget.userId),
                                              ),
                                            );
                                          },
                                          icon: Icon(Icons.add, size: 18, color: Colors.white),
                                          label: Text(
                                            'button.add_income'.tr(),
                                            style: TextStyle(
                                              fontSize: 13,
                                              fontWeight: FontWeight.w600,
                                              color: Colors.white,
                                            ),
                                          ),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Color(0xFF00D4A3),
                                            elevation: 0,
                                            shape: RoundedRectangleBorder(
                                              borderRadius: BorderRadius.circular(10),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                    // Kiadás hozzáadása
                                    Expanded(
                                      child: Container(
                                        height: 44,
                                        margin: EdgeInsets.only(left: 6),
                                        child: ElevatedButton.icon(
                                          onPressed: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                builder: (context) => AddExpensesScreen(userId: widget.userId),
                                              ),
                                            );
                                          },
                                          icon: Icon(Icons.remove, size: 18, color: Colors.white),
                                          label: Text(
                                            'button.add_expense'.tr(),
                                            style: TextStyle(
                                              fontSize: 13,
                                              fontWeight: FontWeight.w600,
                                              color: Colors.white,
                                            ),
                                          ),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Colors.redAccent,
                                            elevation: 0,
                                            shape: RoundedRectangleBorder(
                                              borderRadius: BorderRadius.circular(10),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                
                                SizedBox(height: 12),
                                
                                // Második sor
                                Row(
                                  children: [
                                    // Új alszámla
                                    Expanded(
                                      child: Container(
                                        height: 44,
                                        margin: EdgeInsets.only(right: 6),
                                        child: ElevatedButton.icon(
                                          onPressed: _showAddSubAccountDialog,
                                          icon: Icon(Icons.account_balance_wallet, size: 18, color: Colors.white),
                                          label: Text(
                                            'button.new_account'.tr(),
                                            style: TextStyle(
                                              fontSize: 13,
                                              fontWeight: FontWeight.w600,
                                              color: Colors.white,
                                            ),
                                          ),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Colors.green,
                                            elevation: 0,
                                            shape: RoundedRectangleBorder(
                                              borderRadius: BorderRadius.circular(10),
                                            ),
                                          ),
                                        ),
                                      ),
                                    ),
                                    // Frissítés + Törlés kombinált
                                    Expanded(
                                      child: Container(
                                        height: 44,
                                        margin: EdgeInsets.only(left: 6),
                                        child: Row(
                                          children: [
                                            // Frissítés
                                            Expanded(
                                              child: ElevatedButton(
                                                onPressed: _fetchAccounts,
                                                child: Icon(Icons.refresh, size: 18, color: Colors.white),
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor: Color(0xFF00D4AA),
                                                  elevation: 0,
                                                  shape: RoundedRectangleBorder(
                                                    borderRadius: BorderRadius.circular(10),
                                                  ),
                                                ),
                                              ),
                                            ),
                                            SizedBox(width: 4),
                                            // Törlés
                                            Expanded(
                                              child: ElevatedButton(
                                                onPressed: _showDeleteSubAccountDialog,
                                                child: Icon(Icons.delete, size: 18, color: Colors.white),
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor: Colors.red,
                                                  elevation: 0,
                                                  shape: RoundedRectangleBorder(
                                                    borderRadius: BorderRadius.circular(10),
                                                  ),
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),

                          SizedBox(height: 16),

                        // Tartalom megjelenítése
                        if (_isLoading)
                          Expanded(
                            child: Center(
                              child: CircularProgressIndicator(
                                color: Color(0xFF00D4AA),
                              ),
                            ),
                          )
                        else if (_errorMessage != null)
                          Expanded(
                            child: Center(
                              child: Text(
                                _errorMessage!,
                                style: TextStyle(
                                  color: Colors.red,
                                  fontSize: 16,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          )
                        else if (_accountsData != null)
                          Expanded(
                            child: SingleChildScrollView(
                              child: Column(
                                children: [
                                  // Sunburst diagram hozzáadása
                                  Container(
                                    margin: EdgeInsets.only(bottom: 32),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(20),
                                      boxShadow: [
                                        BoxShadow(
                                          color: Colors.grey.withOpacity(0.08),
                                          spreadRadius: 0,
                                          blurRadius: 20,
                                          offset: Offset(0, 4),
                                        ),
                                        BoxShadow(
                                          color: Colors.grey.withOpacity(0.05),
                                          spreadRadius: 0,
                                          blurRadius: 40,
                                          offset: Offset(0, 8),
                                        ),
                                      ],
                                    ),
                                    child: Padding(
                                      padding: EdgeInsets.all(8),
                                      child: AccountsSunburstChart(accountsData: _accountsData),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                      ],
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