import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../domain/models/card_model.dart';

part 'deck_provider.g.dart';

@riverpod
class DeckController extends _$DeckController {
  @override
  List<CardModel> build() {
    return []; // Current Deck
  }

  void addCard(CardModel card) {
    if (state.length < 30) {
      state = [...state, card];
    }
  }

  void removeCard(String cardId) {
    final index = state.indexWhere((c) => c.id == cardId);
    if (index != -1) {
      final newState = [...state];
      newState.removeAt(index);
      state = newState;
    }
  }

  void clearDeck() {
    state = [];
  }
}

@riverpod
List<CardModel> cardCollection(CardCollectionRef ref) {
  // Dummy Collection
  return List.generate(20, (i) => CardModel(
    id: 'c_$i',
    name: 'Grimoire Card $i',
    description: 'A mysterious card from the old world.',
    type: i % 3 == 0 ? CardType.event : CardType.character,
    rarity: CardRarity.values[i % 4],
    faction: Faction.values[i % 4],
    attack: (i % 5) + 1,
    hp: (i % 5) + 2,
    luck: 5,
    stability: 5,
    manaCost: (i % 4) + 1,
    imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCo6UdCVRPa88ZdCl_e9RQBNNbsl36qmqUs_-kMgiAjx4FeUDZj9Qv4buuPD2nWfmgiv1DV2EcjlCNeKqvmakZ2XfjIEPStcHUIa7LQbdvGENN50SGKBbrBD3aKlPdQ4gzzbsggpgUczps0lwsYbGiury-OpEheMW8vAZnZZQ6logKbBcdPYvYUa5_TNpB_JzmNjl-XN2GSz44R5CyPLV_zqfh3bNYaokTj8IP1X8lhbjRMAtmOhMC_McF432sVR0vb67ulHbfVOQ',
  ));
}
