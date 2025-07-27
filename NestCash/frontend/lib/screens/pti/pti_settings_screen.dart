// lib/screens/pti/pti_settings_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/pti_models.dart';
import 'package:frontend/services/pti_service.dart';

class PTISettingsScreen extends StatefulWidget {
  final String userId;

  const PTISettingsScreen({
    Key? key,
    required this.userId,
  }) : super(key: key);

  @override
  _PTISettingsScreenState createState() => _PTISettingsScreenState();
}

class _PTISettingsScreenState extends State<PTISettingsScreen> {
  final PTIService _ptiService = PTIService();
  final _formKey = GlobalKey<FormState>();
  final _anonymousNameController = TextEditingController();
  final _weeklyGoalController = TextEditingController();
  final _monthlyGoalController = TextEditingController();

  PTIUserSettings? _settings;
  bool _isLoading = true;
  bool _isSaving = false;
  String? _error;

  // Form values
  bool _showInGlobalRanking = true;
  bool _showInFriendsRanking = true;
  bool _isAnonymous = false;
  bool _notifyRankChange = true;
  bool _notifyWeeklySummary = true;
  bool _notifyAchievements = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  @override
  void dispose() {
    _anonymousNameController.dispose();
    _weeklyGoalController.dispose();
    _monthlyGoalController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final settings = await _ptiService.getSettings();
      if (settings != null) {
        setState(() {
          _settings = settings;
          _showInGlobalRanking = settings.showInGlobalRanking;
          _showInFriendsRanking = settings.showInFriendsRanking;
          _isAnonymous = settings.isAnonymous;
          _notifyRankChange = settings.notifyRankChange;
          _notifyWeeklySummary = settings.notifyWeeklySummary;
          _notifyAchievements = settings.notifyAchievements;
          
          _anonymousNameController.text = settings.anonymousName ?? '';
          _weeklyGoalController.text = settings.weeklyPtiGoal?.toString() ?? '';
          _monthlyGoalController.text = settings.monthlyPtiGoal?.toString() ?? '';
          
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Nem sikerült betölteni a beállításokat';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Hiba történt: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _saveSettings() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSaving = true;
      _error = null;
    });

    try {
      final updatedSettings = _settings!.copyWith(
        showInGlobalRanking: _showInGlobalRanking,
        showInFriendsRanking: _showInFriendsRanking,
        isAnonymous: _isAnonymous,
        anonymousName: _anonymousNameController.text.isEmpty 
            ? null 
            : _anonymousNameController.text,
        notifyRankChange: _notifyRankChange,
        notifyWeeklySummary: _notifyWeeklySummary,
        notifyAchievements: _notifyAchievements,
        weeklyPtiGoal: _weeklyGoalController.text.isEmpty 
            ? null 
            : double.tryParse(_weeklyGoalController.text),
        monthlyPtiGoal: _monthlyGoalController.text.isEmpty 
            ? null 
            : double.tryParse(_monthlyGoalController.text),
      );

      final result = await _ptiService.updateSettings(updatedSettings);
      
      if (result != null) {
        setState(() {
          _settings = result;
          _isSaving = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Beállítások sikeresen mentve!'),
            backgroundColor: Color(0xFF00D4A3),
          ),
        );
        
        Navigator.pop(context);
      } else {
        setState(() {
          _error = 'Nem sikerült menteni a beállításokat';
          _isSaving = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Hiba történt: $e';
        _isSaving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: Text(
          'PTI Beállítások',
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.bold,
          ),
        ),
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.black),
        actions: [
          if (!_isLoading && _settings != null)
            TextButton(
              onPressed: _isSaving ? null : _saveSettings,
              child: _isSaving
                  ? SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
                      ),
                    )
                  : Text(
                      'Mentés',
                      style: TextStyle(
                        color: Colors.black,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return Center(
        child: CircularProgressIndicator(
          valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF00D4A3)),
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            SizedBox(height: 16),
            Text(
              _error!,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadSettings,
              child: Text('Újrapróbálás'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Color(0xFF00D4A3),
              ),
            ),
          ],
        ),
      );
    }

    if (_settings == null) {
      return Center(
        child: Text(
          'Nincs beállítás adat',
          style: TextStyle(
            fontSize: 16,
            color: Colors.grey[600],
          ),
        ),
      );
    }

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Ranglista beállítások
            _buildSection(
              'Ranglista megjelenés',
              Icons.leaderboard,
              [
                _buildSwitchTile(
                  'Megjelenés globális ranglistán',
                  'Látható leszel a nyilvános ranglistán',
                  _showInGlobalRanking,
                  (value) => setState(() => _showInGlobalRanking = value),
                ),
                _buildSwitchTile(
                  'Megjelenés barátok ranglistáján',
                  'Látható leszel a barátaid számára',
                  _showInFriendsRanking,
                  (value) => setState(() => _showInFriendsRanking = value),
                ),
                _buildSwitchTile(
                  'Anonimizált megjelenés',
                  'Álnévvel jelensz meg a ranglistákon',
                  _isAnonymous,
                  (value) => setState(() => _isAnonymous = value),
                ),
                if (_isAnonymous) ...[
                  SizedBox(height: 8),
                  TextFormField(
                    controller: _anonymousNameController,
                    decoration: InputDecoration(
                      labelText: 'Álnév',
                      hintText: 'Adja meg az álnevét',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    validator: (value) {
                      if (_isAnonymous && (value == null || value.isEmpty)) {
                        return 'Anonimizált megjelenés esetén meg kell adni az álnevet';
                      }
                      if (value != null && value.length > 50) {
                        return 'Az álnév maximum 50 karakter lehet';
                      }
                      return null;
                    },
                  ),
                ],
              ],
            ),
            
            SizedBox(height: 24),
            
            // Értesítési beállítások
            _buildSection(
              'Értesítések',
              Icons.notifications,
              [
                _buildSwitchTile(
                  'Rangsor változás',
                  'Értesítés ha változik a helyezésed',
                  _notifyRankChange,
                  (value) => setState(() => _notifyRankChange = value),
                ),
                _buildSwitchTile(
                  'Heti összefoglaló',
                  'Heti PTI összefoglaló küldése',
                  _notifyWeeklySummary,
                  (value) => setState(() => _notifyWeeklySummary = value),
                ),
                _buildSwitchTile(
                  'PTI eredmények',
                  'Értesítés új PTI eredményekről',
                  _notifyAchievements,
                  (value) => setState(() => _notifyAchievements = value),
                ),
              ],
            ),
            
            SizedBox(height: 24),
            
            // Célok beállítása
            _buildSection(
              'PTI Célok',
              Icons.flag,
              [
                TextFormField(
                  controller: _weeklyGoalController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'Heti PTI cél',
                    hintText: 'pl. 75.0',
                    suffixText: 'PTI pont',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  validator: (value) {
                    if (value != null && value.isNotEmpty) {
                      final doubleValue = double.tryParse(value);
                      if (doubleValue == null) {
                        return 'Érvényes számot adjon meg';
                      }
                      if (doubleValue < 0 || doubleValue > 100) {
                        return 'A cél 0 és 100 között lehet';
                      }
                    }
                    return null;
                  },
                ),
                SizedBox(height: 16),
                TextFormField(
                  controller: _monthlyGoalController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'Havi PTI cél',
                    hintText: 'pl. 80.0',
                    suffixText: 'PTI pont',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  validator: (value) {
                    if (value != null && value.isNotEmpty) {
                      final doubleValue = double.tryParse(value);
                      if (doubleValue == null) {
                        return 'Érvényes számot adjon meg';
                      }
                      if (doubleValue < 0 || doubleValue > 100) {
                        return 'A cél 0 és 100 között lehet';
                      }
                    }
                    return null;
                  },
                ),
              ],
            ),
            
            SizedBox(height: 24),
            
            // Info kártya
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Color(0xFF00D4A3).withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Color(0xFF00D4A3).withOpacity(0.3),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.info_outline,
                    color: Color(0xFF00D4A3),
                    size: 24,
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'PTI Információ',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF00D4A3),
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'A PTI (Pénzügyi Tudatosság Index) 4 komponensből áll: Tanulás (30%), Szokások (30%), Kitűzők (20%), és Limitek (20%).',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[700],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, IconData icon, List<Widget> children) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: Color(0xFF00D4A3),
                size: 24,
              ),
              SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }

  Widget _buildSwitchTile(
    String title,
    String subtitle,
    bool value,
    ValueChanged<bool> onChanged,
  ) {
    return Container(
      margin: EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: Color(0xFF00D4A3),
          ),
        ],
      ),
    );
  }
}