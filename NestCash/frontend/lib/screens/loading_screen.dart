import 'package:flutter/material.dart';

/// LoadingScreen - NestCash alkalmazás töltőképernyője
/// A meglévő design nyelvezetet követi: teal/green színek, gradient háttér
class LoadingScreen extends StatefulWidget {
  final String? message;
  final bool showLogo;
  final Duration? duration;
  
  const LoadingScreen({
    super.key,
    this.message,
    this.showLogo = true,
    this.duration,
  });

  @override
  State<LoadingScreen> createState() => _LoadingScreenState();
}

class _LoadingScreenState extends State<LoadingScreen>
    with TickerProviderStateMixin {
  late AnimationController _progressController;
  late Animation<double> _progressValue;

  @override
  void initState() {
    super.initState();
    
    // Animáció kontroller inicializálása a 3 másodperces időtartamra
    _progressController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    );

    // Animáció definiálása
    _progressValue = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(_progressController);

    // Animáció indítása
    _startAnimations();
  }

  void _startAnimations() {
    _progressController.forward();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (widget.showLogo) // Hozzáadott feltétel, hogy a logo csak akkor jelenjen meg, ha a showLogo értéke true
              Stack(
                alignment: Alignment.center, // Ez az igazítás a Stack összes gyermekét középre helyezi
                children: [
                  // A kör alakú progress indicator
                  SizedBox(
                    width: 150,
                    height: 150,
                    child: AnimatedBuilder(
                      animation: _progressValue,
                      builder: (context, child) {
                        return CircularProgressIndicator(
                          value: _progressValue.value,
                          strokeWidth: 5.0,
                          backgroundColor: Colors.grey.shade200,
                          valueColor: const AlwaysStoppedAnimation<Color>(
                            Color(0xFF00D4A3),
                          ),
                        );
                      },
                    ),
                  ),
                  /* 
                  // A logó
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 20,
                          offset: const Offset(0, 10),
                        ),
                      ],
                      image: const DecorationImage(
                        image: AssetImage(Icons.money),
                        fit: BoxFit.contain, // Változtatás: BoxFit.cover helyett BoxFit.contain, hogy a kép ne vágódjon le
                      ),
                    ),
                  ),
                  */
                ],
              ),
            const SizedBox(height: 40),
            if (widget.message != null)
              Text(
                widget.message!,
                style: const TextStyle(
                  fontSize: 16,
                  color: Colors.black54,
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _progressController.dispose();
    super.dispose();
  }
}

/// LoadingOverlay - Átlátszó töltőképernyő overlay
/// Meglévő képernyő felett jeleníthető meg
class LoadingOverlay extends StatelessWidget {
  final String? message;
  final bool isVisible;

  const LoadingOverlay({
    super.key,
    this.message,
    this.isVisible = true,
  });

  @override
  Widget build(BuildContext context) {
    if (!isVisible) return const SizedBox.shrink();

    return Container(
      color: Colors.black.withOpacity(0.5),
      child: Center(
        child: Container(
          padding: const EdgeInsets.all(24),
          margin: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(
                color: Color(0xFF00D4A3),
                strokeWidth: 3,
              ),
              if (message != null) ...[
                const SizedBox(height: 16),
                Text(
                  message!,
                  style: const TextStyle(
                    fontSize: 16,
                    color: Colors.black87,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Mini töltő widget - kis méretű töltőjelző
class MiniLoader extends StatelessWidget {
  final Color? color;
  final double size;

  const MiniLoader({
    super.key,
    this.color,
    this.size = 20,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CircularProgressIndicator(
        color: color ?? const Color(0xFF00D4A3),
        strokeWidth: 2,
      ),
    );
  }
}