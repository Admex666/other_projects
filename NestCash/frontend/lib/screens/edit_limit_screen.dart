// lib/screens/edit_limit_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/limit.dart';
import '../services/limit_service.dart';

class EditLimitScreen extends StatefulWidget {
  final String userId;
  final Limit limit;

  const EditLimitScreen({
    Key? key,
    required this.userId,
    required this.limit,
  }) : super(key: key);

  @override
  _EditLimitScreenState createState() => _EditLimitScreenState();
}

class _EditLimitScreenState extends State<EditLimitScreen> {
  final _formKey = GlobalKey<FormState>();
  final LimitService _limitService = LimitService();

  // Form controllers
  late final TextEditingController _nameController;
  late final TextEditingController _amountController;
  late final TextEditingController _notificationThresholdController;

  // Form values
  late LimitPeriod _selectedPeriod;
  late String? _selectedCategory;
  late String? _selectedMainAccount;
  late String? _selectedSubAccount;
  late bool _notifyOnExceed;
  late bool _isActive;

  // Options for dropdowns
  final List<String> _categories = [
    'Élelmiszer', 'Lakás', 'Közlekedés', 'Szórakozás', 
    'Egészség', 'Oktatás', 'Ruházat', 'Egyéb'
  ];
  
  final List<String> _mainAccounts = ['likvid', 'befektetes', 'megtakaritas'];

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    
    // Initialize controllers with current values
    _nameController = TextEditingController(text: widget.limit.name);
    _amountController = TextEditingController(text: widget.limit.amount.toStringAsFixed(0));
    _notificationThresholdController = TextEditingController(
      text: widget.limit.notificationThreshold?.toStringAsFixed(0) ?? '',
    );

