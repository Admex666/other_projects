import { CardDefinition } from './types';
import { CARD_CATALOG } from './cards/catalog';

/**
 * Creates a fresh deck of all 94 playable cards.
 */
export function createDeck(): CardDefinition[] {
  return CARD_CATALOG.map((card) => ({
    ...card,
    types: [...card.types],
    effect: card.effect ? { ...card.effect } : undefined,
  }));
}

/**
 * Deterministic pseudo-random number generator for seeded shuffles.
 */
function createPRNG(seed?: number | string): () => number {
  if (seed === undefined) {
    return Math.random;
  }
  let s: number;
  if (typeof seed === 'string') {
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
      hash = (Math.imul(31, hash) + seed.charCodeAt(i)) | 0;
    }
    s = hash >>> 0;
  } else {
    s = seed >>> 0;
  }

  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Shuffles a deck using Fisher-Yates shuffle algorithm.
 * Returns a new array.
 */
export function shuffleDeck(deck: CardDefinition[], seed?: number | string): CardDefinition[] {
  const result = [...deck];
  const rand = createPRNG(seed);

  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }

  return result;
}

/**
 * Deals 5 cards to player 1 and 5 cards to player 2.
 * Returns hands and remaining draw pile.
 */
export function dealStartingHands(deck: CardDefinition[]): {
  player1Hand: CardDefinition[];
  player2Hand: CardDefinition[];
  remainingDeck: CardDefinition[];
} {
  if (deck.length < 10) {
    throw new Error(`Deck must have at least 10 cards to deal starting hands, got ${deck.length}`);
  }

  const p1Hand: CardDefinition[] = [];
  const p2Hand: CardDefinition[] = [];

  for (let i = 0; i < 5; i++) {
    p1Hand.push(deck[i * 2]);
    p2Hand.push(deck[i * 2 + 1]);
  }

  const canScoreImmediate = (c: CardDefinition): boolean =>
    c.hasGoal ||
    c.effect?.type === 'flat_vp' ||
    c.effect?.type === 'dandelion' ||
    c.effect?.type === 'largest_group' ||
    c.effect?.type === 'tableau_type_count' ||
    c.effect?.type === 'row_col_color' ||
    c.effect?.type === 'row_col_type_color' ||
    c.effect?.type === 'tableau_name_starts_s' ||
    c.effect?.type === 'tableau_card_count';

  p1Hand.sort((a, b) => (canScoreImmediate(b) ? 1 : 0) - (canScoreImmediate(a) ? 1 : 0));
  p2Hand.sort((a, b) => (canScoreImmediate(b) ? 1 : 0) - (canScoreImmediate(a) ? 1 : 0));

  const remainingDeck = deck.slice(10);

  return {
    player1Hand: p1Hand,
    player2Hand: p2Hand,
    remainingDeck,
  };
}
