import 'package:flutter/material.dart';
import 'package:frontend/screens/profile/edit_profile_screen.dart';
import 'package:frontend/screens/auth/login_screen.dart';  
import 'package:frontend/services/auth_service.dart';

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

  Future<void> _fetchUserProfile() async {
    try {
      final profile = await _authService.getUserProfile();
      setState(() {
        _userProfile = profile;
        _isLoading = false;
      });
    } catch (e) {
      debugPrint('Error fetching user profile: $e');
      setState(() {
        _isLoading = false;
      });
      // Kezelj hibaeseteket, pl. SnackBar üzenet
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
          title: Text('Beállítások'),
          content: Text('A beállítások itt lesznek implementálva.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('Bezárás'),
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
          title: Text('Visszajelzés'),
          content: Text('A visszajelzés itt lesz implementálva.'),  
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('Bezárás'),
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
    final String currentEmail = _userProfile?['email'] ?? 'Nincs email';
    final String currentMobile = _userProfile?['mobile'] ?? 'Nincs telefonszám';
    final String currentUserId = _userProfile?['_id'] ?? widget.userId; // Feltételezve, hogy a backend _id-t ad vissza
    
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
                  Expanded(
                    child: Text(
                      'Profil',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
            
            // Profile Picture (positioned to overlap)
            Container(
              height: 60,
              child: Stack(
                children: [
                  Positioned(
                    top: 20,
                    left: 0,
                    right: 0,
                    child: Container(
                      height: 40,
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
                          backgroundImage: AssetImage('assets/profile_image.jpg'), // You'll need to add this asset
                          backgroundColor: Colors.grey[300],
                          child: Icon(
                            Icons.person,
                            size: 40,
                            color: Colors.grey[600],
                          ), // Fallback icon if image is not available
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
                        SizedBox(height: 50), // Space for profile picture
                        
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
                        
                        // Profile Menu Items
                        _buildProfileMenuItem(
                          icon: Icons.person_outline,
                          title: 'Profil szerkesztése',
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
                          icon: Icons.settings_outlined,
                          title: 'Beállítások',
                          backgroundColor: Colors.blue[600]!,
                          onTap: _showSettingsDialog,
                        ),
                        
                        _buildProfileMenuItem(
                          icon: Icons.help_outline,
                          title: 'Visszajelzés',
                          backgroundColor: Colors.blue[300]!,
                          onTap: _showHelpDialog,
                        ),
                        
                        _buildProfileMenuItem(
                        icon: Icons.logout,
                        title: "Kijelentkezés",
                        backgroundColor: Colors.red,
                        onTap: () {
                          showDialog(
                            context: context,
                            builder: (BuildContext context) {
                              return AlertDialog(
                                title: Text('Kijelentkezés'),
                                content: Text('Biztosan ki szeretnél jelentkezni?'),
                                actions: <Widget>[
                                  TextButton(
                                    onPressed: () => Navigator.pop(context),
                                    child: Text('Bezárás'),
                                  ),
                                  TextButton(
                                    onPressed: () async {
                                      await _authService.logout();
                                      if (!mounted) return;
                                      ScaffoldMessenger.of(context).showSnackBar(
                                        const SnackBar(
                                          content: Text('Sikeres kijelentkezés'),
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
                                      'Kijelentkezés',
                                      style: TextStyle(color: Colors.red),
                                    ),
                                  ),
                                ],
                              );
                            },
                          );
                        },
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