// lib/models/onboarding_model.dart
import 'package:frontend/models/referral_model.dart';

enum UserType {
  awareSpender,
  communityDriven,
  learner,
  advanced,
  competitive,
  defaultType,
}

extension UserTypeExtension on UserType {
  String get value {
    switch (this) {
      case UserType.awareSpender:
        return 'aware_spender';
      case UserType.communityDriven:
        return 'community_driven';
      case UserType.learner:
        return 'learner';
      case UserType.advanced:
        return 'advanced';
      case UserType.competitive:
        return 'competitive';
      case UserType.defaultType:
        return 'aware_spender';
    }
  }

  String get displayName {
    switch (this) {
      case UserType.awareSpender:
        return 'Tudatos költő';
      case UserType.communityDriven:
        return 'Közösségorientált';
      case UserType.learner:
        return 'Tanulni vágyó';
      case UserType.advanced:
        return 'Haladó';
      case UserType.competitive:
        return 'Versengő';
      case UserType.defaultType:
        return 'Tudatos költő';
    }
  }

  String get description {
    switch (this) {
      case UserType.awareSpender:
        return 'Szeretnéd jobban követni és kontrollálni a kiadásaidat';
      case UserType.communityDriven:
        return 'Fontos számodra a közösség és a másokkal való fejlődés';
      case UserType.learner:
        return 'Inspirációt és tanulási lehetőségeket keresel';
      case UserType.advanced:
        return 'Mindent akarsz, mélyre szeretnél ásni a funkciókban';
      case UserType.competitive:
        return 'Szeretnéd látni, hogyan állsz másokhoz képest';
      case UserType.defaultType:
        return 'Szeretnéd jobban követni és kontrollálni a kiadásaidat';
    }
  }

  static UserType fromString(String value) {
    switch (value) {
      case 'aware_spender':
        return UserType.awareSpender;
      case 'community_driven':
        return UserType.communityDriven;
      case 'learner':
        return UserType.learner;
      case 'advanced':
        return UserType.advanced;
      case 'competitive':
        return UserType.competitive;
      default:
        return UserType.defaultType;
    }
  }
}

enum UserIntent {
  trackSpending,
  compareWithOthers,
  learnAndImprove,
  communityGrowth,
  advancedFeatures,
  notSure,
}

extension UserIntentExtension on UserIntent {
  String get value {
    switch (this) {
      case UserIntent.trackSpending:
        return 'track_spending';
      case UserIntent.compareWithOthers:
        return 'compare_with_others';
      case UserIntent.learnAndImprove:
        return 'learn_and_improve';
      case UserIntent.communityGrowth:
        return 'community_growth';
      case UserIntent.advancedFeatures:
        return 'advanced_features';
      case UserIntent.notSure:
        return 'not_sure';
    }
  }

  String get displayName {
    switch (this) {
      case UserIntent.trackSpending:
        return 'Költések nyomon követése';
      case UserIntent.compareWithOthers:
        return 'Összehasonlítás másokkal';
      case UserIntent.learnAndImprove:
        return 'Tanulás és fejlődés';
      case UserIntent.communityGrowth:
        return 'Közösségben fejlődés';
      case UserIntent.advancedFeatures:
        return 'Haladó funkciók';
      case UserIntent.notSure:
        return 'Nem vagyok biztos';
    }
  }

  String get description {
    switch (this) {
      case UserIntent.trackSpending:
        return 'Szeretnéd részletesen követni, mire és mennyit költesz';
      case UserIntent.compareWithOthers:
        return 'Érdekel, hogy mások hogyan gazdálkodnak';
      case UserIntent.learnAndImprove:
        return 'Új pénzügyi tudást szeretnél szerezni';
      case UserIntent.communityGrowth:
        return 'Közösségben szeretnél fejlődni és segíteni másokat';
      case UserIntent.advancedFeatures:
        return 'Összetett elemzéseket és funkciókat használnál';
      case UserIntent.notSure:
        return 'Még nem tudom pontosan, mit szeretnék';
    }
  }

  static UserIntent fromString(String value) {
    switch (value) {
      case 'track_spending':
        return UserIntent.trackSpending;
      case 'compare_with_others':
        return UserIntent.compareWithOthers;
      case 'learn_and_improve':
        return UserIntent.learnAndImprove;
      case 'community_growth':
        return UserIntent.communityGrowth;
      case 'advanced_features':
        return UserIntent.advancedFeatures;
      case 'not_sure':
        return UserIntent.notSure;
      default:
        return UserIntent.notSure;
    }
  }
}

class OnboardingStep {
  final int stepNumber;
  final bool completed;
  final Map<String, dynamic>? data;

  OnboardingStep({
    required this.stepNumber,
    this.completed = false,
    this.data,
  });

  factory OnboardingStep.fromJson(Map<String, dynamic> json) {
    return OnboardingStep(
      stepNumber: json['step_number'],
      completed: json['completed'] ?? false,
      data: json['data'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'step_number': stepNumber,
      'completed': completed,
      'data': data,
    };
  }
}

// BasicSetupData osztály frissítése
class BasicSetupData {
  final String preferredCurrency;
  final double? initialBalance;
  final String? mainAccountName;
  final ReferralSource? referralSource;
  final String? referralDetails;

  const BasicSetupData({
    this.preferredCurrency = 'HUF',
    this.initialBalance,
    this.mainAccountName = 'Fő számla',
    this.referralSource,
    this.referralDetails, 
  });

