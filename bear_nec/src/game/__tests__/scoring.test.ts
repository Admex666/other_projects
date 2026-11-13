import { describe, it, expect } from 'vitest';
import {
  isInBounds,
  isValidPlacement,
  getValidPlacements,
  calculateFinalScore,
  evaluateCardActivation,
} from '../scoring';
import { getCardById } from '../cards/catalog';
import { getCardAssetId } from '../../components/CardView';
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

  it('scores Tourist Office as 1 VP per City (red) card in tableau only', () => {
    const tableau = createEmptyTableau();
    const touristOffice = getCardById(53)!;
    const station = getCardById(52)!;
    const cactus = getCardById(42)!; // desert
    const eagle = getCardById(71)!; // mountain

    expect(touristOffice.name).toBe('Tourist Office');
    expect(touristOffice.text).toBe('1 VP per City card in your tableau.');

    tableau[0][0] = touristOffice; // city
    tableau[0][1] = station; // city
    tableau[0][2] = cactus; // desert
    tableau[1][0] = eagle; // mountain

    const player: PlayerState = {
      id: 'p1',
      name: 'Tester',
      hand: [],
      reserveCard: null,
      tableau,
      vpTokens: 0,
      beeTokens: 0,
      roundScore: 0,
    };

    // 2 City cards (Tourist Office + Station) => 2 VP, ignoring Desert and Mountain cards
    expect(evaluateCardActivation(touristOffice, tableau, { row: 0, col: 0 }, player)).toBe(2);
  });

  it('maps spritesheet slotIndex to sequential 1-based WebP asset IDs across card backs', () => {
    expect(getCardAssetId(0)).toBe(1);   // Baby Beaver -> card_01.webp
    expect(getCardAssetId(22)).toBe(23); // Water Lily -> card_23.webp
    expect(getCardAssetId(24)).toBe(24); // Coyote -> card_24.webp
    expect(getCardAssetId(44)).toBe(44); // Yucca -> card_44.webp
    expect(getCardAssetId(46)).toBe(45); // Cat -> card_45.webp
    expect(getCardAssetId(52)).toBe(51); // Station -> card_51.webp
    expect(getCardAssetId(53)).toBe(52); // Tourist Office -> card_52.webp
    expect(getCardAssetId(69)).toBe(68); // Rose -> card_68.webp
    expect(getCardAssetId(71)).toBe(69); // Eagle -> card_69.webp
    expect(getCardAssetId(96)).toBe(94); // Wild Carrot -> card_94.webp
  });
});
