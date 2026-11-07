import { describe, it, expect } from 'vitest';
import { createInitialGameState, resolveHotseatRound } from '../hotseat';

describe('Hotseat Engine', () => {
  it('creates initial game state with 5 cards per player', () => {
    const state = createInitialGameState('Alice', 'Bob');
    expect(state.round).toBe(1);
    expect(state.phase).toBe('DRAFT');
    expect(state.players.p1.hand.length).toBe(5);
    expect(state.players.p2.hand.length).toBe(5);
    expect(state.deck.length).toBe(84); // 94 - 10
  });

  it('resolves a round and awards bee token to lowest scorer', () => {
    const state = createInitialGameState('Alice', 'Bob');
    const p1Card1 = state.players.p1.hand[0];
    const p1Card2 = state.players.p1.hand[1];
    const p2Card1 = state.players.p2.hand[0];
    const p2Card2 = state.players.p2.hand[1];

    const result = resolveHotseatRound(
      state,
      { tableauCardId: p1Card1.id, reserveCardId: p1Card2.id, position: { row: 0, col: 0 } },
      { tableauCardId: p2Card1.id, reserveCardId: p2Card2.id, position: { row: 1, col: 1 } }
    );

    expect(result.nextState.round).toBe(2);
    expect(result.nextState.players.p1.tableau[0][0]?.id).toBe(p1Card1.id);
    expect(result.nextState.players.p2.tableau[1][1]?.id).toBe(p2Card1.id);
    expect(result.beeTokenRecipients.length).toBeGreaterThan(0);
    // In round 2, starting hand size should be 4 (3 passed + 1 reserve)
    expect(result.nextState.players.p1.hand.length).toBe(4);
    expect(result.nextState.players.p2.hand.length).toBe(4);
  });
});
