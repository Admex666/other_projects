import { describe, it, expect } from 'vitest';
import type {
  CardColor,
  CardType,
  CardDefinition,
  GridPosition,
  Tableau,
  PlayerState,
  GameState,
  GameAction,
} from '../types';

describe('Game Core Types', () => {
  it('creates valid CardDefinition instances', () => {
    const color: CardColor = 'water';
    const type: CardType = 'bearfolk';
    const card: CardDefinition = {
      id: 1,
      name: 'Fisherbear',
      color,
      types: [type],
      beeHives: 0,
      hasGoal: false,
      text: '4 VP if adjacent to at least 1 Plant.',
      spriteIndex: 0,
    };

    expect(card.name).toBe('Fisherbear');
    expect(card.color).toBe('water');
    expect(card.types).toContain('bearfolk');
    expect(card.beeHives).toBe(0);
    expect(card.hasGoal).toBe(false);
  });

  it('validates Tableau 4x3 grid structure', () => {
    const emptyTableau: Tableau = [
      [null, null, null, null],
      [null, null, null, null],
      [null, null, null, null],
    ];

    expect(emptyTableau.length).toBe(3);
    expect(emptyTableau[0].length).toBe(4);

    const pos: GridPosition = { row: 1, col: 2 };
    expect(pos.row).toBe(1);
    expect(pos.col).toBe(2);
  });

  it('initializes a valid PlayerState', () => {
    const player: PlayerState = {
      id: 'p1',
      name: 'Player 1',
      hand: [],
      reserveCard: null,
      tableau: [
        [null, null, null, null],
        [null, null, null, null],
        [null, null, null, null],
      ],
      vpTokens: 0,
      beeTokens: 0,
      roundScore: 0,
      connected: true,
    };

    expect(player.id).toBe('p1');
    expect(player.vpTokens).toBe(0);
    expect(player.beeTokens).toBe(0);
    expect(player.tableau.length).toBe(3);
  });

  it('constructs a valid GameState and checks action union types', () => {
    const player1: PlayerState = {
      id: 'p1',
      name: 'Alice',
      hand: [],
      reserveCard: null,
      tableau: [
        [null, null, null, null],
        [null, null, null, null],
        [null, null, null, null],
      ],
      vpTokens: 0,
      beeTokens: 0,
      roundScore: 0,
    };

    const gameState: GameState = {
      roomId: 'room-123',
      round: 1,
      phase: 'DRAFT',
      players: { p1: player1 },
      deck: [],
      discardPile: [],
      status: 'in_progress',
      history: [],
      winner: null,
    };

    expect(gameState.round).toBe(1);
    expect(gameState.phase).toBe('DRAFT');

    const actions: GameAction[] = [
      {
        type: 'SELECT_CARDS',
        playerId: 'p1',
        tableauCardId: 10,
        reserveCardId: 12,
      },
      {
        type: 'CONFIRM_PLACEMENT',
        playerId: 'p1',
        position: { row: 0, col: 0 },
      },
      {
        type: 'ORDER_ACTIVATION',
        playerId: 'p1',
        cardActivationOrder: [10, 5],
      },
      {
        type: 'KEEP_OR_DISCARD_RESERVE',
        playerId: 'p1',
        decision: 'keep',
      },
      {
        type: 'REMATCH',
        playerId: 'p1',
      },
    ];

    expect(actions.length).toBe(5);
    expect(actions[0].type).toBe('SELECT_CARDS');
  });
});
