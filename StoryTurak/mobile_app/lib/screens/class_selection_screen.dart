import 'package:flutter/material.dart';
import 'package:storyturak_mobile/theme.dart';

class ClassSelectionScreen extends StatelessWidget {
  const ClassSelectionScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Ki vagy te?",
                style: GeolixoTheme.darkTheme.textTheme.displayLarge,
              ),
              const SizedBox(height: 8),
              Text(
                "Válassz utat a város sötétjében.",
                style: GeolixoTheme.darkTheme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              Expanded(
                child: ListView(
                  children: const [
                    ClassCard(
                      title: "Őr / Katona",
                      description: "Frontális, stabil döntések. Nem hátrálsz meg.",
                      icon: Icons.shield,
                    ),
                    ClassCard(
                      title: "Poéta",
                      description: "Megfigyelő. A szavak és jelek mestere.",
                      icon: Icons.edit_note,
                    ),
                    ClassCard(
                      title: "Vámszedő",
                      description: "Kockázat és haszon. Ismered a dörzsölt utakat.",
                      icon: Icons.attach_money,
                    ),
                    ClassCard(
                      title: "Zarándok",
                      description: "Kitartás. A hosszú út a te igazi otthonod.",
                      icon: Icons.hiking,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ClassCard extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;

  const ClassCard({
    Key? key,
    required this.title,
    required this.description,
    required this.icon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: GeolixoTheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () {
            // TODO: Select class and navigate to map
            Navigator.pushReplacementNamed(context, '/map');
          },
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(icon, color: GeolixoTheme.accent, size: 32),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: GeolixoTheme.darkTheme.textTheme.displayMedium?.copyWith(fontSize: 18),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        description,
                        style: GeolixoTheme.darkTheme.textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right, color: Colors.white54),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
