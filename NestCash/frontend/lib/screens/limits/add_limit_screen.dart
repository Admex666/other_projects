// lib/screens/add_limit_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:frontend/models/limit.dart';
import 'package:frontend/services/limit_service.dart';
import 'package:easy_localization/easy_localization.dart';

class AddLimitScreen extends StatefulWidget {
  final String userId;

  const AddLimitScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _AddLimitScreenState createState() => _AddLimitScreenState();
}

class _AddLimitScreenState extends State<AddLimitScreen> {
  final _formKey = GlobalKey<FormState>();
  final LimitService _limitService = LimitService();

  // Form controllers
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  final _notificationThresholdController = TextEditingController();

  // Form values
  LimitType _selectedType = LimitType.spending;
  LimitPeriod _selectedPeriod = LimitPeriod.monthly;
  String? _selectedCategory;
  String? _selectedMainAccount;
  String? _selectedSubAccount;
  bool _notifyOnExceed = true;

  // Options for dropdowns
  final List<String> _categories = [
    'Élelmiszer', 'Lakás', 'Közlekedés', 'Szórakozás',
    'Egészség', 'Oktatás', 'Ruházat', 'Egyéb'
  ];

  final List<String> _mainAccounts = ['likvid', 'befektetes', 'megtakaritas'];

  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    _notificationThresholdController.dispose();
    super.dispose();
  }

  Future<void> _saveLimit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final limitData = {
        'name': _nameController.text.trim(),
        'type': _selectedType.value,
        'amount': double.parse(_amountController.text),
        'period': _selectedPeriod.value,
        'currency': 'HUF',
        'notify_on_exceed': _notifyOnExceed,
        if (_notificationThresholdController.text.isNotEmpty)
          'notification_threshold': double.parse(_notificationThresholdController.text),
      };

      // Típus specifikus mezők hozzáadása
      if (_selectedType == LimitType.category && _selectedCategory != null) {
        limitData['category'] = _selectedCategory!;
      } else if (_selectedType == LimitType.account) {
        if (_selectedMainAccount != null) {
          limitData['main_account'] = _selectedMainAccount!;
        }
        if (_selectedSubAccount != null) {
          limitData['sub_account_name'] = _selectedSubAccount!;
        }
      }

      await _limitService.createLimit(limitData);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('addLimitScreen.successMessage'.tr()),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('addLimitScreen.errorMessage'.tr(namedArgs: {'error': e.toString()})),
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
    void Function(String)? onChanged,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        inputFormatters: inputFormatters,
        onChanged: onChanged,
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
    switch (_selectedType) {
      case LimitType.category:
        return _buildDropdownField(
          labelText: 'addLimitScreen.category.label'.tr(),
          icon: Icons.category,
          value: _selectedCategory,
          items: _categories,
          hintText: 'addLimitScreen.category.hint'.tr(),
          onChanged: (value) {
            setState(() {
              _selectedCategory = value;
            });
          },
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'addLimitScreen.category.validator'.tr();
            }
            return null;
          },
        );

      case LimitType.account:
        return Column(
          children: [
            _buildDropdownField(
              labelText: 'addLimitScreen.mainAccount.label'.tr(),
              icon: Icons.account_balance,
              value: _selectedMainAccount?.toUpperCase(),
              items: _mainAccounts.map((account) => account.toUpperCase()).toList(),
              hintText: 'addLimitScreen.mainAccount.hint'.tr(),
              onChanged: (value) {
                setState(() {
                  _selectedMainAccount = value?.toLowerCase();
                  _selectedSubAccount = null; // Reset sub account
                });
              },
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'addLimitScreen.mainAccount.validator'.tr();
                }
                return null;
              },
            ),
            _buildInputField(
              controller: TextEditingController(text: _selectedSubAccount ?? ''),
              labelText: 'addLimitScreen.subAccount.label'.tr(),
              hintText: 'addLimitScreen.subAccount.hint'.tr(),
              icon: Icons.account_balance_wallet,
              onChanged: (value) {
                _selectedSubAccount = value.isEmpty ? null : value;
              },
            ),
          ],
        );

      case LimitType.spending:
        return const SizedBox.shrink();
    }
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
                      'addLimitScreen.title'.tr(),
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

                          // Limit neve
                          _buildInputField(
                            controller: _nameController,
                            labelText: 'addLimitScreen.limitName.label'.tr(),
                            hintText: 'addLimitScreen.limitName.hint'.tr(),
                            icon: Icons.label,
                            validator: (value) {
                              if (value == null || value.trim().isEmpty) {
                                return 'addLimitScreen.limitName.validator'.tr();
                              }
                              return null;
                            },
                          ),

                          // Limit típusa
                          Container(
                            margin: EdgeInsets.only(bottom: 16),
                            child: DropdownButtonFormField<LimitType>(
                              decoration: InputDecoration(
                                labelText: 'addLimitScreen.limitType.label'.tr(),
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
                                prefixIcon: Icon(Icons.tune, color: Colors.grey[600]),
                                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                              ),
                              value: _selectedType,
                              items: LimitType.values.map((type) {
                                return DropdownMenuItem(
                                  value: type,
                                  child: Text('addLimitScreen.limitType.types.${type.name}'.tr()),
                                );
                              }).toList(),
                              onChanged: (value) {
                                setState(() {
                                  _selectedType = value!;
                                  _selectedCategory = null;
                                  _selectedMainAccount = null;
                                  _selectedSubAccount = null;
                                });
                              },
                            ),
                          ),

                          // Típus specifikus mezők
                          _buildTypeSpecificFields(),

                          // Összeg
                          _buildInputField(
                            controller: _amountController,
                            labelText: 'addLimitScreen.amount.label'.tr(),
                            hintText: 'addLimitScreen.amount.hint'.tr(),
                            icon: Icons.attach_money,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(RegExp(r'[0-9]')),
                            ],
                            suffixText: 'HUF',
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'addLimitScreen.amount.validatorRequired'.tr();
                              }
                              final amount = double.tryParse(value);
                              if (amount == null || amount <= 0) {
                                return 'addLimitScreen.amount.validatorValid'.tr();
                              }
                              return null;
                            },
                          ),

                          // Időszak
                          Container(
                            margin: EdgeInsets.only(bottom: 16),
                            child: DropdownButtonFormField<LimitPeriod>(
                              decoration: InputDecoration(
                                labelText: 'addLimitScreen.period.label'.tr(),
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
                                  child: Text('addLimitScreen.period.periods.${period.name}'.tr()),
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
                            labelText: 'addLimitScreen.notificationThreshold.label'.tr(),
                            hintText: 'addLimitScreen.notificationThreshold.hint'.tr(),
                            icon: Icons.notifications,
                            keyboardType: TextInputType.number,
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(RegExp(r'[0-9]')),
                            ],
                            suffixText: '%',
                            helperText: 'addLimitScreen.notificationThreshold.helper'.tr(),
                            validator: (value) {
                              if (value != null && value.isNotEmpty) {
                                final threshold = double.tryParse(value);
                                if (threshold == null || threshold <= 0 || threshold > 100) {
                                  return 'addLimitScreen.notificationThreshold.validator'.tr();
                                }
                              }
                              return null;
                            },
                          ),

                          // Értesítés túllépéskor
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
                                Icon(Icons.notification_important, color: Colors.grey[600]),
                                SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    'addLimitScreen.notifyOnExceed.label'.tr(),
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
                                      _notifyOnExceed = value;
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
                              onPressed: _isLoading ? null : _saveLimit,
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
                                      'addLimitScreen.createButton'.tr(),
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