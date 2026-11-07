import { describe, it, expect } from 'vitest';
import {
  isInBounds,
  isValidPlacement,
  getValidPlacements,
  calculateFinalScore,
} from '../scoring';
import { CardDefinition, PlayerState, Tableau } from '../types';

describe('Scoring & Placement Rules', () => {
  const createEmptyTableau = (): Tableau => [
    [null, null, null, null],
    [null, null, null, null],
    [null, null, null, null],
  ];

  const dummyCard: CardDefinition = {
    id: 1,
    name: 'Baby Beaver',
    color: 'water',
    types: ['animal'],
    beeHives: 0,
    hasGoal: false,
    text: '3 VP if adjacent to any parent.',
    spriteIndex: 0,
  };

  it('validates in-bounds coords correctly', () => {
    expect(isInBounds(0, 0)).toBe(true);
    expect(isInBounds(2, 3)).toBe(true);
    expect(isInBounds(-1, 0)).toBe(false);
    expect(isInBounds(3, 0)).toBe(false);
    expect(isInBounds(0, 4)).toBe(false);
  });

  it('allows first card placed anywhere in 3x4 grid', () => {
    const tableau = createEmptyTableau();
    expect(isValidPlacement(tableau, 0, 0)).toBe(true);
    expect(isValidPlacement(tableau, 1, 2)).toBe(true);
    expect(getValidPlacements(tableau).length).toBe(12);
  });

  it('enforces orthogonal adjacency for subsequent placements', () => {
    const tableau = createEmptyTableau();
    tableau[1][1] = dummyCard;

    // Direct orthogonal neighbors of (1,1) are (0,1), (2,1), (1,0), (1,2)
    expect(isValidPlacement(tableau, 0, 1)).toBe(true);
    expect(isValidPlacement(tableau, 2, 1)).toBe(true);
    expect(isValidPlacement(tableau, 1, 0)).toBe(true);
    expect(isValidPlacement(tableau, 1, 2)).toBe(true);

    // Diagonal (0,0) or (2,2) is invalid
    expect(isValidPlacement(tableau, 0, 0)).toBe(false);
    expect(isValidPlacement(tableau, 2, 2)).toBe(false);

    // Occupied slot (1,1) is invalid
    expect(isValidPlacement(tableau, 1, 1)).toBe(false);
  });

  it('calculates final score with bee multiplier correctly', () => {
    const tableau = createEmptyTableau();
    tableau[0][0] = { ...dummyCard, beeHives: 2 };
    tableau[0][1] = { ...dummyCard, beeHives: 1 };

    const player: PlayerState = {
      id: 'p1',
      name: 'Tester',
      hand: [],
      reserveCard: null,
      tableau,
      vpTokens: 25,
      beeTokens: 4,
      roundScore: 0,
    };

    // 3 total hives * 4 bee tokens = 12 bonus VP.
    // 25 + 12 = 37 total VP.
    expect(calculateFinalScore(player)).toBe(37);
  });
});
