import {
  PlayerState,
  GridPosition,
  CardDefinition,
  Tableau,
} from '../types';
import { getValidPlacements } from '../validation';
import {
  evaluateCardActivation,
  getOrthogonalNeighbors,
} from '../scoring/calculator';

export type BotDifficulty = 'easy' | 'medium' | 'hard';

export interface BotMove {
  tableauCardId: number;
  reserveCardId: number;
  position: GridPosition;
}

export type BotRefillDecision = 'keep' | 'discard';

interface EvaluatedMove {
  tableauCardId: number;
  reserveCardId: number;
  position: GridPosition;
  score: number;
  immediateVp: number;
}

/**
 * Creates a shallow clone of the tableau with one card placed at `pos`.
 */
function simulateTableauPlacement(
  tableau: Tableau,
  card: CardDefinition,
  pos: GridPosition
): Tableau {
  return tableau.map((rowArr, r) =>
    rowArr.map((cell, c) => (r === pos.row && c === pos.col ? card : cell))
  );
}

/**
 * Simulates immediate VP gained from placing `card` at `pos`.
 * According to game rules:
 * 1. Placed card activates FIRST with { isPlacement: true }
 * 2. Orthogonally adjacent neighbors activate NEXT with { isPlacement: false }
 */
export function simulateImmediateVp(
  tableau: Tableau,
  card: CardDefinition,
  pos: GridPosition,
  botPlayerState: PlayerState,
  opponentPlayerState?: PlayerState
): number {
  const simTableau = simulateTableauPlacement(tableau, card, pos);

  // 1. Placed card activates first
  let vp = evaluateCardActivation(card, simTableau, pos, botPlayerState, opponentPlayerState, {
    isPlacement: true,
  });

  // 2. Orthogonally adjacent neighbors activate next
  const neighbors = getOrthogonalNeighbors(simTableau, pos);
  for (const neighbor of neighbors) {
    vp += evaluateCardActivation(
      neighbor.card,
      simTableau,
      neighbor.pos,
      botPlayerState,
      opponentPlayerState,
      { isPlacement: false }
    );
  }

  return vp;
}

/**
 * Evaluates the strategic value / synergy of a reserve card to be used in future turns.
 */
export function evaluateReserveSynergy(
  card: CardDefinition,
  botPlayerState: PlayerState,
  round: number
): number {
  let score = 0;

  // Bee hives are valuable, especially if bot already has or is accumulating bee tokens
  const beeWeight = Math.max(1, botPlayerState.beeTokens);
  score += card.beeHives * (beeWeight * 1.5);

  // Goal cards have high upside if fulfilled
  if (card.hasGoal) {
    score += 2;
  }

  // Base effect potential
  if (card.effect) {
    if (typeof card.effect.points === 'number') {
      score += card.effect.points * 0.5;
    } else if (typeof card.effect.metPoints === 'number') {
      score += card.effect.metPoints * 0.5;
    } else {
      score += 2; // general effect potential
    }
  }

  // Cards with end-of-game or late-game value are slightly favored earlier
  if (round <= 6 && card.beeHives > 0) {
    score += 1;
  }

  return score;
}

/**
 * Evaluates a candidate bot move combining immediate VP, bee hive priority,
 * and reserve card synergy.
 */
function evaluateCandidateMove(
  tableauCard: CardDefinition,
  reserveCard: CardDefinition,
  pos: GridPosition,
  botPlayerState: PlayerState,
  opponentPlayerState: PlayerState | undefined,
  round: number
): EvaluatedMove {
  const immediateVp = simulateImmediateVp(
    botPlayerState.tableau,
    tableauCard,
    pos,
    botPlayerState,
    opponentPlayerState
  );

  let totalScore = immediateVp;

  // Heuristic 1: Bee Hive prioritization on placed card
  // If bot already has bee tokens, placing cards with hives guarantees high multiplier at end game.
  // Even with 0 bee tokens, hives might pay off if bot collects bees later.
  const currentBees = botPlayerState.beeTokens;
  if (tableauCard.beeHives > 0) {
    // Value each hive by estimated bee token payoff (at least 1.5 VP per hive, up to currentBees * 2 VP)
    const hiveMultiplier = Math.max(1.5, currentBees * 1.8);
    totalScore += tableauCard.beeHives * hiveMultiplier;
  }

  // Heuristic 2: Reserve card synergy
  const reserveScore = evaluateReserveSynergy(reserveCard, botPlayerState, round);
  // Reserve weight factor (reserves are played soon, either passed back or used next round)
  totalScore += reserveScore * 0.8;

  // Heuristic 3: Centering / adjacency flexibility bonus for early rounds
  if (round <= 3) {
    // Prefer placing closer to center (row 1, col 1 or 2) to maintain maximum placement freedom
    const distFromCenter = Math.abs(pos.row - 1) + Math.abs(pos.col - 1.5);
    totalScore -= distFromCenter * 0.2;
  }

  return {
    tableauCardId: tableauCard.id,
    reserveCardId: reserveCard.id,
    position: pos,
    score: totalScore,
    immediateVp,
  };
}

