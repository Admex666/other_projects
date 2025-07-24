// lib/screens/forum/forum_settings_screen.dart
import 'package:flutter/material.dart';
import 'package:frontend/services/forum_service.dart';

class ForumSettingsScreen extends StatefulWidget {
  const ForumSettingsScreen({Key? key}) : super(key: key);

  @override
  _ForumSettingsScreenState createState() => _ForumSettingsScreenState();
}

class _ForumSettingsScreenState extends State<ForumSettingsScreen> {
  final ForumService _forumService = ForumService();
  
  bool _isLoading = true;
  bool _isSaving = false;
  
  // Settings data
  String _defaultPrivacyLevel = 'public';
  Map<String, bool> _notificationsEnabled = {
    'likes': true,
    'comments': true,
    'follows': true,
    'mentions': true,
  };
  
  // Stats data
  Map<String, dynamic> _stats = {};

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _loadStats();
  }

  Future<void> _loadSettings() async {
    try {
      final settings = await _forumService.getForumSettings();
      
      setState(() {
        _defaultPrivacyLevel = settings['default_privacy_level'] ?? 'public';
        _notificationsEnabled = Map<String, bool>.from(
          settings['notifications_enabled'] ?? _notificationsEnabled
        );
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a beállítások betöltésekor: $e')),
      );
    }
  }

  Future<void> _loadStats() async {
    try {
      final stats = await _forumService.getForumStats();
      setState(() {
        _stats = stats;
      });
    } catch (e) {
      // Stats loading error is not critical
      print('Stats loading error: $e');
    }
  }

  Future<void> _saveSettings() async {
    setState(() {
      _isSaving = true;
    });

    try {
      await _forumService.updateForumSettings(
        defaultPrivacyLevel: _defaultPrivacyLevel,
        notificationsEnabled: _notificationsEnabled,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Beállítások sikeresen mentve!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hiba a beállítások mentésekor: $e')),
      );
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFF5F5F5),
      appBar: AppBar(
        backgroundColor: Color(0xFF00D4A3),
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Fórum beállítások',
          style: TextStyle(
            color: Colors.black87,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          if (!_isLoading)
            TextButton(
              onPressed: _isSaving ? null : _saveSettings,
              child: _isSaving
                  ? SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.black87,
                      ),
                    )
                  : Text(
                      'Mentés',
                      style: TextStyle(
                        color: Colors.black87,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
        ],
      ),
      body: _isLoading
          ? Center(
              child: CircularProgressIndicator(
                color: Color(0xFF00D4AA),
              ),
            )
          : SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Statistics section
                  if (_stats.isNotEmpty) ...[
                    _buildStatsSection(),
                    SizedBox(height: 24),
                  ],

                  // Privacy settings
                  _buildPrivacySection(),
                  
                  SizedBox(height: 24),
                  
                  // Notification settings
                  _buildNotificationSection(),
                  
                  SizedBox(height: 24),
                  
                  // Account actions
                  _buildAccountActionsSection(),
                ],
              ),
            ),
    );
  }

  Widget _buildStatsSection() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
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
              Icon(
                Icons.analytics,
                color: Color(0xFF00D4AA),
                size: 24,
              ),
              SizedBox(width: 12),
              Text(
                'Statisztikák',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          
          SizedBox(height: 16),
          
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  'Posztjaim',
                  _stats['posts_count']?.toString() ?? '0',
                  Icons.article,
                  Colors.blue,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  'Kedvelések',
                  _stats['likes_received']?.toString() ?? '0',
                  Icons.favorite,
                  Colors.red,
                ),
              ),
            ],
          ),
          
          SizedBox(height: 12),
          
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  'Kommentek',
                  _stats['comments_count']?.toString() ?? '0',
                  Icons.comment,
                  Colors.green,
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: _buildStatCard(
                  'Követők',
                  _stats['followers_count']?.toString() ?? '0',
                  Icons.people,
                  Colors.purple,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color: color,
            size: 24,
          ),
          SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          SizedBox(height: 4),
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildPrivacySection() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
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
              Icon(
                Icons.privacy_tip,
                color: Color(0xFF00D4AA),
                size: 24,
              ),
              SizedBox(width: 12),
              Text(
                'Adatvédelem',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          
          SizedBox(height: 16),
          
          Text(
            'Alapértelmezett láthatóság új posztokhoz:',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.grey[700],
            ),
          ),
          
          SizedBox(height: 12),
          
          Column(
            children: [
              RadioListTile<String>(
                title: Row(
                  children: [
                    Icon(Icons.public, size: 18, color: Colors.green),
                    SizedBox(width: 8),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Nyilvános'),
                        Text(
                          'Mindenki láthatja',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ],
                ),
                value: 'public',
                groupValue: _defaultPrivacyLevel,
                onChanged: (value) => setState(() => _defaultPrivacyLevel = value!),
                contentPadding: EdgeInsets.zero,
              ),
              
              RadioListTile<String>(
                title: Row(
                  children: [
                    Icon(Icons.group, size: 18, color: Colors.orange),
                    SizedBox(width: 8),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Barátok'),
                        Text(
                          'Csak követőid láthatják',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ],
                ),
                value: 'friends',
                groupValue: _defaultPrivacyLevel,
                onChanged: (value) => setState(() => _defaultPrivacyLevel = value!),
                contentPadding: EdgeInsets.zero,
              ),
              
              RadioListTile<String>(
                title: Row(
                  children: [
                    Icon(Icons.lock, size: 18, color: Colors.red),
                    SizedBox(width: 8),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Privát'),
                        Text(
                          'Csak te láthatod',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ],
                ),
                value: 'private',
                groupValue: _defaultPrivacyLevel,
                onChanged: (value) => setState(() => _defaultPrivacyLevel = value!),
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationSection() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
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
              Icon(
                Icons.notifications,
                color: Color(0xFF00D4AA),
                size: 24,
              ),
              SizedBox(width: 12),
              Text(
                'Értesítések',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          
          SizedBox(height: 16),
          
          Text(
            'Értesítést szeretnél kapni ezekről:',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.grey[700],
            ),
          ),
          
          SizedBox(height: 12),
          
          _buildNotificationToggle(
            'likes',
            'Kedvelések',
            'Amikor valaki kedvel egy posztodat',
            Icons.favorite,
            Colors.red,
          ),
          
          _buildNotificationToggle(
            'comments',
            'Kommentek',
            'Amikor valaki kommenteli egy posztodat',
            Icons.comment,
            Colors.blue,
          ),
          
          _buildNotificationToggle(
            'follows',
            'Követések',
            'Amikor valaki követ téged',
            Icons.person_add,
            Colors.green,
          ),
          
          _buildNotificationToggle(
            'mentions',
            'Említések',
            'Amikor valaki megemlít téged',
            Icons.alternate_email,
            Colors.orange,
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationToggle(
    String key,
    String title,
    String description,
    IconData icon,
    Color color,
  ) {
    return Container(
      margin: EdgeInsets.only(bottom: 12),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(
              icon,
              color: color,
              size: 18,
            ),
          ),
          
          SizedBox(width: 12),
          
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: Colors.black87,
                  ),
                ),
                Text(
                  description,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          
          Switch(
            value: _notificationsEnabled[key] ?? false,
            onChanged: (value) {
              setState(() {
                _notificationsEnabled[key] = value;
              });
            },
            activeColor: Color(0xFF00D4AA),
          ),
        ],
      ),
    );
  }

  Widget _buildAccountActionsSection() {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
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
              Icon(
                Icons.manage_accounts,
                color: Color(0xFF00D4AA),
                size: 24,
              ),
              SizedBox(width: 12),
              Text(
                'Fiók műveletek',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          
          SizedBox(height: 16),
          
          _buildActionButton(
            'Adatok exportálása',
            'Töltsd le a fórumon tárolt adataidat',
            Icons.download,
            Colors.blue,
            _exportData,
          ),
          
          SizedBox(height: 12),
          
          _buildActionButton(
            'Fórum adatok törlése',
            'Törli az összes fórumon tárolt adatodat',
            Icons.delete_forever,
            Colors.red,
            _showDeleteDataDialog,
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(
    String title,
    String description,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.grey[50],
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                icon,
                color: color,
                size: 18,
              ),
            ),
            
            SizedBox(width: 12),
            
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: Colors.black87,
                    ),
                  ),
                  Text(
                    description,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
            
            Icon(
              Icons.chevron_right,
              color: Colors.grey[400],
              size: 20,
            ),
          ],
        ),
      ),
    );
  }

  void _exportData() {
    // TODO: Implement data export functionality
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Adatok exportálása hamarosan elérhető lesz!'),
        backgroundColor: Colors.blue,
      ),
    );
  }

  void _showDeleteDataDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.warning, color: Colors.red),
            SizedBox(width: 12),
            Text('Adatok törlése'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ez a művelet véglegesen törli az összes fórumon tárolt adatodat:',
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
            SizedBox(height: 12),
            Text('• Összes posztod'),
            Text('• Összes kommented'),
            Text('• Kedveléseid'),
            Text('• Követési kapcsolataid'),
            Text('• Beállításaid'),
            SizedBox(height: 12),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.error, color: Colors.red, size: 20),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Ez a művelet visszavonhatatlan!',
                      style: TextStyle(
                        color: Colors.red,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Mégse'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _deleteForumData();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            child: Text(
              'Törlés',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  void _deleteForumData() {
    // TODO: Implement forum data deletion
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Adatok törlése hamarosan elérhető lesz!'),
        backgroundColor: Colors.red,
      ),
    );
  }
}