// lib/screens/transactions_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/transaction_service.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/add_incomes_screen.dart';

class TransactionsScreen extends StatefulWidget {
  final String userId;
  final String username;

  const TransactionsScreen({
    Key? key,
    required this.userId,
    required this.username,
  }) : super(key: key);

  @override
  _TransactionsScreenState createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  final TransactionService _transactionService = TransactionService();
  final ScrollController _scrollController = ScrollController();
  
  List<Map<String, dynamic>> _transactions = [];
  bool _isLoading = false;
  bool _hasMore = true;
  int _currentSkip = 0;
  final int _pageSize = 20;
  
  // Szűrő paraméterek
  String? _selectedType;
  String? _selectedCategory;
  DateTime? _startDate;
  DateTime? _endDate;
  
  @override
  void initState() {
    super.initState();
    _loadTransactions();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200 &&
        !_isLoading && _hasMore) {
      _loadMoreTransactions();
    }
  }

  Future<void> _loadTransactions({bool refresh = false}) async {
    if (refresh) {
      setState(() {
        _transactions.clear();
        _currentSkip = 0;
        _hasMore = true;
      });
    }

    setState(() => _isLoading = true);

    try {
      final transactions = await _transactionService.getTransactions(
        limit: _pageSize,
        skip: _currentSkip,
        type: _selectedType,
        category: _selectedCategory,
        startDate: _startDate,
        endDate: _endDate,
      );

      setState(() {
        if (refresh) {
          _transactions = _processTransactions(transactions);
        } else {
          _transactions.addAll(_processTransactions(transactions));
        }
        _hasMore = transactions.length == _pageSize;
        _currentSkip += transactions.length;
      });
    } catch (e) {
      print('Error loading transactions: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba a tranzakciók betöltésekor: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadMoreTransactions() async {
    await _loadTransactions();
  }

  List<Map<String, dynamic>> _processTransactions(List<Map<String, dynamic>> transactions) {
    return transactions.map((transaction) {
      try {
        // Több lehetséges mező nevvel számolunk
        final type = transaction['type'] ?? transaction['tipus'];
        final amount = (transaction['amount'] ?? transaction['osszeg'] ?? 0 as num).toDouble();
        final description = transaction['description'] ?? transaction['leiras'] ?? 'Ismeretlen tranzakció';
        final category = transaction['kategoria'] ?? transaction['category'] ?? 'Egyéb';
        final dateStr = transaction['date'] ?? transaction['datum'];
        
        // Dátum parse-olás
        DateTime date = DateTime.now();
        if (dateStr != null) {
          try {
            date = DateTime.parse(dateStr.toString());
          } catch (e) {
            print('Error parsing date: $dateStr');
          }
        }
        
        // Típus meghatározása
        bool isExpense = false;
        if (type != null) {
          isExpense = type == 'expense' || type == 'kiadas';
        } else {
          isExpense = amount < 0;
        }
        
        return {
          'id': transaction['id'] ?? transaction['_id'] ?? '',
          'title': description,
          'amount': amount,
          'category': category,
          'date': date,
          'isExpense': isExpense,
          'icon': _getTransactionIcon(category, isExpense),
          'main_account': transaction['main_account'] ?? 'Ismeretlen',
          'sub_account_name': transaction['sub_account_name'] ?? 'Ismeretlen',
        };
      } catch (e) {
        print('Error processing transaction: $transaction, error: $e');
        return {
          'id': '',
          'title': 'Hibás tranzakció',
          'amount': 0.0,
          'category': 'Egyéb',
          'date': DateTime.now(),
          'isExpense': false,
          'icon': Icons.error,
          'main_account': 'Ismeretlen',
          'sub_account_name': 'Ismeretlen',
        };
      }
    }).toList();
  }

  IconData _getTransactionIcon(String category, bool isExpense) {
    if (!isExpense) {
      return Icons.attach_money;
    }
    
    switch (category.toLowerCase()) {
      case 'élelmiszer':
      case 'food':
        return Icons.restaurant;
      case 'lakhatás':
      case 'housing':
        return Icons.home;
      case 'közlekedés':
      case 'transport':
        return Icons.directions_car;
      case 'szórakozás':
      case 'entertainment':
        return Icons.movie;
      case 'ruházat':
      case 'clothing':
        return Icons.shopping_bag;
      case 'egészség':
      case 'health':
        return Icons.local_hospital;
      case 'oktatás':
      case 'education':
        return Icons.school;
      default:
        return Icons.shopping_cart;
    }
  }

  void _showFilterDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setModalState) => Container(
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom,
              left: 24,
              right: 24,
              top: 24,
            ),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Szűrők',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 20),
                
                // Típus szűrő
                Text('Típus:', style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                DropdownButton<String?>(
                  value: _selectedType,
                  isExpanded: true,
                  hint: Text('Válassz típust'),
                  items: [
                    DropdownMenuItem(value: null, child: Text('Összes')),
                    DropdownMenuItem(value: 'income', child: Text('Bevételek')),
                    DropdownMenuItem(value: 'expense', child: Text('Kiadások')),
                  ],
                  onChanged: (value) {
                    setModalState(() => _selectedType = value);
                  },
                ),
                SizedBox(height: 16),
                
                // Kategória szűrő
                Text('Kategória:', style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                TextField(
                  decoration: InputDecoration(
                    hintText: 'Kategória neve',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                  onChanged: (value) {
                    _selectedCategory = value.isEmpty ? null : value;
                  },
                ),
                SizedBox(height: 16),
                
                // Dátum szűrők
                Text('Időszak:', style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () async {
                          final date = await showDatePicker(
                            context: context,
                            initialDate: _startDate ?? DateTime.now(),
                            firstDate: DateTime(2020),
                            lastDate: DateTime.now(),
                          );
                          if (date != null) {
                            setModalState(() => _startDate = date);
                          }
                        },
                        child: Container(
                          padding: EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            _startDate != null 
                              ? _formatDate(_startDate!)
                              : 'Kezdő dátum',
                            style: TextStyle(
                              color: _startDate != null ? Colors.black : Colors.grey,
                            ),
                          ),
                        ),
                      ),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: InkWell(
                        onTap: () async {
                          final date = await showDatePicker(
                            context: context,
                            initialDate: _endDate ?? DateTime.now(),
                            firstDate: DateTime(2020),
                            lastDate: DateTime.now(),
                          );
                          if (date != null) {
                            setModalState(() => _endDate = date);
                          }
                        },
                        child: Container(
                          padding: EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            _endDate != null 
                              ? _formatDate(_endDate!)
                              : 'Vég dátum',
                            style: TextStyle(
                              color: _endDate != null ? Colors.black : Colors.grey,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 24),
                
                // Gombok
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          setModalState(() {
                            _selectedType = null;
                            _selectedCategory = null;
                            _startDate = null;
                            _endDate = null;
                          });
                        },
                        child: Text('Törlés'),
                      ),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.pop(context);
                          _loadTransactions(refresh: true);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Color(0xFF00D4A3),
                        ),
                        child: Text(
                          'Alkalmazás',
                          style: TextStyle(color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 20),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Tranzakciók',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        foregroundColor: Colors.black87,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFF00D4A3),
              Color(0xFFF0F8F0),
            ],
            stops: [0.0, 0.3],
          ),
        ),
        child: Column(
          children: [
            // Szűrő indikátorok
            if (_selectedType != null || _selectedCategory != null || _startDate != null || _endDate != null)
              Container(
                margin: EdgeInsets.all(16),
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.filter_list, size: 16, color: Color(0xFF00D4A3)),
                        SizedBox(width: 4),
                        Text('Aktív szűrők:', style: TextStyle(fontWeight: FontWeight.bold)),
                        Spacer(),
                        GestureDetector(
                          onTap: () {
                            setState(() {
                              _selectedType = null;
                              _selectedCategory = null;
                              _startDate = null;
                              _endDate = null;
                            });
                            _loadTransactions(refresh: true);
                          },
                          child: Text(
                            'Törlés',
                            style: TextStyle(
                              color: Color(0xFF00D4A3),
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        if (_selectedType != null)
                          _buildFilterChip(_selectedType == 'income' ? 'Bevételek' : 'Kiadások'),
                        if (_selectedCategory != null)
                          _buildFilterChip('Kategória: $_selectedCategory'),
                        if (_startDate != null)
                          _buildFilterChip('Kezdő: ${_formatDate(_startDate!)}'),
                        if (_endDate != null)
                          _buildFilterChip('Vég: ${_formatDate(_endDate!)}'),
                      ],
                    ),
                  ],
                ),
              ),
            
            // Tranzakciók lista
            Expanded(
              child: Container(
                margin: EdgeInsets.only(top: 8),
                decoration: BoxDecoration(
                  color: Color(0xFFF0F8F0),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: RefreshIndicator(
                  onRefresh: () => _loadTransactions(refresh: true),
                  color: Color(0xFF00D4A3),
                  child: _transactions.isEmpty && !_isLoading
                      ? _buildEmptyState()
                      : ListView.builder(
                          controller: _scrollController,
                          padding: EdgeInsets.only(top: 20, left: 16, right: 16, bottom: 100),
                          itemCount: _transactions.length + (_hasMore ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (index == _transactions.length) {
                              return _buildLoadingIndicator();
                            }
                            return _buildTransactionItem(_transactions[index]);
                          },
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: _buildQuickAddButton(),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }

  Widget _buildFilterChip(String label) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Color(0xFF00D4A3).withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Color(0xFF00D4A3).withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: Color(0xFF00D4A3),
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.receipt_long_outlined,
            size: 80,
            color: Colors.grey[400],
          ),
          SizedBox(height: 16),
          Text(
            'Nincsenek tranzakciók',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.grey[600],
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Adj hozzá tranzakciókat a gyors hozzáadás gombbal',
            style: TextStyle(
              color: Colors.grey[500],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingIndicator() {
    if (!_isLoading) return SizedBox.shrink();
    
    return Container(
      padding: EdgeInsets.all(16),
      child: Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
        ),
      ),
    );
  }

  Widget _buildTransactionItem(Map<String, dynamic> transaction) {
    final isExpense = transaction['isExpense'] as bool;
    final amount = transaction['amount'] as double;
    final date = transaction['date'] as DateTime;
    
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () {
          _showTransactionDetails(transaction);
        },
        child: Row(
          children: [
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: (isExpense ? Colors.red : Colors.green).withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                transaction['icon'] as IconData,
                color: isExpense ? Colors.red : Colors.green,
                size: 24,
              ),
            ),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    transaction['title'] as String,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    '${_formatDate(date)} • ${transaction['category']}',
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    '${transaction['main_account']} • ${transaction['sub_account_name']}',
                    style: TextStyle(
                      color: Colors.grey[500],
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  _formatCurrency(amount),
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: isExpense ? Colors.red : Colors.green,
                  ),
                ),
                Text(
                  _formatTime(date),
                  style: TextStyle(
                    color: Colors.grey[500],
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showTransactionDetails(Map<String, dynamic> transaction) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (BuildContext context) {
        return Container(
          padding: EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Tranzakció részletei',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              _buildDetailRow('Megnevezés:', transaction['title']),
              _buildDetailRow('Összeg:', _formatCurrency(transaction['amount'])),
              _buildDetailRow('Kategória:', transaction['category']),
              _buildDetailRow('Dátum:', _formatDate(transaction['date'])),
              _buildDetailRow('Főszámla:', transaction['main_account']),
              _buildDetailRow('Alszámla:', transaction['sub_account_name']),
              _buildDetailRow('Típus:', transaction['isExpense'] ? 'Kiadás' : 'Bevétel'),
              SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFF00D4A3),
                    padding: EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Text(
                    'Bezárás',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAddButton() {
    return Container(
      margin: EdgeInsets.only(bottom: 40),
      child: FloatingActionButton.extended(
        onPressed: _showQuickAddDialog,
        backgroundColor: Color(0xFF00D4A3),
        icon: Icon(Icons.add, color: Colors.white),
        label: Text(
          'Gyors hozzáadás',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  void _showQuickAddDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (BuildContext context) {
        return Container(
          padding: EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(20),
              topRight: Radius.circular(20),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Gyors hozzáadás',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => AddIncomesScreen(userId: widget.userId),
                          ),
                        );
                      },
                      icon: Icon(Icons.add, color: Colors.white),
                      label: Text('Bevétel', style: TextStyle(color: Colors.white)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Color(0xFF00D4A3),
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => AddExpensesScreen(userId: widget.userId),
                          ),
                        );
                      },
                      icon: Icon(Icons.remove, color: Colors.white),
                      label: Text('Kiadás', style: TextStyle(color: Colors.white)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent,
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  String _formatCurrency(double amount) {
    final absAmount = amount.abs();
    final sign = amount < 0 ? '-' : '';
    
    if (absAmount >= 1000000) {
      return '${sign}${(absAmount / 1000000).toStringAsFixed(1)}M Ft';
    } else if (absAmount >= 1000) {
      return '${sign}${(absAmount / 1000).toStringAsFixed(0)}k Ft';
    } else {
      return '${sign}${absAmount.toStringAsFixed(0)} Ft';
    }
  }

  String _formatDate(DateTime date) {
    return '${date.year}/${date.month.toString().padLeft(2, '0')}/${date.day.toString().padLeft(2, '0')}';
  }

  String _formatTime(DateTime date) {
    return '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}