import 'package:flutter/material.dart';

class EditProfileScreen extends StatefulWidget {
  final String username;
  final String userId;
  final String email;
  final String? mobile; // Opcionális
  // Add a Key parameter
  const EditProfileScreen({
    Key? key,
    required this.username,
    required this.userId,
    required this.email,
    this.mobile,
  }) : super(key: key);

  @override
  _EditProfileScreenState createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  late final TextEditingController usernameController;
  late final TextEditingController phoneController;
  late final TextEditingController emailController;
  late final TextEditingController passwordController;

  bool pushNotifications = true;
  bool darkTheme = false;

  @override
  void initState() {
    super.initState();
    usernameController = TextEditingController(text: widget.username);
    phoneController = TextEditingController(text: widget.mobile ?? ''); // Használjuk a mobil számot, ha van
    emailController = TextEditingController(text: widget.email);
    passwordController = TextEditingController(); // Üresen kezdjük, csak ha változtatni akarja
  }

  @override
  void dispose() {
    usernameController.dispose();
    phoneController.dispose();
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF00D4AA), // Háttérszín a profil oldallal megegyezően
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      "Profil szerkesztése",
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Container(
                // Itt van a lekerekített tetejű fehér rész
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Nincs profilkép - ez a rész már hiányzik az eredeti kódból, ha volt
                      // De ha volt, az itt lett volna a "John Smith" és "dummy ID" felett.
                      // Most közvetlenül az input mezőkre koncentrálunk.
                      const SizedBox(height: 16),
                      // Felhasználónév mező
                      _buildTextField(
                        controller: usernameController,
                        label: "Felhasználónév",
                        icon: Icons.person_outline,
                      ),
                      const SizedBox(height: 16),

                      // Email mező
                      _buildTextField(
                        controller: emailController,
                        label: "Email",
                        icon: Icons.email_outlined,
                        keyboardType: TextInputType.emailAddress,
                      ),
                      const SizedBox(height: 16),

                      // Telefonszám mező
                      _buildTextField(
                        controller: phoneController,
                        label: "Telefonszám",
                        icon: Icons.phone_outlined,
                        keyboardType: TextInputType.phone,
                      ),
                      const SizedBox(height: 16),

                      // ÚJ: Jelszó mező
                      _buildTextField(
                        controller: passwordController,
                        label: "Új Jelszó",
                        icon: Icons.lock_outline,
                        obscureText: true, // Jelszó elrejtése
                      ),
                      const SizedBox(height: 24),

                      // Mentés gomb
                      Center(
                        child: ElevatedButton(
                          onPressed: () {
                            // TODO: Implementáld a profil adatok mentését (pl. AuthService.updateProfile)
                            // Ehhez egy új metódusra lenne szükség az AuthService-ben és egy backend végpontra.
                            debugPrint('Mentés gomb megnyomva!');
                            debugPrint('Felhasználónév: ${usernameController.text}');
                            debugPrint('Email: ${emailController.text}');
                            debugPrint('Telefonszám: ${phoneController.text}');
                            debugPrint('Új Jelszó: ${passwordController.text}');
                            // Példa: Navigator.pop(context) a mentés után
                            Navigator.pop(context);
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF00D4A3),
                            padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 15),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(30),
                            ),
                          ),
                          child: const Text(
                            "Változtatások Mentése",
                            style: TextStyle(fontSize: 18, color: Colors.white),
                          ),
                        ),
                      ),
                      const SizedBox(height: 40),

                      // Beállítások (pushNotifications, darkTheme)
                      _buildSettingsSwitch(
                        title: "Push Értesítések",
                        value: pushNotifications,
                        onChanged: (bool value) {
                          setState(() {
                            pushNotifications = value;
                          });
                        },
                      ),
                      _buildSettingsSwitch(
                        title: "Sötét Mód",
                        value: darkTheme,
                        onChanged: (bool value) {
                          setState(() {
                            darkTheme = value;
                          });
                        },
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
      // NINCS bottomNavigationBar: A fő navigáció marad a MainScreen-ben
    );
  }

  // Segéd metódus a szövegbeviteli mezőkhöz
  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    TextInputType keyboardType = TextInputType.text,
    bool obscureText = false,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      obscureText: obscureText,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Colors.grey[600]),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        filled: true,
        fillColor: Colors.grey[100],
        contentPadding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16),
      ),
    );
  }

  // Segéd metódus a beállítások kapcsolókhoz
  Widget _buildSettingsSwitch({
    required String title,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: const Color(0xFF00D4A3),
            inactiveThumbColor: Colors.grey[400],
            inactiveTrackColor: Colors.grey[300],
          ),
        ],
      ),
    );
  }
}