// lib/screens/habits/add_habit_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:frontend/models/habit.dart';
import 'package:frontend/services/habit_service.dart';
import 'package:easy_localization/easy_localization.dart';

class AddHabitScreen extends StatefulWidget {
  final String userId;

  const AddHabitScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _AddHabitScreenState createState() => _AddHabitScreenState();
}

class _AddHabitScreenState extends State<AddHabitScreen>
    with TickerProviderStateMixin {
  final HabitService _habitService = HabitService();
  
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _targetValueController = TextEditingController();
  
  HabitCategory _selectedCategory = HabitCategory.other;
  TrackingType _selectedTrackingType = TrackingType.boolean;
  FrequencyType _selectedFrequency = FrequencyType.daily;
  
  bool _hasGoal = false;
  FrequencyType? _goalPeriod;
  
  bool _isLoading = false;
  
  late TabController _tabController;
  Map<HabitCategory, List<PredefinedHabit>>? _predefinedHabits;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadPredefinedHabits();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _titleController.dispose();
    _descriptionController.dispose();
    _targetValueController.dispose();
    super.dispose();
  }

  Future<void> _loadPredefinedHabits() async {
    try {
      final predefined = await _habitService.getPredefinedHabits();
      setState(() {
        _predefinedHabits = predefined;
      });
    } catch (e) {
      print('Error loading predefined habits: $e');
    }
  }

  Future<void> _createCustomHabit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final habit = Habit(
        id: '',
        userId: widget.userId,
        title: _titleController.text.trim(),
        description: _descriptionController.text.trim().isEmpty 
            ? null 
            : _descriptionController.text.trim(),
        category: _selectedCategory,
        trackingType: _selectedTrackingType,
        frequency: _selectedFrequency,
        hasGoal: _hasGoal,
        targetValue: _hasGoal && _targetValueController.text.isNotEmpty
            ? int.tryParse(_targetValueController.text)
            : null,
        goalPeriod: _hasGoal ? _goalPeriod : null,
        dailyTarget: null,
        isActive: true,
        streakCount: 0,
        bestStreak: 0,
        createdAt: DateTime.now(),
      );

      await _habitService.createHabit(habit);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('habit_creation_success'.tr()),
            backgroundColor: const Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('error_occurred'.tr(namedArgs: {'error': e.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _createPredefinedHabit(
    HabitCategory category,
    int habitIndex,
  ) async {
    setState(() => _isLoading = true);

    try {
      await _habitService.createHabitFromPredefined(category, habitIndex);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('predefined_habit_add_success'.tr()),
            backgroundColor: const Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('error'.tr(namedArgs: {'error': e.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() => _isLoading = false);
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
    int maxLines = 1,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        inputFormatters: inputFormatters,
        onChanged: onChanged,
        maxLines: maxLines,
        style: const TextStyle(
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
            borderSide: const BorderSide(color: Color(0xFF00D4AA), width: 2),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          filled: true,
          fillColor: Colors.white,
          prefixIcon: Icon(icon, color: Colors.grey[600]),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        validator: validator,
      ),
    );
  }

  Widget _buildDropdownField<T>({
    required String labelText,
    required IconData icon,
    required T? value,
    required List<T> items,
    required void Function(T?) onChanged,
    String? Function(T?)? validator,
    String? hintText,
    required String Function(T) displayText,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: DropdownButtonFormField<T>(
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
            borderSide: const BorderSide(color: Color(0xFF00D4AA), width: 2),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          filled: true,
          fillColor: Colors.white,
          prefixIcon: Icon(icon, color: Colors.grey[600]),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        items: items.map((T item) {
          return DropdownMenuItem<T>(
            value: item,
            child: Text(displayText(item)),
          );
        }).toList(),
        value: value,
        onChanged: onChanged,
        validator: validator,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(
                      Icons.arrow_back,
                      color: Colors.black87,
                      size: 24,
                    ),
                  ),
                  Expanded(
                    child: Text(
                      'add_habit_title'.tr(),
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),
            ),
            
            // Tab Bar
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 20),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.1),
                borderRadius: BorderRadius.circular(25),
              ),
              child: TabBar(
                controller: _tabController,
                indicator: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(25),
                ),
                labelColor: Colors.black87,
                unselectedLabelColor: Colors.black54,
                tabs: [
                  Tab(text: 'custom_habit'.tr()),
                  Tab(text: 'predefined_templates'.tr()),
                ],
              ),
            ),
            
            const SizedBox(height: 20),
            
            // Content Container
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: const BoxDecoration(
                  color: Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: _isLoading
                    ? const Center(
                        child: CircularProgressIndicator(
                          color: Color(0xFF00D4AA),
                        ),
                      )
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildCustomHabitTab(),
                          _buildPredefinedHabitsTab(),
                        ],
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCustomHabitTab() {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 10),
              
              // Szokás neve
              _buildInputField(
                controller: _titleController,
                labelText: 'habit_name'.tr(),
                hintText: 'habit_name_hint'.tr(),
                icon: Icons.psychology,
                validator: (value) {
                  if (value?.trim().isEmpty ?? true) {
                    return 'habit_name_required'.tr();
                  }
                  return null;
                },
              ),
              
              // Leírás
              _buildInputField(
                controller: _descriptionController,
                labelText: 'description_optional'.tr(),
                hintText: 'description_hint'.tr(),
                icon: Icons.description,
                maxLines: 3,
              ),
              
              // Kategória
              _buildDropdownField<HabitCategory>(
                labelText: 'category'.tr(),
                icon: Icons.category,
                value: _selectedCategory,
                items: HabitCategory.values,
                hintText: 'select_category'.tr(),
                onChanged: (value) {
                  setState(() {
                    _selectedCategory = value!;
                  });
                },
                displayText: (category) => category.value,
              ),
              
              // Követés típusa
              _buildDropdownField<TrackingType>(
                labelText: 'tracking_type'.tr(),
                icon: Icons.track_changes,
                value: _selectedTrackingType,
                items: TrackingType.values,
                hintText: 'select_tracking_type'.tr(),
                onChanged: (value) {
                  setState(() {
                    _selectedTrackingType = value!;
                  });
                },
                displayText: (type) => _getTrackingTypeLabel(type),
              ),
              
              // Gyakoriság
              _buildDropdownField<FrequencyType>(
                labelText: 'frequency'.tr(),
                icon: Icons.schedule,
                value: _selectedFrequency,
                items: FrequencyType.values,
                hintText: 'select_frequency'.tr(),
                onChanged: (value) {
                  setState(() {
                    _selectedFrequency = value!;
                  });
                },
                displayText: (frequency) => frequency.displayName,
              ),
              
              // Cél beállítása
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Icon(Icons.flag, color: Colors.grey[600]),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'set_goal'.tr(),
                            style: const TextStyle(
                              fontSize: 16,
                              color: Colors.black87,
                            ),
                          ),
                        ),
                        Switch(
                          value: _hasGoal,
                          onChanged: (value) {
                            setState(() {
                              _hasGoal = value;
                              if (!_hasGoal) {
                                _goalPeriod = null;
                                _targetValueController.clear();
                              }
                            });
                          },
                          activeColor: const Color(0xFF00D4AA),
                        ),
                      ],
                    ),
                    
                    if (_hasGoal) ...[
                      const SizedBox(height: 16),
                      
                      _buildInputField(
                        controller: _targetValueController,
                        labelText: _selectedTrackingType == TrackingType.boolean 
                            ? 'goal_days_count'.tr()
                            : 'goal_value'.tr(),
                        hintText: _selectedTrackingType == TrackingType.boolean 
                            ? 'goal_days_hint'.tr()
                            : 'goal_value_hint'.tr(),
                        icon: Icons.adjust,
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.allow(RegExp(r'[0-9]')),
                        ],
                        validator: _hasGoal ? (value) {
                          if (value?.trim().isEmpty ?? true) {
                            return 'goal_value_required'.tr();
                          }
                          final intValue = int.tryParse(value!);
                          if (intValue == null || intValue <= 0) {
                            return 'goal_value_invalid'.tr();
                          }
                          return null;
                        } : null,
                      ),
                      
                      _buildDropdownField<FrequencyType>(
                        labelText: 'goal_period'.tr(),
                        icon: Icons.date_range,
                        value: _goalPeriod,
                        items: FrequencyType.values,
                        hintText: 'select_goal_period'.tr(),
                        onChanged: (value) {
                          setState(() {
                            _goalPeriod = value;
                          });
                        },
                        displayText: (frequency) => frequency.displayName,
                        validator: _hasGoal ? (value) {
                          if (value == null) {
                            return 'goal_period_required'.tr();
                          }
                          return null;
                        } : null,
                      ),
                    ],
                  ],
                ),
              ),
              
              // Létrehozás gomb
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _createCustomHabit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00D4AA),
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text(
                          'create_habit_button'.tr(),
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                ),
              ),
              
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPredefinedHabitsTab() {
    if (_predefinedHabits == null) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00D4AA)));
    }

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 10),
            
            Text(
              'predefined_selection_title'.tr(),
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
              ),
            ),
            
            const SizedBox(height: 16),
            
            ..._predefinedHabits!.entries.map((entry) {
              final category = entry.key;
              final habits = entry.value;
              
              return _buildPredefinedCategorySection(category, habits);
            }).toList(),
            
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildPredefinedCategorySection(
    HabitCategory category,
    List<PredefinedHabit> habits,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ExpansionTile(
        title: Text(
          category.value,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: _getCategoryColor(category).withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            _getCategoryIcon(category),
            color: _getCategoryColor(category),
            size: 20,
          ),
        ),
        children: habits.asMap().entries.map((entry) {
          final index = entry.key;
          final habit = entry.value;
          
          return Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: ListTile(
              title: Text(
                habit.title,
                style: const TextStyle(
                  fontWeight: FontWeight.w500,
                  fontSize: 15,
                ),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 4),
                  Text(
                    habit.description,
                    style: const TextStyle(fontSize: 13),
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      habit.frequency.displayName,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue[700],
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
              trailing: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF00D4AA),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: IconButton(
                  onPressed: () => _createPredefinedHabit(category, index),
                  icon: const Icon(Icons.add, color: Colors.white),
                  tooltip: 'add_habit_tooltip'.tr(),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  String _getTrackingTypeLabel(TrackingType type) {
    switch (type) {
      case TrackingType.boolean:
        return 'tracking_type_boolean'.tr();
      case TrackingType.numeric:
        return 'tracking_type_numeric'.tr();
    }
  }

  IconData _getCategoryIcon(HabitCategory category) {
    switch (category) {
      case HabitCategory.financial:
        return Icons.account_balance_wallet;
      case HabitCategory.savings:
        return Icons.savings;
      case HabitCategory.investment:
        return Icons.trending_up;
      case HabitCategory.other:
        return Icons.category;
    }
  }

  Color _getCategoryColor(HabitCategory category) {
    switch (category) {
      case HabitCategory.financial:
        return Colors.green;
      case HabitCategory.savings:
        return Colors.blue;
      case HabitCategory.investment:
        return Colors.purple;
      case HabitCategory.other:
        return Colors.grey;
    }
  }
}