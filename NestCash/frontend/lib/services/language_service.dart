// lib/services/language_service.dart
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

class LanguageService {
  static final LanguageService _instance = LanguageService._internal();
  factory LanguageService() => _instance;
  LanguageService._internal();

  // Aktuális nyelv lekérése
  String get currentLanguage {
    final context = EasyLocalization.of(navigatorKey.currentContext!);
    return context?.locale.languageCode ?? 'hu';
  }

  // Támogatott nyelvek
  static const List<Locale> supportedLocales = [
    Locale('hu', 'HU'),
    Locale('en', 'US'),
  ];

  // Navigator key a context eléréshez
  static final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  // Nyelv váltás
  void changeLanguage(String languageCode) {
    final context = navigatorKey.currentContext;
    if (context != null) {
      Locale newLocale;
      switch (languageCode) {
        case 'en':
          newLocale = const Locale('en', 'US');
          break;
        case 'hu':
        default:
          newLocale = const Locale('hu', 'HU');
      }
      context.setLocale(newLocale);
    }
  }
}