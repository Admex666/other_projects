import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/services/auth_service.dart';

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
          _errorMessage = 'Autentikációs token hiányzik.';
          _isLoading = false;
        });
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
        });
      } else if (response.statusCode == 404) { // Specifikus 404 kezelés
        setState(() {
          _errorMessage = 'Számla nem található.';
        });
      } else {
        setState(() {
          // Próbáljuk meg kinyerni a 'detail' üzenetet a backendről
          _errorMessage = _extractErrorMessage(
            response,
            'Hiba a számlák lekérdezésekor: ${response.statusCode}'
          );
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Hálózati hiba: $e';
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
        title: Text('Új alszámla hozzáadása'),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: _mainAccount,
                hint: Text('Főszámla kiválasztása'),
                onChanged: (value) => _mainAccount = value,
                items: ['likvid', 'befektetes', 'megtakaritas']
                    .map((label) => DropdownMenuItem(child: Text(label), value: label))
                    .toList(),
                validator: (value) => value == null ? 'Kötelező mező' : null,
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Alszámla neve'),
                onSaved: (value) => _subAccountName = value,
                validator: (value) => value == null || value.isEmpty ? 'Kötelező mező' : null,
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Egyenleg'),
                keyboardType: TextInputType.number,
                onSaved: (value) => _balance = double.tryParse(value ?? ''),
                validator: (value) {
                  if (value == null || double.tryParse(value) == null) {
                    return 'Érvénytelen szám';
                  }
                  return null;
                },
              ),
              TextFormField(
                initialValue: _currency,
                decoration: InputDecoration(labelText: 'Deviza (pl. HUF, EUR, USD)'),
                onSaved: (value) => _currency = value ?? 'HUF',
                validator: (value) => value == null || value.isEmpty ? 'Kötelező mező' : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Mégse')),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _formKey.currentState!.save();
                _addSubAccount(_mainAccount!, _subAccountName!, _balance!, _currency);
                Navigator.pop(context);
              }
            },
            child: Text('Hozzáadás'),
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
          _errorMessage = 'Autentikációs token hiányzik.';
          _isLoading = false;
        });
        return;
      }

      final response = await http.put(
        Uri.parse('http://10.0.2.2:8000/accounts/me/$mainAccount/$subAccountName'),
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
            'Hiba a hozzáadáskor: ${response.statusCode}'
          );
        });
      }
    } catch (e) {
      setState(() => _errorMessage = 'Hálózati hiba: $e');
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
        title: Text('Alszámla törlése'),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: _mainAccount,
                hint: Text('Főszámla kiválasztása'),
                onChanged: (value) => _mainAccount = value,
                items: ['likvid', 'befektetes', 'megtakaritas']
                    .map((label) => DropdownMenuItem(child: Text(label), value: label))
                    .toList(),
                validator: (value) => value == null ? 'Kötelező mező' : null,
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Alszámla neve'),
                onSaved: (value) => _subAccountName = value,
                validator: (value) => value == null || value.isEmpty ? 'Kötelező mező' : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Mégse')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _formKey.currentState!.save();
                _deleteSubAccount(_mainAccount!, _subAccountName!);
                Navigator.pop(context);
              }
            },
            child: Text('Törlés'),
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
          _errorMessage = 'Autentikációs token hiányzik.';
          _isLoading = false;
        });
        return;
      }

      final response = await http.delete(
        Uri.parse('http://10.0.2.2:8000/accounts/me/$mainAccount/$subAccountName'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
      if (response.statusCode == 200) {
        _fetchAccounts();
      } else if (response.statusCode == 404) { // Specifikus 404 kezelés
        setState(() {
          _errorMessage = 'Alszámla nem található.'; // Pontosabb üzenet törléskor
        });
      }
      else {
        setState(() {
          _errorMessage = _extractErrorMessage(
            response,
            'Hiba a törléskor: ${response.statusCode}'
          );
        });
      }
    } catch (e) {
      setState(() => _errorMessage = 'Hálózati hiba: $e');
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
                        'Számlák Kezelése',
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
                        SizedBox(height: 16),

                        // Gombok
                        Container(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton.icon(
                            onPressed: _fetchAccounts,
                            icon: Icon(Icons.refresh, color: Colors.white),
                            label: Text(
                              'Számlák frissítése',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFF00D4AA),
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),

                        SizedBox(height: 12),

                        Container(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton.icon(
                            onPressed: _showAddSubAccountDialog,
                            icon: Icon(Icons.add, color: Colors.white),
                            label: Text(
                              'Új alszámla',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.green,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),

                        SizedBox(height: 12),

                        Container(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton.icon(
                            onPressed: _showDeleteSubAccountDialog,
                            icon: Icon(Icons.delete, color: Colors.white),
                            label: Text(
                              'Alszámla törlése',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Colors.white,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.red,
                              elevation: 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ),

                        SizedBox(height: 24),

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
                            child: ListView(
                              children: (_accountsData!.entries).map((entry) {
                                return Container(
                                  margin: EdgeInsets.only(bottom: 16),
                                  decoration: BoxDecoration(
                                    color: Color(0xFFE8F5E8),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Padding(
                                    padding: const EdgeInsets.all(16.0),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          entry.key.toUpperCase(), // likvid, befektetes, stb.
                                          style: TextStyle(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.black87,
                                          ),
                                        ),
                                        SizedBox(height: 8),
                                        ...(entry.value['alszamlak'] as Map<String, dynamic>).entries.map((subEntry) {
                                          final subAccountBalance = subEntry.value['balance'];
                                          final subAccountCurrency = subEntry.value['currency'];
                                          return Padding(
                                            padding: const EdgeInsets.only(left: 16.0, top: 4),
                                            child: Row(
                                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                              children: [
                                                Text(
                                                  subEntry.key,
                                                  style: TextStyle(
                                                    fontSize: 16,
                                                    color: Colors.black87,
                                                  ),
                                                ),
                                                Text(
                                                  '${subAccountBalance.toStringAsFixed(2)} ${subAccountCurrency}',
                                                  style: TextStyle(
                                                    fontSize: 16,
                                                    color: Colors.black87,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          );
                                        }).toList(),
                                        Container(
                                          margin: EdgeInsets.symmetric(vertical: 8),
                                          height: 1,
                                          color: Colors.grey[400],
                                        ),
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              'Főösszeg',
                                              style: TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.black87,
                                              ),
                                            ),
                                            Text(
                                              '${entry.value['foosszeg'].toStringAsFixed(2)} Ft',
                                              style: TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.black87,
                                              ),
                                            ),
                                          ],
                                        )
                                      ],
                                    ),
                                  ),
                                );
                              }).toList(),
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