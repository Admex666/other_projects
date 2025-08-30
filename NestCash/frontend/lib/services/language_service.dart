// lib/services/language_service.dart
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

class LanguageService {
  static final LanguageService _instance = LanguageService._internal();
  factory LanguageService() => _instance;
  LanguageService._internal();

  // Aktuális nyelv lekérése - BIZTONSÁGOS változat
  String get currentLanguage {
    try {
      final context = navigatorKey.currentContext;
      if (context == null) {
        print('⚠️ Navigator context is null, using default language');
        return 'hu'; // Alapértelmezett nyelv
      }
      
      final easyLocalization = EasyLocalization.of(context);
      if (easyLocalization == null) {
        print('⚠️ EasyLocalization not found, using default language');
        return 'hu';
      }
      
      return easyLocalization.locale.languageCode;
    } catch (e) {
      print('⚠️ Error getting current language: $e');
      return 'hu'; // Fallback alapértelmezett nyelv
    }
  }

  // Biztonságos nyelv lekérés kontextussal
  String getLanguageWithContext(BuildContext? context) {
    try {
      if (context == null) return 'hu';
      final easyLocalization = EasyLocalization.of(context);
      return easyLocalization?.locale.languageCode ?? 'hu';
    } catch (e) {
      print('⚠️ Language service context error: $e');
      return 'hu';
    }
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