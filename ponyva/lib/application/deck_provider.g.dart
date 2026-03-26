// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'deck_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$cardCollectionHash() => r'7e7ffa0f28dece2e3b876458f151c49ad1fd7b0e';

/// See also [cardCollection].
@ProviderFor(cardCollection)
final cardCollectionProvider = AutoDisposeProvider<List<CardModel>>.internal(
  cardCollection,
  name: r'cardCollectionProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$cardCollectionHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CardCollectionRef = AutoDisposeProviderRef<List<CardModel>>;
String _$deckControllerHash() => r'28c46d55d0e7e25ae48ee3a931d46b8256a8294b';

/// See also [DeckController].
@ProviderFor(DeckController)
final deckControllerProvider =
    AutoDisposeNotifierProvider<DeckController, List<CardModel>>.internal(
      DeckController.new,
      name: r'deckControllerProvider',
      debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
          ? null
          : _$deckControllerHash,
      dependencies: null,
      allTransitiveDependencies: null,
    );

typedef _$DeckController = AutoDisposeNotifier<List<CardModel>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
