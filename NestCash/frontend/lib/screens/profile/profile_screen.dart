import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/screens/profile/edit_profile_screen.dart';
import 'package:frontend/screens/auth/login_screen.dart';  
import 'package:frontend/services/auth_service.dart';
import 'package:frontend/widgets/badge_summary_widget.dart';
import 'package:frontend/screens/auth/auth_wrapper.dart';
import 'package:frontend/screens/subscription/subscription_screen.dart';
import 'package:file_saver/file_saver.dart';
import 'package:flutter/services.dart'; // Clipboard-hoz
import 'package:intl/intl.dart'; // DateFormat-hoz
import 'package:frontend/services/nestcash_analytics_service.dart';

class ProfileScreen extends StatefulWidget {
  final String username;
  final String userId;
  const ProfileScreen({Key? key, required this.username, required this.userId}) : super(key: key);

  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final AuthService _authService = AuthService();
  Map<String, dynamic>? _userProfile;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchUserProfile();
  }

    @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Minden alkalommal újra ellenőrizzük a profilt amikor erre a screen-re navigálunk
    if (mounted) {
      _fetchUserProfile();
    }
  }

  void _handleAuthError() {
    // Token érvénytelen vagy hiányzik - kijelentkeztetés és visszairányítás
    _authService.logout();
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('session_expired'),
          backgroundColor: Colors.red,
        ),
      );
      
      // Navigáció az AuthWrapper-re (ami kezeli a bejelentkezést)
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => AuthWrapper()),
        (Route<dynamic> route) => false,
      );
    }
  }

  bool _isAuthError(dynamic error) {
    final errorStr = error.toString().toLowerCase();
    return errorStr.contains('401') || 
          errorStr.contains('unauthorized') || 
          errorStr.contains('not authenticated') ||
          errorStr.contains('token') && (errorStr.contains('invalid') || errorStr.contains('expired'));
  }

  Future<void> _fetchUserProfile() async {
    setState(() => _isLoading = true);
    
    try {
      final profile = await _authService.getUserProfile();
      if (mounted) {
        setState(() {
          _userProfile = profile;
          _isLoading = false;
        });
      }
      await NestCashAnalyticsService.trackScreenView('profile_screen');
    } catch (e) {
      debugPrint('Error fetching user profile: $e');
      
      if (_isAuthError(e)) {
        _handleAuthError();
        return;
      }
      
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('profile_load_error'.tr(args: [e.toString()])),
            backgroundColor: Colors.orange,
          ),
        );
      }
    }
  }

  Future<void> _deleteAccount() async {
    try {
      await _authService.deleteAccount(); // Felhasználó törlése
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('delete_account_success'.tr()),
          backgroundColor: Color(0xFF00D4AA),
        ),
      );
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => const LoginScreen()),
        (Route<dynamic> route) => false,
      );
    } catch (e) {
      debugPrint('Error deleting account: $e');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('delete_account_failed'.tr()),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildProfileMenuItem({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
    Color iconColor = Colors.white,
    Color backgroundColor = Colors.blue,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: ListTile(
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(24),
          ),
          child: Icon(
            icon,
            color: iconColor,
            size: 24,
          ),
        ),
        title: Text(
          title,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.black87,
          ),
        ),
        trailing: Icon(
          Icons.arrow_forward_ios,
          color: Colors.grey[400],
          size: 16,
        ),
        onTap: onTap,
        contentPadding: EdgeInsets.symmetric(horizontal: 0, vertical: 4),
      ),
    );
  }

  void _showSettingsDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('settings_dialog_title'.tr()), // volt: 'Beállítások'
          content: Text('settings_dialog_content'.tr()), // volt: 'A beállítások itt lesznek implementálva.'
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('close'.tr()), // volt: 'Bezárás'
            ),
          ],
        );
      },
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('feedback_dialog_title'.tr()), // volt: 'Visszajelzés'
          content: Text('feedback_dialog_content'.tr()), // volt: 'A visszajelzés itt lesz implementálva.'
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('close'.tr()), // volt: 'Bezárás'
            ),
          ],
        );
      },
    );
  }

  // Nyelváltó dialógus
  void _showLanguageDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('change_language'.tr()),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Text('🇭🇺'),
                title: const Text('Magyar'),
                onTap: () {
                  context.setLocale(const Locale('hu', 'HU'));
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: const Text('🇬🇧'),
                title: const Text('English'),
                onTap: () {
                  context.setLocale(const Locale('en', 'US'));
                  Navigator.pop(context);
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('close'.tr()),
            ),
          ],
        );
      },
    );
  }

  void _showDeleteAccountDialog() {
    final TextEditingController usernameController = TextEditingController();

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('delete_account_title'.tr()),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('delete_account_confirm'.tr()),
              SizedBox(height: 16),
              Text('delete_account_username_prompt'.tr()),
              SizedBox(height: 8),
              TextField(
                controller: usernameController,
                decoration: InputDecoration(
                  labelText: 'username'.tr(),
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('cancel'.tr()),
            ),
            TextButton(
              onPressed: () async {
                if (usernameController.text == widget.username) {
                  Navigator.of(context).pop(); // Bezárja a dialógust
                  await _deleteAccount();
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('username_mismatch'.tr()),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              child: Text(
                'delete'.tr(),
                style: TextStyle(color: Colors.red),
              ),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    // Alapértelmezett értékek, ha valamiért nem sikerült a profil lekérése
    final String currentUsername = _userProfile?['username'] ?? widget.username;
    final String currentEmail = _userProfile?['email'] ?? '-';
    final String currentMobile = _userProfile?['mobile'] ?? '-';
    final String currentUserId = _userProfile?['_id'] ?? widget.userId; // Feltételezve, hogy a backend _id-t ad vissza
    
    return Scaffold(
      backgroundColor: Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Profile Picture (positioned to overlap)
            Container(
              height: 100,
              child: Stack(
                children: [
                  Positioned(
                    top: 40,
                    left: 0,
                    right: 0,
                    child: Container(
                      height: 60,
                      decoration: BoxDecoration(
                        color: Color(0xFFF5F5F5),
                        borderRadius: BorderRadius.only(
                          topLeft: Radius.circular(30),
                          topRight: Radius.circular(30),
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    top: 0,
                    left: 0,
                    right: 0,
                    child: Center(
                      child: Container(
                        width: 100,
                        height: 100,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 4),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.1),
                              blurRadius: 10,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: CircleAvatar(
                          radius: 48,
                          backgroundColor: Color(0xFF00D4AA),
                          child: Text(
                            currentUsername.isNotEmpty ? currentUsername[0].toUpperCase() : '?',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 36, // Nagyobb betűméret a nagyobb avatar miatt
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            
            // Content Container
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Color(0xFFF5F5F5),
                ),
                child: SingleChildScrollView(
                  child: Padding(
                    padding: EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      children: [
                        SizedBox(height: 30), // Space for profile picture
                        
                        // User Info
                        Text(
                          widget.username,
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'ID: ${widget.userId}',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                        
                        SizedBox(height: 40),
                        
                        BadgeSummaryWidget(
                          userId: currentUserId,
                          username: currentUsername,
                        ),

                        SizedBox(height: 20),

                        // Profile Menu Items
                        _buildProfileMenuItem(
                          icon: Icons.person_outline,
                          title: 'edit_profile'.tr(),
                          backgroundColor: Colors.blue[400]!,
                          onTap: () {
                            // Navigálás az EditProfileScreen-re
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => EditProfileScreen(
                                username: currentUsername,
                                userId: currentUserId,
                                email: currentEmail,
                                mobile: currentMobile,
                              )),
                            );
                          },
                        ),

                        _buildProfileMenuItem(
                          icon: Icons.card_membership,
                          title: 'my_subscription'.tr(),
                          backgroundColor: Colors.purple[400]!,
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => const SubscriptionScreen()),
                            );
                          },
                        ),

                        _buildProfileMenuItem(
                          icon: Icons.settings_outlined,
                          title: 'settings'.tr(),
                          backgroundColor: Colors.blue[600]!,
                          onTap: _showSettingsDialog,
                        ),
                        
                        _buildProfileMenuItem(
                          icon: Icons.help_outline,
                          title: 'feedback'.tr(),
                          backgroundColor: Colors.blue[300]!,
                          onTap: _showHelpDialog,
                        ),

                        // Nyelváltó gomb hozzáadása
                        _buildProfileMenuItem(
                          icon: Icons.language,
                          title: 'change_language'.tr(),
                          backgroundColor: Colors.green[400]!,
                          onTap: _showLanguageDialog,
                        ),
                        
                        _buildProfileMenuItem(
                        icon: Icons.logout,
                        title: 'logout'.tr(),
                        backgroundColor: Colors.red,
                        onTap: () {
                          showDialog(
                            context: context,
                            builder: (BuildContext context) {
                              return AlertDialog(
                                title: Text('logout_title'.tr()),
                                content: Text('logout_confirm'.tr()),
                                actions: <Widget>[
                                  TextButton(
                                    onPressed: () => Navigator.pop(context),
                                    child: Text('close'.tr()),
                                  ),
                                  TextButton(
                                    onPressed: () async {
                                      await _authService.logout();
                                      if (!mounted) return;
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        SnackBar(
                                          content: Text('logout_success'.tr()),
                                          backgroundColor: Color(0xFF00D4AA),
                                        ),
                                      );
                                      Navigator.pushAndRemoveUntil(
                                        context,
                                        MaterialPageRoute(builder: (context) => const LoginScreen()),
                                        (Route<dynamic> route) => false,
                                      );
                                    },
                                    child: Text(
                                      'logout'.tr(),
                                      style: TextStyle(color: Colors.red),
                                    ),
                                  ),
                                ],
                              );
                            },
                          );
                        },
                      ),

                      _buildProfileMenuItem(
                        icon: Icons.download,
                        title: 'export_data'.tr(),
                        backgroundColor: Colors.teal[400]!,
                        onTap: () async {
                          try {
                            final response = await _authService.exportUserData();
                            
                            if (response.statusCode == 200) {
                              final content = response.bodyBytes;
                              final timestamp = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
                              final filename = 'nestcash_export_$timestamp';
                              
                              // Egyszerű FileSaver használat
                              await FileSaver.instance.saveAs(
                                name: filename,
                                bytes: content,
                                ext: 'json',
                                mimeType: MimeType.json,
                              );
                              
                              if (!mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('data_export_success'.tr()),
                                  backgroundColor: Color(0xFF00D4AA),
                                ),
                              );
                            }
                          } catch (e) {
                            print('Export error: $e');
                            if (!mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Export failed: ${e.toString()}'),
                                backgroundColor: Colors.red,
                              ),
                            );
                          }
                        },
                      ),

                      _buildProfileMenuItem(
                        icon: Icons.delete_forever,
                        title: 'delete_account'.tr(),
                        backgroundColor: Colors.red[700]!,
                        onTap: _showDeleteAccountDialog, // Új metódus hívása
                      ),
                      SizedBox(height: 40),
                    ],
                  ),
                ),
              ),
            ),
        ),],
        ),
      ),
    );
  }
}