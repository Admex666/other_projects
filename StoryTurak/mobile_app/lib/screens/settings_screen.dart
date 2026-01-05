import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/map_config.dart';

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
      _mapStyle = prefs.getString('map_style') ?? 'dark';
      _localIp = prefs.getString('local_ip') ?? '10.0.2.2';
      _ipController.text = _localIp;
    });
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
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      appBar: AppBar(
        title: Text("Beállítások", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF0F172A),
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _buildSectionHeader("ÁLTALÁNOS"),
          _buildToggleTile(Icons.vibration, "Haptikus visszajelzés", _hapticsEnabled, (v) => setState(() => _hapticsEnabled = v)),
          _buildToggleTile(Icons.dark_mode_outlined, "Sötét mód", _darkMode, (v) => setState(() => _darkMode = v)),
          
          const SizedBox(height: 24),
          _buildMapStyleSelector(),
          
          const SizedBox(height: 32),
          _buildSectionHeader("FEJLESZTŐI BEÁLLÍTÁSOK"),
          _buildToggleTile(
            Icons.developer_mode, 
            "Localhost Backend használata", 
            _useLocalBackend, 
            _toggleBackend
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

  Widget _buildMapStyleSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader("TÉRKÉP STÍLUSA"),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          decoration: BoxDecoration(
            color: const Color(0xFF1E293B),
            borderRadius: BorderRadius.circular(20),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: _mapStyle,
              dropdownColor: const Color(0xFF1E293B),
              icon: const Icon(Icons.arrow_drop_down, color: Colors.blueAccent),
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
              onChanged: _updateMapStyle,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Text(
        title,
        style: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2, color: Colors.blueAccent),
      ),
    );
  }

  Widget _buildToggleTile(IconData icon, String title, bool value, Function(bool) onChanged) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
      ),
      child: SwitchListTile(
        secondary: Icon(icon, color: Colors.blueAccent),
        title: Text(title, style: GoogleFonts.outfit(color: Colors.white)),
        value: value,
        onChanged: onChanged,
        activeColor: Colors.blueAccent,
      ),
    );
  }

  Widget _buildActionTile(IconData icon, String title, String subtitle, Color textColor, VoidCallback? onTap) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(20),
      ),
      child: ListTile(
        leading: Icon(icon, color: textColor == Colors.redAccent ? Colors.redAccent : Colors.blueAccent),
        title: Text(title, style: GoogleFonts.outfit(color: textColor)),
        subtitle: Text(subtitle, style: GoogleFonts.outfit(fontSize: 12, color: Colors.white54)),
        onTap: onTap,
      ),
    );
  }
}
