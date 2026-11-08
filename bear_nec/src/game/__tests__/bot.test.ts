import { describe, it, expect } from 'vitest';
import {
  initGame,
  submitCardSelection,
  resolveRound,
  chooseBotMove,
  chooseBotRefillDecision,
  isValidPlacement,
  calculateFinalScore,
  createDeck,
  createEmptyTableau,
} from '../index';
import type { PlayerState, CardDefinition } from '../types';

describe('AI Bot Opponent for Bear Necessities', () => {
  it('chooses valid distinct cards present in hand and a legal placement position', () => {
    const gameState = initGame('HumanPlayer', 'BotPlayer', 12345);
    const botState = gameState.players['BotPlayer'];
    const humanState = gameState.players['HumanPlayer'];

    const move = chooseBotMove(botState, humanState, 1, 'hard');

    // Bot chooses cards from its hand
    const handCardIds = botState.hand.map((c) => c.id);
    expect(handCardIds).toContain(move.tableauCardId);
    expect(handCardIds).toContain(move.reserveCardId);

    // Cards must be distinct
    expect(move.tableauCardId).not.toBe(move.reserveCardId);

    // Placement position must be legal
    expect(isValidPlacement(botState.tableau, move.position.row, move.position.col)).toBe(true);
  });

  it('works for all difficulties (easy, medium, hard)', () => {
    const gameState = initGame('HumanPlayer', 'BotPlayer', 54321);
    const botState = gameState.players['BotPlayer'];
    const humanState = gameState.players['HumanPlayer'];

    for (const difficulty of ['easy', 'medium', 'hard'] as const) {
      const move = chooseBotMove(botState, humanState, 1, difficulty);
      const handCardIds = botState.hand.map((c) => c.id);

      expect(handCardIds).toContain(move.tableauCardId);
      expect(handCardIds).toContain(move.reserveCardId);
      expect(move.tableauCardId).not.toBe(move.reserveCardId);
      expect(isValidPlacement(botState.tableau, move.position.row, move.position.col)).toBe(true);
    }
  });

  it('prioritizes Bee Hive symbols when bot has accumulated Bee tokens', () => {
    const deck = createDeck();
    const botState: PlayerState = {
      id: 'BotPlayer',
      name: 'Bot',
      hand: [],
      reserveCard: null,
      tableau: createEmptyTableau(),
      vpTokens: 10,
      beeTokens: 4, // Bot has many bee tokens
      roundScore: 0,
    };

    // Find a card with 2 bee hives and a card with 0 bee hives
    const cardWith2Hives = deck.find((c) => c.beeHives === 2)!;
    const cardWith0Hives = deck.find((c) => c.beeHives === 0 && !c.hasGoal)!;
    const fillerCard = deck.find((c) => c.id !== cardWith2Hives.id && c.id !== cardWith0Hives.id)!;

    botState.hand = [cardWith0Hives, cardWith2Hives, fillerCard];

    const move = chooseBotMove(botState, undefined, 5, 'hard');

    // Because bee tokens are high (4), the card with 2 hives gives immense multiplier bonus
    expect(move.tableauCardId).toBe(cardWith2Hives.id);
  });

  it('returns valid refill decisions at rounds 4 and 8', () => {
    const deck = createDeck();
    const botState: PlayerState = {
      id: 'BotPlayer',
      name: 'Bot',
      hand: [],
      reserveCard: null,
      tableau: createEmptyTableau(),
      vpTokens: 5,
      beeTokens: 0,
      roundScore: 0,
    };

    // When reserveCard is null
    expect(chooseBotRefillDecision(botState, 4)).toBe('discard');

    // When reserve card has high value or hives with bee tokens
    const hiveCard = deck.find((c) => c.beeHives === 2)!;
    botState.reserveCard = hiveCard;
    botState.beeTokens = 3;
    expect(chooseBotRefillDecision(botState, 4)).toBe('keep');

    // When reserve card has 0 hives and no bee tokens and low value
    const weakCard: CardDefinition = {
      id: 999,
      name: 'Weak Card',
      color: 'water',
      types: ['plant'],
      beeHives: 0,
      hasGoal: false,
      text: 'No points',
      spriteIndex: 0,
    };
    botState.reserveCard = weakCard;
    botState.beeTokens = 0;
    expect(chooseBotRefillDecision(botState, 4)).toBe('discard');
  });

  it('can simulate an entire 12-round game with the bot without crashing', () => {
    let state = initGame('HumanPlayer', 'BotPlayer', 99999);

    for (let round = 1; round <= 12; round++) {
      expect(state.round).toBe(round);
      expect(state.phase).toBe('DRAFT');

      const human = state.players['HumanPlayer'];
      const bot = state.players['BotPlayer'];

      // Bot chooses its move
      const botMove = chooseBotMove(bot, human, round, 'hard');

      // Human chooses valid move (e.g. first 2 cards and first valid placement)
      const validHumanPlacements = [
        // precomputed valid path or using valid positions
        ...state.players['HumanPlayer'].hand,
      ];
      expect(validHumanPlacements.length).toBeGreaterThanOrEqual(2);

      const humanMove = chooseBotMove(human, bot, round, 'medium');

      // Submit selections
      state = submitCardSelection(
        state,
        'HumanPlayer',
        humanMove.tableauCardId,
        humanMove.reserveCardId,
        humanMove.position
      );

      state = submitCardSelection(
        state,
        'BotPlayer',
        botMove.tableauCardId,
        botMove.reserveCardId,
        botMove.position
      );

      // Handle refill decisions for rounds 4 and 8
      let reserveDecisions: Record<string, 'keep' | 'discard'> | undefined;
      if (round === 4 || round === 8) {
        reserveDecisions = {
          HumanPlayer: chooseBotRefillDecision(state.players['HumanPlayer'], round),
          BotPlayer: chooseBotRefillDecision(state.players['BotPlayer'], round),
        };
      }

      state = resolveRound(
        state,
        undefined,
        undefined,
        undefined,
        undefined,
        reserveDecisions
      );
    }

    // Verify game finished cleanly
    expect(state.phase).toBe('GAME_OVER');
    expect(state.status).toBe('game_over');
    expect(state.round).toBe(12);
    expect(state.winner).toBeDefined();

    const botFinalScore = calculateFinalScore(state.players['BotPlayer']);
    const humanFinalScore = calculateFinalScore(state.players['HumanPlayer']);

    expect(botFinalScore).toBeGreaterThan(0);
    expect(humanFinalScore).toBeGreaterThan(0);
  });
});
