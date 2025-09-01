// lib/screens/transactions_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/transaction_service.dart';
import 'package:frontend/screens/add_expenses_screen.dart';
import 'package:frontend/screens/add_incomes_screen.dart';
import 'package:frontend/screens/edit_transaction_screen.dart';
import 'package:intl/intl.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/utils/category_translate.dart';

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
  String _sortBy = 'date'; // 'date', 'amount', 'category', 'title'
  bool _sortDescending = true; // alapból legújabb először
  
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
    if (_scrollController.position.pixels >= 
        _scrollController.position.maxScrollExtent - 200 &&
        !_isLoading && _hasMore) {
      _loadMoreTransactions();
    }
  }

  void _editTransaction(Map<String, dynamic> transaction) {
    final isExpense = transaction['isExpense'] as bool;
    
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EditTransactionScreen(
          userId: widget.userId,
          transaction: transaction,
          isExpense: isExpense,
        ),
      ),
    ).then((result) {
      // Ha sikeres volt a módosítás, frissítsük a listát
      if (result == true) {
        _loadTransactions(refresh: true);
      }
    });
  }

void _deleteTransaction(Map<String, dynamic> transaction) {
  showDialog(
    context: context,
    builder: (BuildContext context) {
      return AlertDialog(
        title: Text('transactions_screen.dialogs.delete_transaction.title'.tr()),
        content: Text('transactions_screen.dialogs.delete_transaction.content'.tr(args: [transaction['title']])),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('transactions_screen.dialogs.delete_transaction.cancel_button'.tr()),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await _performDelete(transaction['id']);
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: Text('transactions_screen.dialogs.delete_transaction.delete_button'.tr()),
          ),
        ],
      );
    },
  );
}