  factory BasicSetupData.fromJson(Map<String, dynamic> json) {
    return BasicSetupData(
      preferredCurrency: json['preferred_currency'] ?? 'HUF',
      initialBalance: json['initial_balance']?.toDouble(),
      mainAccountName: json['main_account_name'] ?? 'Fő számla',
      referralSource: json['referral_source'] != null 
          ? ReferralSource.fromString(json['referral_source'])
          : null,  
      referralDetails: json['referral_details'], 
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'preferred_currency': preferredCurrency,
      'initial_balance': initialBalance,
      'main_account_name': mainAccountName,
      'referral_source': referralSource?.value, 
      'referral_details': referralDetails, 
    };
  }
}

class OnboardingProgress {
  final int currentStep;
  final List<OnboardingStep> completedSteps;
  final UserType? userType;
  final List<UserIntent> selectedIntents;
  final BasicSetupData? basicSetup;
  final bool tutorialCompleted;
  final bool onboardingCompleted;

  OnboardingProgress({
    this.currentStep = 0,
    this.completedSteps = const [],
    this.userType,
    this.selectedIntents = const [],
    this.basicSetup,
    this.tutorialCompleted = false,
    this.onboardingCompleted = false,
  });

  factory OnboardingProgress.fromJson(Map<String, dynamic> json) {
    return OnboardingProgress(
      currentStep: json['current_step'] ?? 0,
      completedSteps: (json['completed_steps'] as List<dynamic>?)
          ?.map((step) => OnboardingStep.fromJson(step))
          .toList() ?? [],
      userType: json['user_type'] != null 
          ? UserTypeExtension.fromString(json['user_type'])
          : null,
      selectedIntents: (json['selected_intents'] as List<dynamic>?)
          ?.map((intent) => UserIntentExtension.fromString(intent))
          .toList() ?? [],
      basicSetup: json['basic_setup'] != null
          ? BasicSetupData.fromJson(json['basic_setup'])
          : null,
      tutorialCompleted: json['tutorial_completed'] ?? false,
      onboardingCompleted: json['onboarding_completed'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'current_step': currentStep,
      'completed_steps': completedSteps.map((step) => step.toJson()).toList(),
      'user_type': userType?.value,
      'selected_intents': selectedIntents.map((intent) => intent.value).toList(),
      'basic_setup': basicSetup?.toJson(),
      'tutorial_completed': tutorialCompleted,
      'onboarding_completed': onboardingCompleted,
    };
  }

  OnboardingProgress copyWith({
    int? currentStep,
    List<OnboardingStep>? completedSteps,
    UserType? userType,
    List<UserIntent>? selectedIntents,
    BasicSetupData? basicSetup,
    bool? tutorialCompleted,
    bool? onboardingCompleted,
  }) {
    return OnboardingProgress(
      currentStep: currentStep ?? this.currentStep,
      completedSteps: completedSteps ?? this.completedSteps,
      userType: userType ?? this.userType,
      selectedIntents: selectedIntents ?? this.selectedIntents,
      basicSetup: basicSetup ?? this.basicSetup,
      tutorialCompleted: tutorialCompleted ?? this.tutorialCompleted,
      onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
    );
  }
}

// API Request/Response modellek
class UserIntentSelection {
  final List<UserIntent> intents;

  UserIntentSelection({required this.intents});

  Map<String, dynamic> toJson() {
    return {
      'intents': intents.map((intent) => intent.value).toList(),
    };
  }
}

class UpdateOnboardingStepRequest {
  final int step;
  final Map<String, dynamic>? data;

  UpdateOnboardingStepRequest({
    required this.step,
    this.data,
  });

  Map<String, dynamic> toJson() {
    return {
      'step': step,
      'data': data,
    };
  }
}

class OnboardingStatusResponse {
  final int currentStep;
  final UserType? userType;
  final List<UserIntent> selectedIntents;
  final bool onboardingCompleted;
  final String? nextRecommendedAction;

  OnboardingStatusResponse({
    required this.currentStep,
    this.userType,
    this.selectedIntents = const [],
    required this.onboardingCompleted,
    this.nextRecommendedAction,
  });

  factory OnboardingStatusResponse.fromJson(Map<String, dynamic> json) {
    return OnboardingStatusResponse(
      currentStep: json['current_step'],
      userType: json['user_type'] != null
          ? UserTypeExtension.fromString(json['user_type'])
          : null,
      selectedIntents: (json['selected_intents'] as List<dynamic>?)
          ?.map((intent) => UserIntentExtension.fromString(intent))
          .toList() ?? [],
      onboardingCompleted: json['onboarding_completed'],
      nextRecommendedAction: json['next_recommended_action'],
    );
  }
}

class TutorialContent {
  final String title;
  final String description;
  final List<TutorialStep> steps;
  final String? nextAction;

  TutorialContent({
    required this.title,
    required this.description,
    required this.steps,
    this.nextAction,
  });

  factory TutorialContent.fromJson(Map<String, dynamic> json) {
    return TutorialContent(
      title: json['title'],
      description: json['description'],
      steps: (json['steps'] as List<dynamic>)
          .map((step) => TutorialStep.fromJson(step))
          .toList(),
      nextAction: json['next_action'],
    );
  }
}

class TutorialStep {
  final String title;
  final String content;
  final String? imagePath;
  final String? highlightElement;

  TutorialStep({
    required this.title,
    required this.content,
    this.imagePath,
    this.highlightElement,
  });

  factory TutorialStep.fromJson(Map<String, dynamic> json) {
    return TutorialStep(
      title: json['title'],
      content: json['content'],
      imagePath: json['image_path'],
      highlightElement: json['highlight_element'],
    );
  }
}