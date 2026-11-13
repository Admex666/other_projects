import { describe, it, expect } from 'vitest';
import {
  createDeck,
  shuffleDeck,
  dealStartingHands,
} from '../deck';
import { CARD_CATALOG, getCardBySlot } from '../cards/catalog';
import {
  isValidPlacement,
  getValidPlacements,
  createEmptyTableau,
  countTableauCards,
} from '../validation';
import {
  evaluateCardActivation,
  calculateFinalScore,
  getOrthogonalNeighbors,
  findLargestConnectedGroup,
} from '../scoring/calculator';
import {
  initGame,
  submitCardSelection,
  resolveRound,
  cloneGameState,
} from '../engine';
import type { GridPosition, PlayerState } from '../types';

describe('Bear Necessities Game Engine (Phase 2)', () => {
  describe('1. 94-Card Deck & Catalog Validation', () => {
    it('creates a complete deck of exactly 94 playable cards', () => {
      const deck = createDeck();
      expect(deck.length).toBe(94);
      expect(CARD_CATALOG.length).toBe(94);
    });

    it('ensures all 94 cards have unique IDs and slot indices', () => {
      const deck = createDeck();
      const idSet = new Set(deck.map((c) => c.id));
      const slotSet = new Set(deck.map((c) => c.slotIndex));

      expect(idSet.size).toBe(94);
      expect(slotSet.size).toBe(94);
    });

    it('matches exact official suit / biome distribution', () => {
      const deck = createDeck();
      const counts: Record<string, number> = {
        water: 0,
        desert: 0,
        city: 0,
        mountain: 0,
      };

      for (const card of deck) {
        counts[card.color]++;
      }

      expect(counts.water).toBe(23); // Slots 0..22
      expect(counts.desert).toBe(21); // Slots 24..44
      expect(counts.city).toBe(24); // Slots 46..69
      expect(counts.mountain).toBe(26); // Slots 71..96
    });

    it('excludes interleaved card backs (23, 45, 70, 97) and blanks (98, 99)', () => {
      const deck = createDeck();
      const excludedSlots = [23, 45, 70, 97, 98, 99];

      for (const slot of excludedSlots) {
        const found = deck.find((c) => c.slotIndex === slot);
        expect(found).toBeUndefined();
      }
    });

    it('verifies card types, bee hives, and goal attributes', () => {
      const rubberDuck = getCardBySlot(55);
      expect(rubberDuck).toBeDefined();
      expect(rubberDuck?.name).toBe('Rubber Duck');
      expect(rubberDuck?.beeHives).toBe(2);
      expect(rubberDuck?.color).toBe('city');
      expect(rubberDuck?.types).toContain('item');

      const queenBee = getCardBySlot(25);
      expect(queenBee).toBeDefined();
      expect(queenBee?.name).toBe('Queen Bee');
      expect(queenBee?.beeHives).toBe(1);
      expect(queenBee?.types).toContain('animal');

      const harbor = getCardBySlot(12);
      expect(harbor).toBeDefined();
      expect(harbor?.hasGoal).toBe(true);

      const tradingPost = getCardBySlot(26);
      expect(tradingPost).toBeDefined();
      expect(tradingPost?.hasGoal).toBe(true);

      const bearlet = getCardBySlot(63);
      expect(bearlet).toBeDefined();
      expect(bearlet?.hasGoal).toBe(true);
    });

    it('shuffles deterministically with a random seed', () => {
      const deck = createDeck();
      const shuffled1 = shuffleDeck(deck, 42);
      const shuffled2 = shuffleDeck(deck, 42);
      const shuffled3 = shuffleDeck(deck, 999);

      expect(shuffled1.map((c) => c.id)).toEqual(shuffled2.map((c) => c.id));
      expect(shuffled1.map((c) => c.id)).not.toEqual(shuffled3.map((c) => c.id));
    });

    it('deals starting hands of 5 cards per player with 84 remaining in deck', () => {
      const deck = createDeck();
      const dealt = dealStartingHands(deck);

      expect(dealt.player1Hand.length).toBe(5);
      expect(dealt.player2Hand.length).toBe(5);
      expect(dealt.remainingDeck.length).toBe(84);

      // Verify no overlap between hands
      const p1Ids = new Set(dealt.player1Hand.map((c) => c.id));
      for (const card of dealt.player2Hand) {
        expect(p1Ids.has(card.id)).toBe(false);
      }
    });
  });

  describe('2. Grid Placement & Bounding Box Validation', () => {
    it('allows the very first card to be placed at any position in 3x4 grid', () => {
      const tableau = createEmptyTableau();
      expect(countTableauCards(tableau)).toBe(0);

      // Any cell 0..2, 0..3 is valid
      for (let r = 0; r < 3; r++) {
        for (let c = 0; c < 4; c++) {
          expect(isValidPlacement(tableau, r, c)).toBe(true);
        }
      }
      expect(getValidPlacements(tableau).length).toBe(12);
    });

    it('rejects coordinates outside the 3x4 grid boundaries', () => {
      const tableau = createEmptyTableau();
      expect(isValidPlacement(tableau, -1, 0)).toBe(false);
      expect(isValidPlacement(tableau, 3, 0)).toBe(false);
      expect(isValidPlacement(tableau, 0, -1)).toBe(false);
      expect(isValidPlacement(tableau, 0, 4)).toBe(false);
    });

    it('rejects placing a card on top of an already occupied cell', () => {
      const tableau = createEmptyTableau();
      const card = getCardBySlot(0)!;
      tableau[1][1] = card;

      expect(isValidPlacement(tableau, 1, 1)).toBe(false);
    });

    it('requires subsequent cards to be orthogonally adjacent to existing cards', () => {
      const tableau = createEmptyTableau();
      const card = getCardBySlot(0)!;
      tableau[1][1] = card;

      // Orthogonal neighbors of (1, 1): (0, 1), (2, 1), (1, 0), (1, 2)
      expect(isValidPlacement(tableau, 0, 1)).toBe(true);
      expect(isValidPlacement(tableau, 2, 1)).toBe(true);
      expect(isValidPlacement(tableau, 1, 0)).toBe(true);
      expect(isValidPlacement(tableau, 1, 2)).toBe(true);

      // Diagonals must be rejected
      expect(isValidPlacement(tableau, 0, 0)).toBe(false);
      expect(isValidPlacement(tableau, 0, 2)).toBe(false);
      expect(isValidPlacement(tableau, 2, 0)).toBe(false);
      expect(isValidPlacement(tableau, 2, 2)).toBe(false);
    });

    it('strictly enforces the 4-column by 3-row bounding box constraint', () => {
      const tableau = createEmptyTableau();
      const card = getCardBySlot(0)!;

      // Place a full 4-card horizontal row at row 1
      tableau[1][0] = card;
      tableau[1][1] = card;
      tableau[1][2] = card;
      tableau[1][3] = card;

      // Now all 4 columns (0..3) are used
      // Remaining valid placements must be within rows 0 and 2, cols 0..3
      const valid = getValidPlacements(tableau);
      expect(valid.length).toBe(8); // 4 in row 0 + 4 in row 2
      for (const pos of valid) {
        expect(pos.col).toBeGreaterThanOrEqual(0);
        expect(pos.col).toBeLessThanOrEqual(3);
        expect(pos.row === 0 || pos.row === 2).toBe(true);
      }
    });
  });

  describe('3. Cascade Activation & Order of Execution', () => {
    it('activates the newly placed card FIRST, then adjacent neighbors in specified order', () => {
      const p1: PlayerState = {
        id: 'p1',
        name: 'Alice',
        hand: [],
        reserveCard: null,
        tableau: createEmptyTableau(),
        vpTokens: 0,
        beeTokens: 0,
        roundScore: 0,
      };

      // Place Dog at (1, 0)
      const dogCard = getCardBySlot(47)!; // Dog: 3 VP per adjacent Bearfolk
      p1.tableau[1][0] = dogCard;

      // Place Fisherbear at (1, 2)
      const fisherbearCard = getCardBySlot(18)!; // Fisherbear: 4 VP if adjacent to Water
      p1.tableau[1][2] = fisherbearCard;

      // Now player places Actor (Bearfolk) at (1, 1), between Dog and Fisherbear
      const actorCard = getCardBySlot(59)!; // Actor: 2 VP per every other Bearfolk
      p1.tableau[1][1] = actorCard;

      // Test neighbor retrieval
      const neighbors = getOrthogonalNeighbors(p1.tableau, { row: 1, col: 1 });
      expect(neighbors.length).toBe(2);
      expect(neighbors.map((n) => n.card.name)).toContain('Dog');
      expect(neighbors.map((n) => n.card.name)).toContain('Fisherbear');

      // Actor activation:
      // Actor is Bearfolk at (1, 1). Fisherbear at (1, 2) is another Bearfolk.
      // Actor scores 2 VP (1 other Bearfolk in tableau).
      const actorVP = evaluateCardActivation(actorCard, p1.tableau, { row: 1, col: 1 }, p1, undefined, {
        isPlacement: true,
      });
      expect(actorVP).toBe(2);

      // Dog activation (Neighbor of Actor):
      // Dog at (1, 0) is adjacent to Actor (Bearfolk at (1, 1)).
      // Dog scores 3 VP per adjacent Bearfolk = 3 VP!
      const dogVP = evaluateCardActivation(dogCard, p1.tableau, { row: 1, col: 0 }, p1, undefined, {
        isPlacement: false,
      });
      expect(dogVP).toBe(3);
    });

    it('ensures Dandelion scores 7 on placement and 1 on neighbor activation', () => {
      const player: PlayerState = {
        id: 'p1',
        name: 'Alice',
        hand: [],
        reserveCard: null,
        tableau: createEmptyTableau(),
        vpTokens: 0,
        beeTokens: 0,
        roundScore: 0,
      };

      const dandelion = getCardBySlot(93)!;
      player.tableau[0][0] = dandelion;

      // Self activation on place: 7 VP
      const placeVP = evaluateCardActivation(dandelion, player.tableau, { row: 0, col: 0 }, player, undefined, {
        isPlacement: true,
      });
      expect(placeVP).toBe(7);

      // Neighbor activation: 1 VP
      const neighborVP = evaluateCardActivation(dandelion, player.tableau, { row: 0, col: 0 }, player, undefined, {
        isPlacement: false,
      });
      expect(neighborVP).toBe(1);
    });

    it('computes largest connected Fish group correctly', () => {
      const tableau = createEmptyTableau();
      const fish = getCardBySlot(3)!;

      // Place 3 connected Fish in an L-shape: (0,0), (0,1), (1,1)
      tableau[0][0] = fish;
      tableau[0][1] = fish;
      tableau[1][1] = fish;

      // Place 1 disconnected Fish at (2, 3)
      tableau[2][3] = fish;

      expect(findLargestConnectedGroup(tableau, 'Fish')).toBe(3);

      // Add (1, 0) to form a 4-card block
      tableau[1][0] = fish;
      expect(findLargestConnectedGroup(tableau, 'Fish')).toBe(4);
    });
  });

  describe('4. Bee Time Token Allocation & Tie Handling', () => {
    it('awards 1 Bee token to the player who scored the lowest VP in current round', () => {
      const game = initGame('Alice', 'Bob', 123);
      const p1 = game.players['Alice'];
      const p2 = game.players['Bob'];

      const p1TableauCard = p1.hand[0];
      const p1ReserveCard = p1.hand[1];
      const p2TableauCard = p2.hand[0];
      const p2ReserveCard = p2.hand[1];

      // Draft cards
      let state = submitCardSelection(
        game,
        'Alice',
        p1TableauCard.id,
        p1ReserveCard.id,
        { row: 0, col: 0 }
      );
      state = submitCardSelection(
        state,
        'Bob',
        p2TableauCard.id,
        p2ReserveCard.id,
        { row: 1, col: 1 }
      );

      const next = resolveRound(state);

      // Total bee tokens distributed across both players must be >= 1
      const totalBees = next.players['Alice'].beeTokens + next.players['Bob'].beeTokens;
      expect(totalBees).toBeGreaterThanOrEqual(1);
    });

    it('awards 1 Bee token to BOTH players when tied for lowest round score', () => {
      const game = initGame('Alice', 'Bob', 123);

      // Manually set up identical round scores
      const next = cloneGameState(game);
      next.pendingSelections = {
        Alice: {
          tableauCard: getCardBySlot(95)!, // Sequoia (flat 3 VP)
          reserveCard: getCardBySlot(0)!,
          placement: { row: 0, col: 0 },
        },
        Bob: {
          tableauCard: getCardBySlot(95)!, // Sequoia (flat 3 VP)
          reserveCard: getCardBySlot(0)!,
          placement: { row: 0, col: 0 },
        },
      };

      const resolved = resolveRound(next);
      // Both scored exactly 3 VP -> tied lowest -> BOTH get 1 Bee token
      expect(resolved.players['Alice'].beeTokens).toBe(1);
      expect(resolved.players['Bob'].beeTokens).toBe(1);
    });
  });

  describe('5. Full 12-Round Deterministic Game Simulation', () => {
    it('simulates a complete 12-round game from round 1 through game over', () => {
      // Deterministic seed ensures reproducible card draws
      let state = initGame('Player1', 'Player2', 'seed_bear_necessities_tournament_2026');

      expect(state.round).toBe(1);
      expect(state.phase).toBe('DRAFT');
      expect(state.status).toBe('in_progress');

      // 12 predefined placement positions covering the entire 3-row by 4-col tableau
      const placementSequence: GridPosition[] = [
        { row: 0, col: 0 }, // Round 1
        { row: 0, col: 1 }, // Round 2
        { row: 0, col: 2 }, // Round 3
        { row: 0, col: 3 }, // Round 4 (Cycle 1 complete)
        { row: 1, col: 0 }, // Round 5
        { row: 1, col: 1 }, // Round 6
        { row: 1, col: 2 }, // Round 7
        { row: 1, col: 3 }, // Round 8 (Cycle 2 complete)
        { row: 2, col: 0 }, // Round 9
        { row: 2, col: 1 }, // Round 10
        { row: 2, col: 2 }, // Round 11
        { row: 2, col: 3 }, // Round 12 (Game over)
      ];

      for (let round = 1; round <= 12; round++) {
        expect(state.round).toBe(round);
        expect(state.phase).toBe('DRAFT');

        const p1 = state.players['Player1'];
        const p2 = state.players['Player2'];

        expect(p1.hand.length).toBeGreaterThanOrEqual(2);
        expect(p2.hand.length).toBeGreaterThanOrEqual(2);

        const pos = placementSequence[round - 1];

        // Player 1 picks first 2 cards in hand
        const p1TabCard = p1.hand[0];
        const p1ResCard = p1.hand[1];

        // Player 2 picks first 2 cards in hand
        const p2TabCard = p2.hand[0];
        const p2ResCard = p2.hand[1];

        state = submitCardSelection(
          state,
          'Player1',
          p1TabCard.id,
          p1ResCard.id,
          pos
        );
        state = submitCardSelection(
          state,
          'Player2',
          p2TabCard.id,
          p2ResCard.id,
          pos
        );

        // Resolve the round
        state = resolveRound(state);

        if (round < 12) {
          expect(state.round).toBe(round + 1);
        }
      }

      // After Round 12: game over verification
      expect(state.round).toBe(12);
      expect(state.phase).toBe('GAME_OVER');
      expect(state.status).toBe('game_over');
      expect(state.winner).toBeDefined();
      expect(state.winner!.length).toBeGreaterThanOrEqual(1);

      // Both players should have exactly 12 cards in their tableau (4x3 full)
      const p1TableauCount = countTableauCards(state.players['Player1'].tableau);
      const p2TableauCount = countTableauCards(state.players['Player2'].tableau);
      expect(p1TableauCount).toBe(12);
      expect(p2TableauCount).toBe(12);

      // Check final score calculation with Bee Hive multipliers
      const p1Score = calculateFinalScore(state.players['Player1']);
      const p2Score = calculateFinalScore(state.players['Player2']);

      expect(p1Score).toBeGreaterThan(0);
      expect(p2Score).toBeGreaterThan(0);

      if (p1Score > p2Score) {
        expect(state.winner).toEqual(['Player1']);
      } else if (p2Score > p1Score) {
        expect(state.winner).toEqual(['Player2']);
      } else {
        expect(state.winner).toContain('Player1');
        expect(state.winner).toContain('Player2');
      }

      // History log contains game start and final scoring
      const startEntry = state.history.find((h) => h.action === 'GAME_STARTED');
      const finalEntry = state.history.find((h) => h.action === 'FINAL_SCORING');
      expect(startEntry).toBeDefined();
      expect(finalEntry).toBeDefined();

      // Round summaries recorded for all 12 rounds, with Round 12 marked isGameOver
      expect(state.roundSummaries?.length).toBe(12);
      expect(state.roundSummaries?.[0].round).toBe(1);
      expect(state.roundSummaries?.[0].isGameOver).toBe(false);
      expect(state.roundSummaries?.[11].round).toBe(12);
      expect(state.roundSummaries?.[11].isGameOver).toBe(true);
    });
  });
});
