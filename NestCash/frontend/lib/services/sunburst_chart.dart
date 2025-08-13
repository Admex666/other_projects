import 'package:flutter/material.dart';
import 'dart:math' as math;

class AccountsSunburstChart extends StatefulWidget {
  final Map<String, dynamic>? accountsData;

  const AccountsSunburstChart({Key? key, this.accountsData}) : super(key: key);

  @override
  _AccountsSunburstChartState createState() => _AccountsSunburstChartState();
}

class _AccountsSunburstChartState extends State<AccountsSunburstChart> {
  String? selectedMainAccount;

  @override
  Widget build(BuildContext context) {
    if (widget.accountsData == null || widget.accountsData!.isEmpty) {
      return Container(
        height: 300,
        child: Center(
          child: Text(
            'Nincsenek adatok a megjelenítéshez',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
            ),
          ),
        ),
      );
    }

    return Container(
      height: 500, // Növelt magasság
      child: Column(
        children: [
          Text(
            'Számlák megoszlása',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 20),
          Expanded(
            child: Column(
              children: [
                // Nagyított chart
                Container(
                  height: 280, // Nagyobb chart
                  child: _buildSunburstChart(),
                ),
                SizedBox(height: 24),
                // Modernizált legenda
                Expanded(
                  child: _buildModernLegend(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSunburstChart() {
    return GestureDetector(
      onTapDown: (details) {
        _handleTap(details.localPosition);
      },
      child: CustomPaint(
        painter: SunburstPainter(
          accountsData: widget.accountsData!,
          selectedMainAccount: selectedMainAccount,
        ),
        size: Size.infinite,
      ),
    );
  }

  Widget _buildModernLegend() {
    List<Widget> legendCards = [];
    List<Color> mainColors = [
      Color(0xFF00D4AA), // Likvid - zöld
      Color(0xFF4285F4), // Befektetés - kék  
      Color(0xFFEA4335), // Megtakarítás - piros
    ];
    
    int mainColorIndex = 0;
    
    widget.accountsData!.forEach((mainAccountKey, mainAccountValue) {
      double amount = (mainAccountValue['foosszeg'] ?? 0).toDouble();
      
      // Főkártya létrehozása
      legendCards.add(
        Container(
          margin: EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                mainColors[mainColorIndex % mainColors.length].withOpacity(0.1),
                mainColors[mainColorIndex % mainColors.length].withOpacity(0.05),
              ],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: mainColors[mainColorIndex % mainColors.length].withOpacity(0.3),
              width: 1,
            ),
          ),
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Főszámla header
                Row(
                  children: [
                    Container(
                      width: 20,
                      height: 20,
                      decoration: BoxDecoration(
                        color: mainColors[mainColorIndex % mainColors.length],
                        borderRadius: BorderRadius.circular(6),
                        boxShadow: [
                          BoxShadow(
                            color: mainColors[mainColorIndex % mainColors.length].withOpacity(0.3),
                            spreadRadius: 0,
                            blurRadius: 4,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _getAccountDisplayName(mainAccountKey),
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                          ),
                          Text(
                            '${amount.toStringAsFixed(0)} Ft',
                            style: TextStyle(
                              fontSize: 14,
                              color: mainColors[mainColorIndex % mainColors.length],
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                
                // Alszámlák
                if (mainAccountValue['alszamlak'] != null && 
                    (mainAccountValue['alszamlak'] as Map<String, dynamic>).isNotEmpty) ...[
                  SizedBox(height: 12),
                  Container(
                    height: 1,
                    color: Colors.grey[300],
                  ),
                  SizedBox(height: 12),
                  ...((mainAccountValue['alszamlak'] as Map<String, dynamic>).entries.map((subEntry) {
                    double subAmount = (subEntry.value['balance'] ?? 0).toDouble();
                    String currency = subEntry.value['currency'] ?? 'Ft';
                    
                    return Padding(
                      padding: EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          SizedBox(width: 32), // Indentálás
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: mainColors[mainColorIndex % mainColors.length].withOpacity(0.6),
                              shape: BoxShape.circle,
                            ),
                          ),
                          SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              subEntry.key,
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey[700],
                              ),
                            ),
                          ),
                          Text(
                            '${subAmount.toStringAsFixed(0)} $currency',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey[800],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList()),
                ],
              ],
            ),
          ),
        ),
      );
      mainColorIndex++;
    });

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: EdgeInsets.only(left: 4, bottom: 16),
            child: Text(
              'Részletek',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.black87,
              ),
            ),
          ),
          ...legendCards,
        ],
      ),
    );
  }

  void _handleTap(Offset localPosition) {
    // A tap kezelés logikája később implementálható
    // Itt lehet meghatározni, hogy melyik szegmensre kattintottak
  }

  String _getAccountDisplayName(String key) {
    switch (key.toLowerCase()) {
      case 'likvid':
        return '💰 Likvid eszközök';
      case 'befektetes':
        return '📈 Befektetések';
      case 'megtakaritas':
        return '🏦 Megtakarítások';
      default:
        return key.toUpperCase();
    }
  }
}

class SunburstPainter extends CustomPainter {
  final Map<String, dynamic> accountsData;
  final String? selectedMainAccount;
  
  static const double innerRadius = 70.0;  // Nagyobb központi kör
  static const double outerRadius = 130.0; // Külső sugár marad
  static const double gap = 2.0; // Visszaállítjuk a hézagot

  SunburstPainter({
    required this.accountsData,
    this.selectedMainAccount,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final paint = Paint()..style = PaintingStyle.fill;
    
    // Színek definíálása
    List<Color> mainColors = [
      Color(0xFF00D4AA), // Likvid - zöld
      Color(0xFF4285F4), // Befektetés - kék  
      Color(0xFFEA4335), // Megtakarítás - piros
    ];

    // Összesített összeg számítása
    double totalAmount = 0;
    accountsData.forEach((key, value) {
      totalAmount += (value['foosszeg'] ?? 0).toDouble();
    });

    if (totalAmount == 0) return;

    // CSAK a belső kör (főszámlák) rajzolása - vastagabb külső gyűrű
    double startAngle = -math.pi / 2;
    int mainColorIndex = 0;
    
    accountsData.forEach((mainAccountKey, mainAccountValue) {
      double amount = (mainAccountValue['foosszeg'] ?? 0).toDouble();
      double sweepAngle = (amount / totalAmount) * 2 * math.pi;
      
      paint.color = mainColors[mainColorIndex % mainColors.length];
      
      // Vastabb gyűrű rajzolása (innerRadius-tól outerRadius-ig)
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: outerRadius),
        startAngle,
        sweepAngle - (gap * math.pi / 180),
        true,
        paint,
      );
      
      startAngle += sweepAngle;
      mainColorIndex++;
    });

    // Belső rész kivágása (donut effect) - nagyobb központi kör
    paint.color = Colors.white;
    canvas.drawCircle(center, innerRadius, paint);
    
    // Árnyék a központi körre
    final shadowPaint = Paint()
      ..color = Colors.grey.withOpacity(0.15)
      ..maskFilter = MaskFilter.blur(BlurStyle.normal, 4);
    canvas.drawCircle(center, innerRadius - 2, shadowPaint);
    
    // Központi kör újra (tiszta)
    paint.color = Colors.white;
    canvas.drawCircle(center, innerRadius, paint);
    
    // Központi szöveg nagyobb méretben
    final textPainter = TextPainter(
      text: TextSpan(
        children: [
          TextSpan(
            text: 'Összes vagyon\n',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          TextSpan(
            text: '${totalAmount.toStringAsFixed(0)} Ft',
            style: TextStyle(
              color: Colors.black87,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(
      canvas, 
      center - Offset(textPainter.width / 2, textPainter.height / 2),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}