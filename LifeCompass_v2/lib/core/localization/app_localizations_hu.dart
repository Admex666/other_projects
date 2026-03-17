// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hungarian (`hu`).
class AppLocalizationsHu extends AppLocalizations {
  AppLocalizationsHu([String locale = 'hu']) : super(locale);

  @override
  String get appTitle => 'LifeCompass v2';

  @override
  String get todayTab => 'Ma';

  @override
  String get goalsTab => 'Célok';

  @override
  String get projectsTab => 'Projektek';

  @override
  String get habitsTab => 'Szokások';

  @override
  String get profileTab => 'Profil';

  @override
  String get dailyIntention => 'Napi Szándék';

  @override
  String get whatIsYourFocus => 'Mi a mai fókuszod?';

  @override
  String get save => 'Mentés';

  @override
  String get loading => 'Betöltés...';

  @override
  String get error => 'Valami hiba történt';
}