Future<void> _performDelete(String transactionId) async {
    try {
      await _transactionService.deleteTransaction(transactionId);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('transactions_screen.snackbar.success_delete'.tr()),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
        _loadTransactions(refresh: true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('transactions_screen.snackbar.error_delete'.tr(args: [e.toString()])),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _loadTransactions({bool refresh = false}) async {
    // Megakadályozzuk a dupla betöltést
    if (_isLoading && !refresh) return;
    
    if (refresh) {
      setState(() {
        _transactions.clear();
        _currentSkip = 0;
        _hasMore = true;
        _isLoading = true; // Fontos: itt is beállítjuk
      });
    } else {
      setState(() => _isLoading = true);
    }

    try {
      final transactions = await _transactionService.getTransactions(
        limit: _pageSize,
        skip: _currentSkip,
        type: _selectedType,
        category: _selectedCategory,
        startDate: _startDate,
        endDate: _endDate,
      );

      // Csak akkor frissítjük az állapotot, ha még mounted
      if (!mounted) return;

      setState(() {
        if (refresh) {
          _transactions = _processTransactions(transactions);
        } else {
          _transactions.addAll(_processTransactions(transactions));
        }
        
        // Rendezés alkalmazása
        _sortTransactions();
        
        _hasMore = transactions.length == _pageSize;
        if (refresh) {
          _currentSkip = transactions.length;
        } else {
          _currentSkip += transactions.length;
        }
        _isLoading = false; // Itt állítjuk vissza
      });
    } catch (e) {
      print('Error loading transactions: $e');
      if (mounted) {
        setState(() {
          _isLoading = false; // Hiba esetén is visszaállítjuk
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('transactions_screen.snackbar.error_load'.tr(args: [e.toString()])),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _sortTransactions() {
    _transactions.sort((a, b) {
      int comparison = 0;
      
      switch (_sortBy) {
        case 'date':
          comparison = (a['date'] as DateTime).compareTo(b['date'] as DateTime);
          break;
        case 'amount':
          comparison = (a['amount'] as double).compareTo(b['amount'] as double);
          break;
        case 'category':
          comparison = (a['category'] as String).compareTo(b['category'] as String);
          break;
        case 'title':
          comparison = (a['title'] as String).compareTo(b['title'] as String);
          break;
      }
      
      return _sortDescending ? -comparison : comparison;
    });
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
        final description = transaction['description'] ?? transaction['leiras'] ?? 'transactions_screen.transaction_processing.default_description'.tr();
        final category = transaction['kategoria'] ?? transaction['category'] ?? 'transactions_screen.transaction_processing.default_category'.tr();
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
          'main_account': transaction['main_account'] ?? 'transactions_screen.transaction_processing.default_account'.tr(),
          'sub_account_name': transaction['sub_account_name'] ?? 'transactions_screen.transaction_processing.default_account'.tr(),
        };
      } catch (e) {
        print('Error processing transaction: $transaction, error: $e');
        return {
          'id': '',
          'title': 'transactions_screen.transaction_processing.invalid_transaction'.tr(),
          'amount': 0.0,
          'category': 'transactions_screen.transaction_processing.default_category'.tr(),
          'date': DateTime.now(),
          'isExpense': false,
          'icon': Icons.error,
          'main_account': 'transactions_screen.transaction_processing.default_account'.tr(),
          'sub_account_name': 'transactions_screen.transaction_processing.default_account'.tr(),
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
                  'transactions_screen.dialogs.filter.title'.tr(),
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 20),
                
                // Típus szűrő
                Text('transactions_screen.dialogs.filter.type_label'.tr(), style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                DropdownButton<String?>(
                  value: _selectedType,
                  isExpanded: true,
                  hint: Text('transactions_screen.dialogs.filter.all'.tr()),
                  items: [
                    DropdownMenuItem(value: null, child: Text('transactions_screen.dialogs.filter.all'.tr())),
                    DropdownMenuItem(value: 'income', child: Text('transactions_screen.income'.tr())),
                    DropdownMenuItem(value: 'expense', child: Text('transactions_screen.expense'.tr())),
                  ],
                  onChanged: (value) {
                    setModalState(() => _selectedType = value);
                  },
                ),
                SizedBox(height: 16),
                
                // Kategória szűrő
                Text('transactions_screen.dialogs.filter.category_label'.tr(), style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                TextField(
                  decoration: InputDecoration(
                    hintText: 'transactions_screen.dialogs.filter.category_hint'.tr(),
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
                Text('transactions_screen.dialogs.filter.date_label'.tr(), style: TextStyle(fontWeight: FontWeight.bold)),
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
                              : 'transactions_screen.dialogs.filter.start_date_hint'.tr(),
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
                              : 'transactions_screen.dialogs.filter.end_date_hint'.tr(),
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
                        child: Text('transactions_screen.dialogs.filter.clear_button'.tr()),
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
                          'transactions_screen.dialogs.filter.apply_button'.tr(),
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

  void _showSortDialog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setModalState) => Container(
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
                  'transactions_screen.dialogs.sort.title'.tr(),
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 20),
                
                Text('transactions_screen.dialogs.sort.sort_by_label'.tr(), style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 12),
                
                _buildSortOption(
                  'date', 
                  'transactions_screen.dialogs.sort.sort_options.date'.tr(), 
                  Icons.calendar_today,
                  setModalState,
                ),
                _buildSortOption(
                  'amount', 
                  'transactions_screen.dialogs.sort.sort_options.amount'.tr(), 
                  Icons.attach_money,
                  setModalState,
                ),
                _buildSortOption(
                  'category', 
                  'transactions_screen.dialogs.sort.sort_options.category'.tr(), 
                  Icons.category,
                  setModalState,
                ),
                _buildSortOption(
                  'title', 
                  'transactions_screen.dialogs.sort.sort_options.title'.tr(), 
                  Icons.title,
                  setModalState,
                ),
                
                SizedBox(height: 16),
                Divider(),
                SizedBox(height: 8),
                
                Row(
                  children: [
                    Icon(
                      _sortDescending ? Icons.arrow_downward : Icons.arrow_upward,
                      color: Color(0xFF00D4A3),
                    ),
                    SizedBox(width: 8),
                    Text(
                      'transactions_screen.dialogs.sort.order_label'.tr(),
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Row(
                        children: [
                          Expanded(
                            child: GestureDetector(
                              onTap: () {
                                setModalState(() {
                                  _sortDescending = true;
                                });
                              },
                              child: Container(
                                padding: EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                                decoration: BoxDecoration(
                                  color: _sortDescending ? Color(0xFF00D4A3) : Colors.grey[200],
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  'transactions_screen.dialogs.sort.descending'.tr(),
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    color: _sortDescending ? Colors.white : Colors.black,
                                    fontWeight: _sortDescending ? FontWeight.bold : FontWeight.normal,
                                  ),
                                ),
                              ),
                            ),
                          ),
                          SizedBox(width: 8),
                          Expanded(
                            child: GestureDetector(
                              onTap: () {
                                setModalState(() {
                                  _sortDescending = false;
                                });
                              },
                              child: Container(
                                padding: EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                                decoration: BoxDecoration(
                                  color: !_sortDescending ? Color(0xFF00D4A3) : Colors.grey[200],
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  'transactions_screen.dialogs.sort.ascending'.tr(),
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    color: !_sortDescending ? Colors.white : Colors.black,
                                    fontWeight: !_sortDescending ? FontWeight.bold : FontWeight.normal,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                
                SizedBox(height: 24),
                
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(context);
                      setState(() {
                        _sortTransactions();
                      });
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Color(0xFF00D4A3),
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: Text(
                      'transactions_screen.dialogs.sort.apply_button'.tr(),
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildSortOption(String value, String label, IconData icon, StateSetter setModalState) {
    final isSelected = _sortBy == value;
    
    return GestureDetector(
      onTap: () {
        setModalState(() {
          _sortBy = value;
        });
      },
      child: Container(
        margin: EdgeInsets.only(bottom: 8),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected ? Color(0xFF00D4A3).withOpacity(0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? Color(0xFF00D4A3) : Colors.grey[300]!,
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: isSelected ? Color(0xFF00D4A3) : Colors.grey[600],
            ),
            SizedBox(width: 12),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Color(0xFF00D4A3) : Colors.black,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            Spacer(),
            if (isSelected)
              Icon(
                Icons.check,
                color: Color(0xFF00D4A3),
                size: 20,
              ),
          ],
        ),
      ),
    );
  }

  String _getSortLabel() {
    return 'transactions_screen.sort_labels.${_sortBy}'.tr();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'transactions_screen.title'.tr(),
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        foregroundColor: Colors.black87,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.sort),
            onPressed: _showSortDialog,
            tooltip: 'transactions_screen.sort_tooltip'.tr(),
          ),
          IconButton(
            icon: Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
            tooltip: 'transactions_screen.filter_tooltip'.tr(),
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
                        Text('transactions_screen.active_filters'.tr(), style: TextStyle(fontWeight: FontWeight.bold)),
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
                            'transactions_screen.clear_filters'.tr(),
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
                          _buildFilterChip(_selectedType == 'income' ? 'transactions_screen.income'.tr() : 'transactions_screen.expense'.tr()),
                        if (_selectedCategory != null)
                          _buildFilterChip('${'transactions_screen.category'.tr()}: $_selectedCategory'),
                        if (_startDate != null)
                          _buildFilterChip('${'transactions_screen.start_date'.tr()}: ${_formatDate(_startDate!)}'),
                        if (_endDate != null)
                          _buildFilterChip('${'transactions_screen.end_date'.tr()}: ${_formatDate(_endDate!)}'),
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
                  onRefresh: () async {
                    // Explicit módon várjuk meg a befejezést
                    await _loadTransactions(refresh: true);
                  },
                  color: Color(0xFF00D4A3),
                  child: _transactions.isEmpty && !_isLoading
                      ? _buildEmptyState()
                      : ListView.builder(
                          controller: _scrollController,
                          padding: EdgeInsets.only(top: 20, left: 16, right: 16, bottom: 100),
                          itemCount: _transactions.length + (_hasMore && _isLoading ? 1 : 0),
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
            'transactions_screen.empty_state.title'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.grey[600],
            ),
          ),
          SizedBox(height: 8),
          Text(
            'transactions_screen.empty_state.description'.tr(),
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
                    '${_formatDate(date)} • ${CategoryTranslate.getLocalizedCategory(transaction['category']).tr()}',
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
                'transactions_screen.details.title'.tr(),
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 20),
              _buildDetailRow('transactions_screen.details.label_title'.tr(), transaction['title']),
              _buildDetailRow('transactions_screen.details.label_amount'.tr(), _formatCurrency(transaction['amount'])),
              _buildDetailRow('transactions_screen.details.label_category'.tr(), transaction['category']),
              _buildDetailRow('transactions_screen.details.label_date'.tr(), _formatDate(transaction['date'])),
              _buildDetailRow('transactions_screen.details.label_main_account'.tr(), transaction['main_account']),
              _buildDetailRow('transactions_screen.details.label_sub_account'.tr(), transaction['sub_account_name']),
              _buildDetailRow('transactions_screen.details.label_type'.tr(), transaction['isExpense'] ? 'transactions_screen.details.type_expense'.tr() : 'transactions_screen.details.type_income'.tr()),
              SizedBox(height: 20),
              // Cseréld le a bezárás gombot ezekkel a gombokkal:
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        _editTransaction(transaction);
                      },
                      icon: Icon(Icons.edit, color: Color(0xFF00D4A3)),
                      label: Text('transactions_screen.details.edit_button'.tr(), style: TextStyle(color: Color(0xFF00D4A3))),
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(color: Color(0xFF00D4A3)),
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        _deleteTransaction(transaction);
                      },
                      icon: Icon(Icons.delete, color: Colors.red),
                      label: Text('transactions_screen.details.delete_button'.tr(), style: TextStyle(color: Colors.red)),
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(color: Colors.red),
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.grey[300],
                    padding: EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: Text(
                    'transactions_screen.details.close_button'.tr(),
                    style: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
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
          'transactions_screen.quick_add.title'.tr(),
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
                'transactions_screen.quick_add.title'.tr(),
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
                      label: Text('transactions_screen.quick_add.income_button'.tr(), style: TextStyle(color: Colors.white)),
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
                      label: Text('transactions_screen.quick_add.expense_button'.tr(), style: TextStyle(color: Colors.white)),
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

    // Használjuk az intl csomag NumberFormat osztályát a szám tagolásához
    // A 'hu' locale használatával a magyar formátumot kapjuk, ami szóközzel tagol
    final formatter = NumberFormat('#,##0', 'hu'); 
    
    // Formázzuk az abszolút értéket
    final formattedAmount = formatter.format(absAmount);

    return '$sign$formattedAmount Ft';
  }

  String _formatDate(DateTime date) {
    return '${date.year}/${date.month.toString().padLeft(2, '0')}/${date.day.toString().padLeft(2, '0')}';
  }

  String _formatTime(DateTime date) {
    return '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}