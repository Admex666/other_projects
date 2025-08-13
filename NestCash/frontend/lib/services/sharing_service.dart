// lib/services/sharing_service.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:frontend/config/config.dart';

class SharingService {
  static const _storage = FlutterSecureStorage();

  const SharingService();

  Future<String?> getToken() async {
    return _storage.read(key: 'token');
  }

  Future<Map<String, dynamic>?> shareAchievement(String achievementType, String achievementId) async {
    final token = await getToken();
    if (token == null) return null;

    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/sharing/share'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'achievement_type': achievementType,
          'achievement_id': achievementId,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print('Error sharing achievement: $e');
      return null;
    }
  }

  Future<bool> canShareAchievement(String achievementType, String achievementId) async {
    final token = await getToken();
    if (token == null) return false;

    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/sharing/can-share/$achievementType/$achievementId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['can_share'] ?? false;
      }
      return false;
    } catch (e) {
      print('Error checking if can share: $e');
      return false;
    }
  }
}

// Megosztás gomb widget - JAVÍTOTT VERZIÓ
class ShareAchievementButton extends StatefulWidget {
  final String achievementType;
  final String achievementId;
  final String achievementName;
  final VoidCallback? onShared;

  const ShareAchievementButton({
    Key? key,
    required this.achievementType,
    required this.achievementId,
    required this.achievementName,
    this.onShared,
  }) : super(key: key);

  @override
  State<ShareAchievementButton> createState() => _ShareAchievementButtonState();
}

class _ShareAchievementButtonState extends State<ShareAchievementButton> {
  final SharingService _sharingService = const SharingService();
  bool _canShare = false;
  bool _isLoading = true;
  bool _isSharing = false;

  @override
  void initState() {
    super.initState();
    _checkCanShare();
  }

  Future<void> _checkCanShare() async {
    setState(() => _isLoading = true);
    
    final canShare = await _sharingService.canShareAchievement(
      widget.achievementType,
      widget.achievementId,
    );
    
    setState(() {
      _canShare = canShare;
      _isLoading = false;
    });
  }

  Future<void> _shareAchievement() async {
    setState(() => _isSharing = true);
    
    print('DEBUG: Attempting to share ${widget.achievementType} - ${widget.achievementId}');
    
    try {
      final result = await _sharingService.shareAchievement(
        widget.achievementType,
        widget.achievementId,
      );
      
      print('DEBUG: Share result: $result');
      
      if (mounted) {
        if (result != null && result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('${widget.achievementName} sikeresen megosztva! 🎉'),
              backgroundColor: Colors.green,
            ),
          );
          
          setState(() => _canShare = false);
          widget.onShared?.call();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(result?['message'] ?? 'Hiba történt a megosztás során'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      print('DEBUG: Share error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hiba történt: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
    
    if (mounted) {
      setState(() => _isSharing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const SizedBox(
        width: 20,
        height: 20,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }

    if (!_canShare) {
      return const SizedBox.shrink();
    }

    return Container(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF00D4A3), Color(0xFF00B894)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _isSharing ? null : _shareAchievement,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_isSharing)
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2,
                    ),
                  )
                else
                  const Icon(
                    Icons.share,
                    color: Colors.white,
                    size: 16,
                  ),
                const SizedBox(width: 8),
                Text(
                  _isSharing ? 'Megosztás...' : 'Megosztás',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}