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
    expect(result.roundSummary).toBeDefined();
    expect(result.roundSummary.round).toBe(1);
    expect(result.nextState.roundSummaries?.length).toBe(1);
  });

  it('records chosen activationOrder for >= 2 adjacent cards in roundSummary', () => {
    let state = createInitialGameState('Alice', 'Bob');

    // Round 1: place at (0,0)
    const r1 = resolveHotseatRound(
      state,
      { tableauCardId: state.players.p1.hand[0].id, reserveCardId: state.players.p1.hand[1].id, position: { row: 0, col: 0 } },
      { tableauCardId: state.players.p2.hand[0].id, reserveCardId: state.players.p2.hand[1].id, position: { row: 0, col: 0 } }
    );
    state = r1.nextState;
    const neighbor1Id = state.players.p1.tableau[0][0]!.id;

    // Round 2: place at (1,1) -> wait, (1,1) is not adjacent to (0,0); place at (0,1) and (1,0) first!
    const r2 = resolveHotseatRound(
      state,
      { tableauCardId: state.players.p1.hand[0].id, reserveCardId: state.players.p1.hand[1].id, position: { row: 0, col: 1 } },
      { tableauCardId: state.players.p2.hand[0].id, reserveCardId: state.players.p2.hand[1].id, position: { row: 0, col: 1 } }
    );
    state = r2.nextState;

    const r3 = resolveHotseatRound(
      state,
      { tableauCardId: state.players.p1.hand[0].id, reserveCardId: state.players.p1.hand[1].id, position: { row: 1, col: 0 } },
      { tableauCardId: state.players.p2.hand[0].id, reserveCardId: state.players.p2.hand[1].id, position: { row: 1, col: 0 } }
    );
    state = r3.nextState;
    const neighborAId = state.players.p1.tableau[0][1]!.id;
    const neighborBId = state.players.p1.tableau[1][0]!.id;

    // Round 4: place at (1,1), which is orthogonally adjacent to (0,1) and (1,0)
    // Choose reverse order: [neighborBId, neighborAId]
    const placedCard = state.players.p1.hand[0];
    const r4 = resolveHotseatRound(
      state,
      {
        tableauCardId: placedCard.id,
        reserveCardId: state.players.p1.hand[1].id,
        position: { row: 1, col: 1 },
        activationOrder: [neighborBId, neighborAId],
      },
      {
        tableauCardId: state.players.p2.hand[0].id,
        reserveCardId: state.players.p2.hand[1].id,
        position: { row: 1, col: 1 },
      }
    );

    expect(neighbor1Id).toBeGreaterThan(0);
    const p1Summary = r4.roundSummary.players.p1;
    expect(p1Summary.activations.length).toBe(3);
    expect(p1Summary.activations[0].cardId).toBe(placedCard.id);
    expect(p1Summary.activations[0].isPlacedCard).toBe(true);
    expect(p1Summary.activations[1].cardId).toBe(neighborBId);
    expect(p1Summary.activations[2].cardId).toBe(neighborAId);
    expect(r4.nextState.roundSummaries?.length).toBe(4);
  });
});
