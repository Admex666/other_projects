import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class UpdateService {
  static const String _versionUrl = 'https://raw.githubusercontent.com/user/repo/main/version.json';

  Future<UpdateInfo?> checkForUpdate() async {
    try {
      final response = await http.get(Uri.parse(_versionUrl));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final latestVersion = data['version'] as String;
        final downloadUrl = data['download_url'] as String;
        
        final packageInfo = await PackageInfo.fromPlatform();
        final currentVersion = packageInfo.version;

        if (_isNewer(latestVersion, currentVersion)) {
          return UpdateInfo(
            latestVersion: latestVersion,
            downloadUrl: downloadUrl,
            releaseNotes: data['release_notes'] as String?,
          );
        }
      }
    } catch (e) {
      // Silently fail or log
    }
    return null;
  }

  bool _isNewer(String latest, String current) {
    // Basic semver comparison
    return latest.compareTo(current) > 0;
  }
}

class UpdateInfo {
  final String latestVersion;
  final String downloadUrl;
  final String? releaseNotes;

  UpdateInfo({
    required this.latestVersion,
    required this.downloadUrl,
    this.releaseNotes,
  });
}

final updateServiceProvider = Provider<UpdateService>((ref) {
  return UpdateService();
});
