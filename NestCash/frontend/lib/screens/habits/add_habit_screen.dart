// lib/screens/habits/add_habit_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:frontend/models/habit.dart';
import 'package:frontend/services/habit_service.dart';

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
          const SnackBar(
            content: Text('Szokás sikeresen létrehozva!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba: $e'),
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
          const SnackBar(
            content: Text('Szokás sikeresen hozzáadva!'),
            backgroundColor: Color(0xFF00D4AA),
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba: $e'),
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
      margin: EdgeInsets.only(bottom: 16),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        inputFormatters: inputFormatters,
        onChanged: onChanged,
        maxLines: maxLines,
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
      margin: EdgeInsets.only(bottom: 16),
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
                      'Új szokás létrehozása',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  SizedBox(width: 48),
                ],
              ),
            ),
            
            // Tab Bar
            Container(
              margin: EdgeInsets.symmetric(horizontal: 20),
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
                tabs: const [
                  Tab(text: 'Egyéni'),
                  Tab(text: 'Sablonok'),
                ],
              ),
            ),
            
            SizedBox(height: 20),
            
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
                child: _isLoading
                    ? Center(
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
        padding: EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(height: 10),
              
              // Szokás neve
              _buildInputField(
                controller: _titleController,
                labelText: 'Szokás neve',
                hintText: 'pl. Napi séta',
                icon: Icons.psychology,
                validator: (value) {
                  if (value?.trim().isEmpty ?? true) {
                    return 'A szokás neve kötelező';
                  }
                  return null;
                },
              ),
              
              // Leírás
              _buildInputField(
                controller: _descriptionController,
                labelText: 'Leírás (opcionális)',
                hintText: 'Rövid leírás a szokásról...',
                icon: Icons.description,
                maxLines: 3,
              ),
              
              // Kategória
              _buildDropdownField<HabitCategory>(
                labelText: 'Kategória',
                icon: Icons.category,
                value: _selectedCategory,
                items: HabitCategory.values,
                hintText: 'Válassz kategóriát',
                onChanged: (value) {
                  setState(() {
                    _selectedCategory = value!;
                  });
                },
                displayText: (category) => category.value,
              ),
              
              // Követés típusa
              _buildDropdownField<TrackingType>(
                labelText: 'Követés típusa',
                icon: Icons.track_changes,
                value: _selectedTrackingType,
                items: TrackingType.values,
                hintText: 'Válassz követési típust',
                onChanged: (value) {
                  setState(() {
                    _selectedTrackingType = value!;
                  });
                },
                displayText: (type) => _getTrackingTypeLabel(type),
              ),
              
              // Gyakoriság
              _buildDropdownField<FrequencyType>(
                labelText: 'Gyakoriság',
                icon: Icons.schedule,
                value: _selectedFrequency,
                items: FrequencyType.values,
                hintText: 'Válassz gyakoriságot',
                onChanged: (value) {
                  setState(() {
                    _selectedFrequency = value!;
                  });
                },
                displayText: (frequency) => frequency.displayName,
              ),
              
              // Cél beállítása
              Container(
                margin: EdgeInsets.only(bottom: 16),
                padding: EdgeInsets.all(16),
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
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Cél beállítása',
                            style: TextStyle(
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
                          activeColor: Color(0xFF00D4AA),
                        ),
                      ],
                    ),
                    
                    if (_hasGoal) ...[
                      SizedBox(height: 16),
                      
                      _buildInputField(
                        controller: _targetValueController,
                        labelText: _selectedTrackingType == TrackingType.boolean 
                            ? 'Cél napok száma'
                            : 'Cél érték',
                        hintText: _selectedTrackingType == TrackingType.boolean 
                            ? 'pl. 20'
                            : 'pl. 10000',
                        icon: Icons.adjust,
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          FilteringTextInputFormatter.allow(RegExp(r'[0-9]')),
                        ],
                        validator: _hasGoal ? (value) {
                          if (value?.trim().isEmpty ?? true) {
                            return 'A cél érték kötelező';
                          }
                          final intValue = int.tryParse(value!);
                          if (intValue == null || intValue <= 0) {
                            return 'Érvényes pozitív számot adj meg';
                          }
                          return null;
                        } : null,
                      ),
                      
                      _buildDropdownField<FrequencyType>(
                        labelText: 'Cél időszaka',
                        icon: Icons.date_range,
                        value: _goalPeriod,
                        items: FrequencyType.values,
                        hintText: 'Válassz időszakot',
                        onChanged: (value) {
                          setState(() {
                            _goalPeriod = value;
                          });
                        },
                        displayText: (frequency) => frequency.displayName,
                        validator: _hasGoal ? (value) {
                          if (value == null) {
                            return 'Cél időszak kiválasztása kötelező';
                          }
                          return null;
                        } : null,
                      ),
                    ],
                  ],
                ),
              ),
              
              // Létrehozás gomb
              Container(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _createCustomHabit,
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
                          'Szokás létrehozása',
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
    );
  }

  Widget _buildPredefinedHabitsTab() {
    if (_predefinedHabits == null) {
      return Center(child: CircularProgressIndicator(color: Color(0xFF00D4AA)));
    }

    return SingleChildScrollView(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(height: 10),
            
            Text(
              'Válassz a készített sablonokból:',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
              ),
            ),
            
            SizedBox(height: 16),
            
            ..._predefinedHabits!.entries.map((entry) {
              final category = entry.key;
              final habits = entry.value;
              
              return _buildPredefinedCategorySection(category, habits);
            }).toList(),
            
            SizedBox(height: 30),
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
      margin: EdgeInsets.only(bottom: 16),
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
      child: ExpansionTile(
        title: Text(
          category.value,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
        leading: Container(
          padding: EdgeInsets.all(8),
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
            margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: ListTile(
              title: Text(
                habit.title,
                style: TextStyle(
                  fontWeight: FontWeight.w500,
                  fontSize: 15,
                ),
              ),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(height: 4),
                  Text(
                    habit.description,
                    style: TextStyle(fontSize: 13),
                  ),
                  SizedBox(height: 6),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 3),
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
                  color: Color(0xFF00D4AA),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: IconButton(
                  onPressed: () => _createPredefinedHabit(category, index),
                  icon: Icon(Icons.add, color: Colors.white),
                  tooltip: 'Szokás hozzáadása',
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
        return 'Igen/Nem (Boolean)';
      case TrackingType.numeric:
        return 'Numerikus érték';
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