/**
 * Chooses the bot's move for the round:
 * - 1 card from hand for tableau
 * - 1 card from hand for reserve
 * - 1 valid placement position in 4x3 tableau
 */
export function chooseBotMove(
  botPlayerState: PlayerState,
  opponentPlayerState?: PlayerState,
  round: number = 1,
  difficulty: BotDifficulty = 'medium'
): BotMove {
  const hand = botPlayerState.hand;
  if (!hand || hand.length < 2) {
    throw new Error('Bot must have at least 2 cards in hand to choose a move.');
  }

  const validPositions = getValidPlacements(botPlayerState.tableau);
  if (validPositions.length === 0) {
    throw new Error('No valid placement positions found in tableau.');
  }

  const candidates: EvaluatedMove[] = [];

  // Evaluate all permutations of (tableauCard, reserveCard, validPosition)
  for (let i = 0; i < hand.length; i++) {
    for (let j = 0; j < hand.length; j++) {
      if (i === j) continue;
      const tableauCard = hand[i];
      const reserveCard = hand[j];

      for (const pos of validPositions) {
        const candidate = evaluateCandidateMove(
          tableauCard,
          reserveCard,
          pos,
          botPlayerState,
          opponentPlayerState,
          round
        );
        candidates.push(candidate);
      }
    }
  }

  if (candidates.length === 0) {
    // Fallback safeguard
    return {
      tableauCardId: hand[0].id,
      reserveCardId: hand[1].id,
      position: validPositions[0],
    };
  }

  // Sort descending by score
  candidates.sort((a, b) => b.score - a.score);

  // Difficulty adjustment
  if (difficulty === 'easy') {
    // Easy: Pick from the top 50% or introduce randomness
    const samplePoolSize = Math.max(1, Math.min(candidates.length, 6));
    const randomIndex = Math.floor(Math.random() * samplePoolSize);
    const chosen = candidates[randomIndex];
    return {
      tableauCardId: chosen.tableauCardId,
      reserveCardId: chosen.reserveCardId,
      position: chosen.position,
    };
  } else if (difficulty === 'medium') {
    // Medium: Pick among the top 2-3 moves to have slight variety while playing strong
    const samplePoolSize = Math.min(candidates.length, 3);
    const randomIndex = Math.floor(Math.random() * samplePoolSize);
    const chosen = candidates[randomIndex];
    return {
      tableauCardId: chosen.tableauCardId,
      reserveCardId: chosen.reserveCardId,
      position: chosen.position,
    };
  }

  // Hard: Always select the highest evaluated move
  const best = candidates[0];
  return {
    tableauCardId: best.tableauCardId,
    reserveCardId: best.reserveCardId,
    position: best.position,
  };
}

/**
 * Chooses whether to 'keep' or 'discard' the reserve card at the end of rounds 4 and 8.
 * In Bear Necessities, at the end of rounds 4 and 8:
 * - 'keep': bot keeps the reserve card, and receives 4 new cards from the deck (total 5).
 * - 'discard': bot discards reserve card, and receives 5 new cards from the deck (total 5).
 */
export function chooseBotRefillDecision(
  botPlayerState: PlayerState,
  round: number = 4
): BotRefillDecision {
  const reserve = botPlayerState.reserveCard;
  if (!reserve) {
    return 'discard';
  }

  // Calculate value of keeping this reserve card
  const value = evaluateReserveSynergy(reserve, botPlayerState, round);

  // Decision threshold:
  // An average new card from deck provides around ~3-4 expected value.
  // If reserve card has high synergy (bee hives + bee tokens, or high score goal), keep it.
  // Otherwise, discard to get a fresh card from deck.
  if (reserve.beeHives > 0 && botPlayerState.beeTokens >= 2) {
    return 'keep';
  }

  if (value >= 4.0) {
    return 'keep';
  }

  return 'discard';
}
