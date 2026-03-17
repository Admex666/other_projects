// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'LifeCompass v2';

  @override
  String get todayTab => 'Today';

  @override
  String get goalsTab => 'Goals';

  @override
  String get projectsTab => 'Projects';

  @override
  String get habitsTab => 'Habits';

  @override
  String get profileTab => 'Profile';

  @override
  String get dailyIntention => 'Daily Intention';

  @override
  String get whatIsYourFocus => 'What is your focus today?';

  @override
  String get save => 'Save';

  @override
  String get loading => 'Loading...';

  @override
  String get error => 'Something went wrong';
}