    // Initialize form values
    _selectedPeriod = widget.limit.period;
    _selectedCategory = widget.limit.category;
    _selectedMainAccount = widget.limit.mainAccount;
    _selectedSubAccount = widget.limit.subAccountName;
    _notifyOnExceed = widget.limit.notifyOnExceed;
    _isActive = widget.limit.isActive;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    _notificationThresholdController.dispose();
    super.dispose();
  }

  Future<void> _updateLimit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final updateData = <String, dynamic>{
        'name': _nameController.text.trim(),
        'amount': double.parse(_amountController.text),
        'period': _selectedPeriod.value,
        'is_active': _isActive,
        'notify_on_exceed': _notifyOnExceed,
      };

      if (_notificationThresholdController.text.isNotEmpty) {
        updateData['notification_threshold'] = double.parse(_notificationThresholdController.text);
      }

      // Típus specifikus mezők hozzáadása
      if (widget.limit.type == LimitType.category && _selectedCategory != null) {
        updateData['category'] = _selectedCategory!;
      } else if (widget.limit.type == LimitType.account) {
        if (_selectedMainAccount != null) {
          updateData['main_account'] = _selectedMainAccount!;
        }
        if (_selectedSubAccount != null) {
          updateData['sub_account_name'] = _selectedSubAccount!;
        }
      }

      await _limitService.updateLimit(widget.limit.id, updateData);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Limit sikeresen frissítve'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
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
    List<TextInputFormatter>? inputFormatters,
    String? suffixText,
    String? helperText,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        inputFormatters: inputFormatters,
        style: TextStyle(
          fontSize: 16,
          color: Colors.black87,
        ),
        decoration: InputDecoration(
          labelText: labelText,
          hintText: hintText,
          helperText: helperText,
          suffixText: suffixText,
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
          hintText: hintText,
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

  Widget _buildTypeSpecificFields() {
    switch (widget.limit.type) {
      case LimitType.category:
        return _buildDropdownField(
          labelText: 'Kategória',
          icon: Icons.category,
          value: _selectedCategory,
          items: _categories,
          hintText: 'Válassz kategóriát',
          onChanged: (value) {
            setState(() {
              _selectedCategory = value;
            });
          },
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Kategória kiválasztása kötelező';
            }
            return null;
          },
        );

      case LimitType.account:
        return Column(
          children: [
            _buildDropdownField(
              labelText: 'Főszámla',
              icon: Icons.account_balance,
              value: _selectedMainAccount?.toUpperCase(),
              items: _mainAccounts.map((account) => account.toUpperCase()).toList(),
              hintText: 'Válassz főszámlát',
              onChanged: (value) {
                setState(() {
                  _selectedMainAccount = value?.toLowerCase();
                });
              },
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Főszámla kiválasztása kötelező';
                }
                return null;
              },
            ),
            _buildInputField(
              controller: TextEditingController(text: _selectedSubAccount ?? ''),
              labelText: 'Alszámla (opcionális)',
              hintText: 'Alszámla neve',
              icon: Icons.account_balance_wallet,
              validator: null,
            ),
          ],
        );

      case LimitType.spending:
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildUsageInfo() {
    if (widget.limit.currentSpending == null) return const SizedBox.shrink();

    final usagePercentage = widget.limit.usagePercentage ?? 0;
    final isExceeded = widget.limit.isExceeded;
    final isNearLimit = widget.limit.isNearLimit;

    Color progressColor = Colors.green;
    if (isExceeded) {
      progressColor = Colors.red;
    } else if (isNearLimit) {
      progressColor = Colors.orange;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: progressColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  Icons.analytics,
                  color: progressColor,
                  size: 24,
                ),
              ),
              SizedBox(width: 12),
              Text(
                'Aktuális felhasználás',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Költés: ${widget.limit.currentSpending!.toStringAsFixed(0)} ${widget.limit.currency}',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Colors.black87,
                ),
              ),
              Text(
                'Limit: ${widget.limit.amount.toStringAsFixed(0)} ${widget.limit.currency}',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: usagePercentage / 100,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(progressColor),
            minHeight: 6,
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${usagePercentage.toStringAsFixed(1)}% felhasználva',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: progressColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  widget.limit.statusText,
                  style: TextStyle(
                    fontSize: 12,
                    color: progressColor,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
          if (widget.limit.remainingAmount != null && widget.limit.remainingAmount! > 0) ...[
            const SizedBox(height: 8),
            Text(
              'Fennmaradó: ${widget.limit.remainingAmount!.toStringAsFixed(0)} ${widget.limit.currency}',
              style: TextStyle(
                fontSize: 14,
                color: Colors.green[700],
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ],
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
                      'Limit szerkesztése',
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
                          
                          // Használat információ
                          _buildUsageInfo(),

                          // Limit típusa (csak olvasható)
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(16),
                            margin: EdgeInsets.only(bottom: 16),
                            decoration: BoxDecoration(
                              color: Colors.grey[100],
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.grey[300]!),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.category, color: Colors.grey[600]),
                                SizedBox(width: 12),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Limit típusa',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.grey[600],
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      widget.limit.type.displayName,
                                      style: TextStyle(
                                        fontSize: 16,
                                        color: Colors.grey[700],
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          
                          // Limit neve
                          _buildInputField(
                            controller: _nameController,
                            labelText: 'Limit neve',
                            hintText: 'pl. Havi élelmiszer költségvetés',
                            icon: Icons.label,
                            validator: (value) {
                              if (value == null || value.trim().isEmpty) {
                                return 'Limit neve kötelező';
                              }
                              return null;
                            },
                          ),
                          
                          // Típus specifikus mezők
                          _buildTypeSpecificFields(),
                          
                          // Összeg
                          _buildInputField(
                            controller: _amountController,
                            labelText: 'Limit összeg',
                            hintText: '50000',
                            icon: Icons.attach_money,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(RegExp(r'[0-9]')),
                            ],
                            suffixText: 'HUF',
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Összeg megadása kötelező';
                              }
                              final amount = double.tryParse(value);
                              if (amount == null || amount <= 0) {
                                return 'Érvényes összeget adj meg';
                              }
                              return null;
                            },
                          ),
                          
                          // Időszak
                          Container(
                            margin: EdgeInsets.only(bottom: 16),
                            child: DropdownButtonFormField<LimitPeriod>(
                              decoration: InputDecoration(
                                labelText: 'Időszak',
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
                                prefixIcon: Icon(Icons.schedule, color: Colors.grey[600]),
                                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                              ),
                              value: _selectedPeriod,
                              items: LimitPeriod.values.map((period) {
                                return DropdownMenuItem(
                                  value: period,
                                  child: Text(period.displayName),
                                );
                              }).toList(),
                              onChanged: (value) {
                                setState(() {
                                  _selectedPeriod = value!;
                                });
                              },
                            ),
                          ),
                          
                          // Értesítési küszöb
                          _buildInputField(
                            controller: _notificationThresholdController,
                            labelText: 'Értesítési küszöb (%)',
                            hintText: '80',
                            icon: Icons.notifications,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(RegExp(r'[0-9]')),
                            ],
                            suffixText: '%',
                            helperText: 'Értesítés amikor eléri ezt a százalékot (opcionális)',
                            validator: (value) {
                              if (value != null && value.isNotEmpty) {
                                final threshold = double.tryParse(value);
                                if (threshold == null || threshold <= 0 || threshold > 100) {
                                  return '1 és 100 közötti számot adj meg';
                                }
                              }
                              return null;
                            },
                          ),
                          
                          // Értesítés túllépéskor
                          Container(
                            margin: EdgeInsets.only(bottom: 16),
                            padding: EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.grey[300]!),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.notification_important, color: Colors.grey[600]),
                                SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    'Értesítés küldése túllépéskor',
                                    style: TextStyle(
                                      fontSize: 16,
                                      color: Colors.black87,
                                    ),
                                  ),
                                ),
                                Switch(
                                  value: _notifyOnExceed,
                                  onChanged: (value) {
                                    setState(() {
                                      _notifyOnExceed = value ?? true;
                                    });
                                  },
                                  activeColor: Color(0xFF00D4AA),
                                ),
                              ],
                            ),
                          ),

                          // Limit aktív-e
                          Container(
                            margin: EdgeInsets.only(bottom: 24),
                            padding: EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.grey[300]!),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  _isActive ? Icons.toggle_on : Icons.toggle_off, 
                                  color: _isActive ? Color(0xFF00D4AA) : Colors.grey[600],
                                  size: 28,
                                ),
                                SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'Limit aktív',
                                        style: TextStyle(
                                          fontSize: 16,
                                          color: Colors.black87,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                      Text(
                                        _isActive 
                                            ? 'A limit jelenleg aktív' 
                                            : 'A limit jelenleg inaktív',
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.grey[600],
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Switch(
                                  value: _isActive,
                                  onChanged: (value) {
                                    setState(() {
                                      _isActive = value ?? true;
                                    });
                                  },
                                  activeColor: Color(0xFF00D4AA),
                                ),
                              ],
                            ),
                          ),
                          
                          // Mentés gomb
                          Container(
                            width: double.infinity,
                            height: 56,
                            child: ElevatedButton(
                              onPressed: _isLoading ? null : _updateLimit,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Color(0xFF00D4AA),
                                foregroundColor: Colors.white,
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(30),
                                ),
                              ),
                              child: _isLoading
                                  ? CircularProgressIndicator(color: Colors.white)
                                  : Text(
                                      'Limit frissítése',
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