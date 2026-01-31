import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:provider/provider.dart';
import '../services/map_config.dart';
import '../services/settings_service.dart';
import '../services/auth_service.dart';
import '../services/keldor_service.dart';
import '../services/story_engine.dart';
import '../services/location_service.dart';
import '../theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _hapticsEnabled = true;
  bool _darkMode = true;
  bool _useLocalBackend = false;
  String _mapStyle = 'dark';
  String _localIp = '10.0.2.2';
  final _ipController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _useLocalBackend = prefs.getBool('use_local_backend') ?? false;
      _localIp = prefs.getString('local_ip') ?? '10.0.2.2';
      _ipController.text = _localIp;
    });
  }

  void _logout() {
    context.read<KeldorService>().clearActiveCharacter();
    context.read<AuthService>().logout();
  }

  Future<void> _updateMapStyle(String? style) async {
    if (style == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('map_style', style);
    setState(() {
      _mapStyle = style;
    });
  }

  Future<void> _toggleBackend(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('use_local_backend', value);
    setState(() {
      _useLocalBackend = value;
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(value ? "Átváltva: Localhost" : "Átváltva: Render (Cloud)"),
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _saveIp(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('local_ip', value);
    setState(() => _localIp = value);
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsService>();

    return Scaffold(
      backgroundColor: KeldorTheme.background,
      appBar: AppBar(
        title: Text("Beállítások", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        backgroundColor: KeldorTheme.background,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _buildUserInfo(),
          const SizedBox(height: 32),
          _buildSectionHeader("ÁLTALÁNOS"),
          _buildToggleTile(Icons.vibration, "Haptikus visszajelzés", settings.hapticsEnabled, (v) => settings.setHapticsEnabled(v)),
          _buildToggleTile(Icons.dark_mode_outlined, "Sötét mód", _darkMode, (v) => setState(() => _darkMode = v)),
          
          const SizedBox(height: 24),
          _buildMapStyleSelector(settings),
          
          const SizedBox(height: 32),
          _buildSectionHeader("FIÓK"),
          _buildActionTile(Icons.logout, "Kijelentkezés", "Biztosan ki akarsz jelentkezni?", Colors.redAccent, _logout),
          _buildSectionHeader("FEJLESZTŐI BEÁLLÍTÁSOK"),
          _buildToggleTile(
            Icons.developer_mode, 
            "Localhost Backend használata", 
            _useLocalBackend, 
            _toggleBackend
          ),
          _buildToggleTile(
            Icons.location_on, 
            "Debug Mód (Kattintás = Teleport)", 
            context.watch<LocationService>().isDebugMode, 
            (v) => context.read<LocationService>().setDebugMode(v)
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Bekapcsolva az app az alábbi címet keresi:",
                  style: GoogleFonts.outfit(fontSize: 11, color: Colors.white38),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _ipController,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: "pl. 192.168.1.10",
                    hintStyle: const TextStyle(color: Colors.white24),
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  onChanged: _saveIp,
                ),
                const SizedBox(height: 4),
                const Text(
                  "Emulator: 10.0.2.2 | Fizikai eszköz: Géped belső IP címe",
                  style: TextStyle(color: Colors.white24, fontSize: 9),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),
          _buildSectionHeader("ADATOK"),
          _buildActionTile(Icons.delete_outline, "Gyorsítótár ürítése", "Képek és térképadatok törlése", Colors.white, () {}),
          _buildActionTile(Icons.refresh, "Haladás alaphelyzetbe", "Összes mentett játék törlése", Colors.redAccent, () {}),
          
          const SizedBox(height: 32),
          _buildSectionHeader("INFO"),
          _buildActionTile(Icons.info_outline, "Verzió", "1.1.0 Professional", Colors.white54, null),
        ],
      ),
    );
  }

  Widget _buildMapStyleSelector(SettingsService settings) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader("TÉRKÉP STÍLUSA"),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(20),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: settings.mapStyle,
              dropdownColor: KeldorTheme.surface,
              icon: const Icon(Icons.arrow_drop_down, color: KeldorTheme.primary),
              isExpanded: true,
              items: MapConfig.styles.map((style) {
                return DropdownMenuItem<String>(
                  value: style['id'],
                  child: Text(
                    style['name']!,
                    style: GoogleFonts.outfit(color: Colors.white),
                  ),
                );
              }).toList(),
              onChanged: (v) => v != null ? settings.setMapStyle(v) : null,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildUserInfo() {
    final user = context.watch<StoryEngine>().user;
    final character = context.watch<KeldorService>().activeCharacter;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [KeldorTheme.primary.withOpacity(0.2), KeldorTheme.secondary.withOpacity(0.05)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: KeldorTheme.primary.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 35,
            backgroundColor: KeldorTheme.primary.withOpacity(0.2),
            child: const Icon(Icons.person, size: 40, color: KeldorTheme.primary),
          ),
          const SizedBox(height: 16),
          Text(
            context.watch<AuthService>().username ?? "Felfedező",
            style: GoogleFonts.outfit(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          if (character != null) ...[
            const SizedBox(height: 4),
            Text(
              "Karakter: ${character.name}",
              style: GoogleFonts.outfit(fontSize: 14, color: KeldorTheme.primary, fontWeight: FontWeight.w500),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Text(
        title,
        style: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2, color: KeldorTheme.primary),
      ),
    );
  }

  Widget _buildToggleTile(IconData icon, String title, bool value, Function(bool) onChanged) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
      ),
      child: SwitchListTile(
        secondary: Icon(icon, color: KeldorTheme.primary),
        title: Text(title, style: GoogleFonts.outfit(color: Colors.white)),
        value: value,
        onChanged: onChanged,
        activeColor: KeldorTheme.primary,
      ),
    );
  }

  Widget _buildActionTile(IconData icon, String title, String subtitle, Color textColor, VoidCallback? onTap) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(20),
      ),
      child: ListTile(
        leading: Icon(icon, color: textColor == Colors.redAccent ? Colors.redAccent : KeldorTheme.primary),
        title: Text(title, style: GoogleFonts.outfit(color: textColor)),
        subtitle: Text(subtitle, style: GoogleFonts.outfit(fontSize: 12, color: Colors.white54)),
        onTap: onTap,
      ),
    );
  }
}
