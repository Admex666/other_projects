# Implementation Plan - Paprika Storm

## 🎯 Modern Objective
Develop "Paprika Storm," a mobile card game with a "Folk-Punk Grimoire" aesthetic, focusing on 1v1 quick matches, deck building, and "controlled chaos" mechanics.

## 🛠️ Phase 2: Gameplay & Persistence

### 🎴 Card Data & Collection
- **[NEW] [card_registry.dart](file:///c:/Users/Adam/Data/other_projects/ponyva/lib/domain/data/card_registry.dart)**: Define the core set of actual card data (Betyár, Sárkány cohorts).
- **[NEW] [deck_storage.dart](file:///c:/Users/Adam/Data/other_projects/ponyva/lib/infrastructure/deck_storage.dart)**: Implement `shared_preferences` persistence for the player's deck and collection.

### ⚔️ Match Logic Refinement
- **[MOD] [match_provider.dart](file:///c:/Users/Adam/Data/other_projects/ponyva/lib/application/match_provider.dart)**:
  - Complex damage calculation (attack minus luck/stability).
  - Status effects (Stun, Burn, Bleed).
  - Turn phases: Upkeep, Draw, Action, Cleanup.

### 🖥️ Responsive Deck Builder
- **[MOD] [deck_builder_screen.dart](file:///c:/Users/Adam/Data/other_projects/ponyva/lib/presentation/screens/deck_builder_screen.dart)**:
  - Grid responsiveness for different aspect ratios.
  - Better drag-and-drop or tap-to-add gestures.
  - Advanced filtering (rarity, faction, cost).

## ✅ Verification
- **Automated Tests**: Unit tests for damage logic and persistence.
- **Manual Verification**: Verify deck loading after app restart.
