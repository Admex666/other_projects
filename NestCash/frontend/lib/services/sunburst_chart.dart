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
      height: 400,
      child: Column(
        children: [
          Text(
            'Számlák megoszlása',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 16),
          Expanded(
            child: Row(
              children: [
                // Sunburst Chart
                Expanded(
                  flex: 3,
                  child: _buildSunburstChart(),
                ),
                SizedBox(width: 16),
                // Legenda
                Expanded(
                  flex: 1,
                  child: _buildLegend(),
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

  void _handleTap(Offset localPosition) {
    // A tap kezelés logikája később implementálható
    // Itt lehet meghatározni, hogy melyik szegmensre kattintottak
  }

  Widget _buildLegend() {
    List<Widget> legendItems = [];
    List<Color> mainColors = [
      Color(0xFF00D4AA), // Likvid - zöld
      Color(0xFF4285F4), // Befektetés - kék  
      Color(0xFFEA4335), // Megtakarítás - piros
    ];
    
    List<Color> subColors = [
      Color(0xFF81C784), // Világos zöld
      Color(0xFF64B5F6), // Világos kék
      Color(0xFFFFB74D), // Narancssárga
      Color(0xFFF06292), // Rózsaszín
      Color(0xFFBA68C8), // Lila
      Color(0xFFAED581), // Még világosabb zöld
      Color(0xFF90CAF9), // Még világosabb kék
      Color(0xFFFFCC02), // Sárga
    ];
    
    int mainColorIndex = 0;
    
    widget.accountsData!.forEach((mainAccountKey, mainAccountValue) {
      double amount = (mainAccountValue['foosszeg'] ?? 0).toDouble();
      
      legendItems.add(
        Container(
          margin: EdgeInsets.only(bottom: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Főszámla
              Row(
                children: [
                  Container(
                    width: 14,
                    height: 14,
                    decoration: BoxDecoration(
                      color: mainColors[mainColorIndex % mainColors.length],
                      shape: BoxShape.circle,
                    ),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          mainAccountKey.toUpperCase(),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        Text(
                          '${amount.toStringAsFixed(0)} Ft',
                          style: TextStyle(
                            fontSize: 10,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              // Alszámlák - JAVÍTOTT színlogika
              if (mainAccountValue['alszamlak'] != null)
                ...((mainAccountValue['alszamlak'] as Map<String, dynamic>).entries.map((subEntry) {
                  int entryIndex = (mainAccountValue['alszamlak'] as Map<String, dynamic>).keys.toList().indexOf(subEntry.key);
                  
                  // Ugyanaz a színlogika, mint a SunburstPainter-ben
                  Color subColor;
                  if (mainColorIndex == 0) { // Likvid - zöld árnyalatok
                    subColor = subColors[entryIndex % 3];
                  } else if (mainColorIndex == 1) { // Befektetés - kék árnyalatok
                    subColor = subColors[(entryIndex + 1) % 3];
                  } else { // Megtakarítás - egyéb színek
                    subColor = subColors[(entryIndex + 3) % subColors.length];
                  }
                  
                  double subAmount = (subEntry.value['balance'] ?? 0).toDouble();
                  String currency = subEntry.value['currency'] ?? 'Ft';
                  
                  return Padding(
                    padding: EdgeInsets.only(left: 22, top: 4),
                    child: Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: subColor,
                            shape: BoxShape.circle,
                          ),
                        ),
                        SizedBox(width: 6),
                        Expanded(
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Flexible(
                                child: Text(
                                  subEntry.key,
                                  style: TextStyle(
                                    fontSize: 9,
                                    color: Colors.grey[700],
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              Text(
                                '${subAmount.toStringAsFixed(0)} $currency',
                                style: TextStyle(
                                  fontSize: 8,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList()),
            ],
          ),
        ),
      );
      mainColorIndex++;
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Számlák',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
        SizedBox(height: 8),
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              children: legendItems,
            ),
          ),
        ),
      ],
    );
  }
}

class SunburstPainter extends CustomPainter {
  final Map<String, dynamic> accountsData;
  final String? selectedMainAccount;
  
  static const double innerRadius = 60.0;
  static const double outerRadius = 120.0;
  static const double gap = 2.0; // Szegmensek közötti hézag

  SunburstPainter({
    required this.accountsData,
    this.selectedMainAccount,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final paint = Paint()..style = PaintingStyle.fill;
    
    // Színek definiálása
    List<Color> mainColors = [
      Color(0xFF00D4AA), // Likvid - zöld
      Color(0xFF4285F4), // Befektetés - kék  
      Color(0xFFEA4335), // Megtakarítás - piros
    ];
    
    List<Color> subColors = [
      Color(0xFF81C784), // Világos zöld
      Color(0xFF64B5F6), // Világos kék
      Color(0xFFFFB74D), // Narancssárga
      Color(0xFFF06292), // Rózsaszín
      Color(0xFFBA68C8), // Lila
      Color(0xFFAED581), // Még világosabb zöld
      Color(0xFF90CAF9), // Még világosabb kék
      Color(0xFFFFCC02), // Sárga
    ];

    // Összesített összeg számítása
    double totalAmount = 0;
    accountsData.forEach((key, value) {
      totalAmount += (value['foosszeg'] ?? 0).toDouble();
    });

    if (totalAmount == 0) return;

    // Belső kör (főszámlák) rajzolása
    double startAngle = -math.pi / 2; // Tetejéről induljon
    int mainColorIndex = 0;
    
    Map<String, double> mainAccountAngles = {};
    Map<String, double> mainAccountSweeps = {};
    
    accountsData.forEach((mainAccountKey, mainAccountValue) {
      double amount = (mainAccountValue['foosszeg'] ?? 0).toDouble();
      double sweepAngle = (amount / totalAmount) * 2 * math.pi;
      
      mainAccountAngles[mainAccountKey] = startAngle;
      mainAccountSweeps[mainAccountKey] = sweepAngle;
      
      paint.color = mainColors[mainColorIndex % mainColors.length];
      
      // Belső kör szegmens
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: innerRadius),
        startAngle,
        sweepAngle - (gap * math.pi / 180), // Kis hézag a szegmensek között
        true,
        paint,
      );
      
      startAngle += sweepAngle;
      mainColorIndex++;
    });

    // Főszámlák szövegeinek rajzolása
    startAngle = -math.pi / 2;
    mainColorIndex = 0;
    accountsData.forEach((mainAccountKey, mainAccountValue) {
      double amount = (mainAccountValue['foosszeg'] ?? 0).toDouble();
      double sweepAngle = (amount / totalAmount) * 2 * math.pi;
      
      // Csak akkor rajzoljuk ki a szöveget, ha a szegmens elég nagy
      if (sweepAngle > 0.3) { // ~17 fok minimális méret
        double midAngle = startAngle + sweepAngle / 2;
        double textRadius = (innerRadius + innerRadius * 0.6) / 2; // Középre
        
        double textX = center.dx + math.cos(midAngle) * textRadius;
        double textY = center.dy + math.sin(midAngle) * textRadius;
        
        _drawHorizontalText(
          canvas,
          mainAccountKey.toUpperCase(),
          Offset(textX, textY),
          TextStyle(
            color: Colors.white,
            fontSize: 10,
            fontWeight: FontWeight.bold,
          ),
        );
      }
      
      startAngle += sweepAngle;
      mainColorIndex++;
    });

    // Külső kör (alszámlák) rajzolása
    mainColorIndex = 0;
    accountsData.forEach((mainAccountKey, mainAccountValue) {
      Map<String, dynamic>? subAccounts = mainAccountValue['alszamlak'];
      if (subAccounts == null || subAccounts.isEmpty) {
        mainColorIndex++;
        return;
      }
      
      double mainAccountStartAngle = mainAccountAngles[mainAccountKey]!;
      double mainAccountSweepAngle = mainAccountSweeps[mainAccountKey]!;
      
      // Alszámlák összege
      double subAccountsTotal = 0;
      subAccounts.forEach((key, value) {
        subAccountsTotal += (value['balance'] ?? 0).toDouble();
      });
      
      if (subAccountsTotal == 0) {
        mainColorIndex++;
        return;
      }
      
      double subStartAngle = mainAccountStartAngle;
      int subColorIndex = 0;
      
      subAccounts.forEach((subAccountKey, subAccountValue) {
        double subAmount = (subAccountValue['balance'] ?? 0).toDouble();
        double subSweepAngle = (subAmount / subAccountsTotal) * mainAccountSweepAngle;
        
        // Szín kiválasztása - a főszámla színéhez kapcsolódó árnyalatok
        Color subColor;
        if (mainColorIndex == 0) { // Likvid - zöld árnyalatok
          subColor = subColors[subColorIndex % 3];
        } else if (mainColorIndex == 1) { // Befektetés - kék árnyalatok
          subColor = subColors[(subColorIndex + 1) % 3];
        } else { // Megtakarítás - egyéb színek
          subColor = subColors[(subColorIndex + 3) % subColors.length];
        }
        
        paint.color = subColor;
        
        // Külső kör szegmens
        canvas.drawArc(
          Rect.fromCircle(center: center, radius: outerRadius),
          subStartAngle,
          subSweepAngle - (gap * math.pi / 180),
          true,
          paint,
        );
        
        // Belső rész kivágása (donut effect)
        paint.color = Colors.white;
        canvas.drawCircle(center, innerRadius, paint);
        
        // Alszámla szövegének rajzolása
        if (subSweepAngle > 0.2) { // ~11 fok minimális méret
          double midAngle = subStartAngle + subSweepAngle / 2;
          double textRadius = (innerRadius + outerRadius) / 2;
          
          double textX = center.dx + math.cos(midAngle) * textRadius;
          double textY = center.dy + math.sin(midAngle) * textRadius;
          
          String currency = subAccountValue['currency'] ?? 'Ft';
          String displayText;
          
          // Ha a szegmens nagy, mindkét információt megjelenítjük
          if (subSweepAngle > 0.5) { // ~28 fok
            displayText = '$subAccountKey\n${subAmount.toStringAsFixed(0)} $currency';
          } else if (subSweepAngle > 0.3) { // ~17 fok
            // Közepes méret - csak az összeg
            displayText = '${subAmount.toStringAsFixed(0)} $currency';
          } else {
            // Kicsi méret - csak a név rövidítve
            displayText = subAccountKey.length > 6 ? 
              '${subAccountKey.substring(0, 6)}...' : subAccountKey;
          }
          
          _drawHorizontalText(
            canvas,
            displayText,
            Offset(textX, textY),
            TextStyle(
              color: Colors.white,
              fontSize: 8,
              fontWeight: FontWeight.w600,
            ),
          );
        }
        
        subStartAngle += subSweepAngle;
        subColorIndex++;
      });
      
      mainColorIndex++;
    });

    // Központi kör
    paint.color = Color(0xFFF5F5F5);
    canvas.drawCircle(center, innerRadius * 0.6, paint);
    
    // Központi szöveg
    final textPainter = TextPainter(
      text: TextSpan(
        text: 'Számlák\n${totalAmount.toStringAsFixed(0)} Ft',
        style: TextStyle(
          color: Colors.black87,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
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

  // Segédfüggvény vízszintes szöveg rajzolásához
  void _drawHorizontalText(Canvas canvas, String text, Offset position, TextStyle style) {
    final textPainter = TextPainter(
      text: TextSpan(text: text, style: style),
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    
    // Szöveg középponthoz igazítása
    Offset textOffset = Offset(
      position.dx - textPainter.width / 2,
      position.dy - textPainter.height / 2,
    );
    
    textPainter.paint(canvas, textOffset);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}