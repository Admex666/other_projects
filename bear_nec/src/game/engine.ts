import {
  GameState,
  PlayerState,
  GridPosition,
  GameHistoryEntry,
  GameAction,
  CardActivationDetail,
  RoundSummary,
} from './types';
import { createDeck, shuffleDeck, dealStartingHands } from './deck';
import { createEmptyTableau, isValidPlacement } from './validation';
import {
  evaluateCardActivation,
  calculateFinalScore,
  getOrthogonalNeighbors,
} from './scoring/calculator';

/**
 * Deep clones a GameState object to maintain pure immutable transitions.
 */
export function cloneGameState(state: GameState): GameState {
  return JSON.parse(JSON.stringify(state));
}

/**
 * Initializes a new 2-player game of Bear Necessities.
 */
export function initGame(
  player1Id: string,
  player2Id: string,
  seed?: number | string
): GameState {
  const fullDeck = createDeck();
  const shuffled = shuffleDeck(fullDeck, seed);
  const { player1Hand, player2Hand, remainingDeck } = dealStartingHands(shuffled);

  const p1: PlayerState = {
    id: player1Id,
    name: player1Id,
    hand: player1Hand,
    reserveCard: null,
    tableau: createEmptyTableau(),
    vpTokens: 0,
    beeTokens: 0,
    roundScore: 0,
    connected: true,
  };

  const p2: PlayerState = {
    id: player2Id,
    name: player2Id,
    hand: player2Hand,
    reserveCard: null,
    tableau: createEmptyTableau(),
    vpTokens: 0,
    beeTokens: 0,
    roundScore: 0,
    connected: true,
  };

  const initialHistory: GameHistoryEntry[] = [
    {
      round: 1,
      phase: 'DRAFT',
      playerId: 'system',
      action: 'GAME_STARTED',
      timestamp: Date.now(),
      details: { seed: seed ?? null },
    },
  ];

  return {
    roomId: `game-${Date.now()}`,
    round: 1,
    phase: 'DRAFT',
    players: {
      [player1Id]: p1,
      [player2Id]: p2,
    },
    deck: remainingDeck,
    discardPile: [],
    status: 'in_progress',
    history: initialHistory,
    roundSummaries: [],
    winner: null,
    pendingSelections: {},
  };
}

/**
 * Helper to create initial game state with custom roomId and player list.
 */
export function createInitialGameState(
  roomId: string,
  players: { id: string; name: string }[]
): GameState {
  if (players.length !== 2) {
    throw new Error('createInitialGameState requires exactly 2 players.');
  }

  const base = initGame(players[0].id, players[1].id);
  base.roomId = roomId;
  base.players[players[0].id].name = players[0].name;
  base.players[players[1].id].name = players[1].name;
  return base;
}

/**
 * Submits card selection (tableau card + reserve card) and optional placement for a player.
 */
export function submitCardSelection(
  state: GameState,
  playerId: string,
  tableauCardId: number,
  reserveCardId: number,
  position?: GridPosition,
  activationOrder?: number[]
): GameState {
  const next = cloneGameState(state);
  const player = next.players[playerId];
  if (!player) {
    throw new Error(`Player ${playerId} not found in game.`);
  }

  const tableauCard = player.hand.find((c) => c.id === tableauCardId);
  const reserveCard = player.hand.find((c) => c.id === reserveCardId);

  if (!tableauCard || !reserveCard) {
    throw new Error(`Selected cards must be present in player's hand.`);
  }
  if (tableauCardId === reserveCardId) {
    throw new Error('Tableau card and reserve card must be distinct cards.');
  }

  // Accept valid placement position if valid; if invalid, card selection is still accepted
  // but placement is deferred until a valid position is confirmed.
  const validPlacement =
    position && isValidPlacement(player.tableau, position.row, position.col)
      ? position
      : undefined;

  // Remove selected cards from hand
  player.hand = player.hand.filter(
    (c) => c.id !== tableauCardId && c.id !== reserveCardId
  );
  player.reserveCard = reserveCard;

  if (!next.pendingSelections) {
    next.pendingSelections = {};
  }
  next.pendingSelections[playerId] = {
    tableauCard,
    reserveCard,
    placement: validPlacement,
    activationOrder: activationOrder ? [...activationOrder] : undefined,
  };

  next.history.push({
    round: next.round,
    phase: 'DRAFT',
    playerId,
    action: 'CARDS_SELECTED',
    timestamp: Date.now(),
    details: { tableauCardId, reserveCardId, position },
  });

  return next;
}

/**
 * Submits placement position for a player if not submitted during selection.
 */
export function submitPlacement(
  state: GameState,
  playerId: string,
  position: GridPosition,
  activationOrder?: number[]
): GameState {
  const next = cloneGameState(state);
  const player = next.players[playerId];
  if (!player) {
    throw new Error(`Player ${playerId} not found.`);
  }

  if (!isValidPlacement(player.tableau, position.row, position.col)) {
    throw new Error(`Placement at (${position.row}, ${position.col}) is invalid.`);
  }

  if (!next.pendingSelections || !next.pendingSelections[playerId]) {
    throw new Error(`No pending card selection found for player ${playerId}.`);
  }

  next.pendingSelections[playerId].placement = position;
  if (activationOrder) {
    next.pendingSelections[playerId].activationOrder = [...activationOrder];
  }
  return next;
}

export interface ReserveDecisions {
  [playerId: string]: 'keep' | 'discard';
}

/**
 * Resolves the round once both players have submitted cards and placement positions:
 * 1. Places tableau cards for both players.
 * 2. Cascades activations: placed card FIRST, then orthogonal neighbors in order.
 * 3. Distributes VP tokens.
 * 4. Resolves Bee Time: lowest VP this round takes 1 Bee token (tied lowest both take 1).
 * 5. Passes hands left and adds reserve card into received hand.
 * 6. At end of Round 4 and 8: handles keep/discard reserve decisions and refills hands to 5 cards.
 * 7. At end of Round 12: computes final scores with Bee Hive multiplier and declares winner.
 */
export function resolveRound(
  state: GameState,
  p1ActivationOrder?: number[],
  p2ActivationOrder?: number[],
  p1Placement?: GridPosition,
  p2Placement?: GridPosition,
  reserveDecisions?: ReserveDecisions
): GameState {
  const next = cloneGameState(state);
  const playerIds = Object.keys(next.players);
  if (playerIds.length !== 2) {
    throw new Error(`Expected exactly 2 players, got ${playerIds.length}`);
  }

  const [p1Id, p2Id] = playerIds;
  const p1 = next.players[p1Id];
  const p2 = next.players[p2Id];

  // Resolve placement coordinates
  const p1Pending = next.pendingSelections?.[p1Id];
  const p2Pending = next.pendingSelections?.[p2Id];

  const pos1 = p1Placement || p1Pending?.placement;
  const pos2 = p2Placement || p2Pending?.placement;

  if (!pos1 || !pos2) {
    throw new Error('Both players must have designated placement positions.');
  }

  const card1 = p1Pending?.tableauCard;
  const card2 = p2Pending?.tableauCard;

  if (!card1 || !card2) {
    throw new Error('Both players must have chosen a tableau card.');
  }

  // 1. Place cards into tableaus
  p1.tableau[pos1.row][pos1.col] = card1;
  p2.tableau[pos2.row][pos2.col] = card2;

  // Reset round scores
  p1.roundScore = 0;
  p2.roundScore = 0;

  // 2. Resolve activations for Player 1
  // Placed card activates FIRST
  const p1Order = p1ActivationOrder ?? p1Pending?.activationOrder;
  const p1Activations: CardActivationDetail[] = [];

  const p1SelfVP = evaluateCardActivation(card1, p1.tableau, pos1, p1, p2, {
    isPlacement: true,
  });
  p1.vpTokens += p1SelfVP;
  p1.roundScore += p1SelfVP;
  p1Activations.push({
    cardId: card1.id,
    cardName: card1.name,
    cardColor: card1.color,
    position: { ...pos1 },
    vp: p1SelfVP,
    isPlacedCard: true,
  });

  // Adjacent neighbors activate NEXT in player's chosen order
  let p1Neighbors = getOrthogonalNeighbors(p1.tableau, pos1);
  if (p1Order && p1Order.length > 0) {
    p1Neighbors.sort((a, b) => {
      const idxA = p1Order.indexOf(a.card.id);
      const idxB = p1Order.indexOf(b.card.id);
      if (idxA === -1 && idxB === -1) return 0;
      if (idxA === -1) return 1;
      if (idxB === -1) return -1;
      return idxA - idxB;
    });
  }

  for (const neighbor of p1Neighbors) {
    const nVP = evaluateCardActivation(neighbor.card, p1.tableau, neighbor.pos, p1, p2, {
      isPlacement: false,
    });
    p1.vpTokens += nVP;
    p1.roundScore += nVP;
    p1Activations.push({
      cardId: neighbor.card.id,
      cardName: neighbor.card.name,
      cardColor: neighbor.card.color,
      position: { ...neighbor.pos },
      vp: nVP,
      isPlacedCard: false,
    });
  }

  // 2. Resolve activations for Player 2
  // Placed card activates FIRST
  const p2Order = p2ActivationOrder ?? p2Pending?.activationOrder;
  const p2Activations: CardActivationDetail[] = [];

  const p2SelfVP = evaluateCardActivation(card2, p2.tableau, pos2, p2, p1, {
    isPlacement: true,
  });
  p2.vpTokens += p2SelfVP;
  p2.roundScore += p2SelfVP;
  p2Activations.push({
    cardId: card2.id,
    cardName: card2.name,
    cardColor: card2.color,
    position: { ...pos2 },
    vp: p2SelfVP,
    isPlacedCard: true,
  });

  // Adjacent neighbors activate NEXT in player's chosen order
  let p2Neighbors = getOrthogonalNeighbors(p2.tableau, pos2);
  if (p2Order && p2Order.length > 0) {
    p2Neighbors.sort((a, b) => {
      const idxA = p2Order.indexOf(a.card.id);
      const idxB = p2Order.indexOf(b.card.id);
      if (idxA === -1 && idxB === -1) return 0;
      if (idxA === -1) return 1;
      if (idxB === -1) return -1;
      return idxA - idxB;
    });
  }

  for (const neighbor of p2Neighbors) {
    const nVP = evaluateCardActivation(neighbor.card, p2.tableau, neighbor.pos, p2, p1, {
      isPlacement: false,
    });
    p2.vpTokens += nVP;
    p2.roundScore += nVP;
    p2Activations.push({
      cardId: neighbor.card.id,
      cardName: neighbor.card.name,
      cardColor: neighbor.card.color,
      position: { ...neighbor.pos },
      vp: nVP,
      isPlacedCard: false,
    });
  }

  // 3. Step 3: Bee Time
  let beesAwardedTo: string[] = [];
  if (p1.roundScore < p2.roundScore) {
    p1.beeTokens += 1;
    beesAwardedTo = [p1Id];
  } else if (p2.roundScore < p1.roundScore) {
    p2.beeTokens += 1;
    beesAwardedTo = [p2Id];
  } else {
    // Tie: both players receive 1 Bee token
    p1.beeTokens += 1;
    p2.beeTokens += 1;
    beesAwardedTo = [p1Id, p2Id];
  }

  // Record structured round summary for UI & persistent Game History
  const roundSummary: RoundSummary = {
    round: next.round,
    players: {
      [p1Id]: {
        playerId: p1Id,
        playerName: p1.name,
        placedCard: { id: card1.id, name: card1.name, color: card1.color },
        position: { ...pos1 },
        activations: p1Activations,
        totalRoundVp: p1.roundScore,
        totalVpTokens: p1.vpTokens,
        receivedBeeToken: beesAwardedTo.includes(p1Id),
      },
      [p2Id]: {
        playerId: p2Id,
        playerName: p2.name,
        placedCard: { id: card2.id, name: card2.name, color: card2.color },
        position: { ...pos2 },
        activations: p2Activations,
        totalRoundVp: p2.roundScore,
        totalVpTokens: p2.vpTokens,
        receivedBeeToken: beesAwardedTo.includes(p2Id),
      },
    },
    beeWinners: beesAwardedTo,
    isGameOver: next.round === 12,
  };
  if (!next.roundSummaries) {
    next.roundSummaries = [];
  }
  next.roundSummaries.push(roundSummary);

  next.history.push({
    round: next.round,
    phase: 'BEE_RESOLUTION',
    playerId: 'system',
    action: 'BEE_TIME_AWARDED',
    timestamp: Date.now(),
    details: {
      p1RoundScore: p1.roundScore,
      p2RoundScore: p2.roundScore,
      awardedTo: beesAwardedTo,
    },
  });

  // Check if Game Over (after Round 12)
  if (next.round === 12) {
    const p1Final = calculateFinalScore(p1);
    const p2Final = calculateFinalScore(p2);

    if (p1Final > p2Final) {
      next.winner = [p1Id];
    } else if (p2Final > p1Final) {
      next.winner = [p2Id];
    } else {
      next.winner = [p1Id, p2Id]; // Shared victory on tie
    }

    next.phase = 'GAME_OVER';
    next.status = 'game_over';
    next.pendingSelections = {};

    next.history.push({
      round: 12,
      phase: 'GAME_OVER',
      playerId: 'system',
      action: 'FINAL_SCORING',
      timestamp: Date.now(),
      details: {
        p1FinalScore: p1Final,
        p2FinalScore: p2Final,
        winner: next.winner,
      },
    });

    return next;
  }

  // 4. End of 4-round cycle check (Round 4 and 8)
  if (next.round === 4 || next.round === 8) {
    // Both players currently have 0 cards in hand and 1 reserveCard
    for (const pid of [p1Id, p2Id]) {
      const p = next.players[pid];
      const decision = reserveDecisions?.[pid] || 'keep';

      if (decision === 'discard') {
        if (p.reserveCard) {
          next.discardPile.push(p.reserveCard);
          p.reserveCard = null;
        }
        // Deal 5 cards from deck
        p.hand = next.deck.slice(0, 5);
        next.deck = next.deck.slice(5);
      } else {
        // Keep reserve card: deal 4 new cards + reserve card = 5 cards
        const dealt = next.deck.slice(0, 4);
        next.deck = next.deck.slice(4);
        p.hand = p.reserveCard ? [p.reserveCard, ...dealt] : dealt;
        p.reserveCard = null;
      }
    }
  } else {
    // Standard passing: Player 1 passes remaining hand to Player 2, and vice versa.
    // Each player adds their reserve card into the hand received from opponent.
    const p1RemainingHand = [...p1.hand];
    const p2RemainingHand = [...p2.hand];

    p1.hand = p2RemainingHand;
    if (p1.reserveCard) {
      p1.hand.push(p1.reserveCard);
      p1.reserveCard = null;
    }

    p2.hand = p1RemainingHand;
    if (p2.reserveCard) {
      p2.hand.push(p2.reserveCard);
      p2.reserveCard = null;
    }
  }

  // Advance to next round
  next.round += 1;
  next.phase = 'DRAFT';
  next.pendingSelections = {};

  return next;
}

// ---------------------------------------------------------------------------
// Server RoomManager & Multiplayer Engine Compatibility Layer
// ---------------------------------------------------------------------------

export interface EnginePlayerChoice {
  tableauCardId?: number;
  reserveCardId?: number;
  position?: GridPosition;
  activationOrder?: number[];
  decision?: 'keep' | 'discard';
}

export interface EngineTurnState {
  choices: Record<string, EnginePlayerChoice>;
}

export function createInitialTurnState(): EngineTurnState {
  return {
    choices: {},
  };
}

export function isValidAction(
  state: GameState,
  action: GameAction
): { valid: boolean; reason?: string } {
  if (action.type === 'SELECT_CARDS') {
    const player = state.players[action.playerId];
    if (!player) {
      return { valid: false, reason: 'Player not found.' };
    }
    if (action.tableauCardId === action.reserveCardId) {
      return { valid: false, reason: 'Tableau and reserve card must be different.' };
    }
    const hasTableau = player.hand.some((c) => c.id === action.tableauCardId);
    const hasReserve = player.hand.some((c) => c.id === action.reserveCardId);
    if (!hasTableau || !hasReserve) {
      return { valid: false, reason: 'Selected cards must be present in player hand.' };
    }
    return { valid: true };
  }

  if (action.type === 'CONFIRM_PLACEMENT') {
    const player = state.players[action.playerId];
    if (!player) {
      return { valid: false, reason: 'Player not found.' };
    }
    if (!isValidPlacement(player.tableau, action.position.row, action.position.col)) {
      return { valid: false, reason: 'Placement position is invalid or non-adjacent.' };
    }
    return { valid: true };
  }

  return { valid: true };
}

export function executeSelectCards(
  gameState: GameState,
  turnState: EngineTurnState,
  input: {
    playerId: string;
    tableauCardId: number;
    reserveCardId: number;
    position?: GridPosition;
    activationOrder?: number[];
  }
): {
  state: GameState;
  turnState: EngineTurnState;
  roundResolved?: {
    p1Score: number;
    p2Score: number;
    beeTokenRecipients: string[];
    round: number;
    roundScores: Record<string, number>;
    beeWinners: string[];
    roundSummary?: RoundSummary;
  };
} {
  const nextState = submitCardSelection(
    gameState,
    input.playerId,
    input.tableauCardId,
    input.reserveCardId,
    input.position,
    input.activationOrder
  );

  const nextTurnState: EngineTurnState = {
    choices: {
      ...turnState.choices,
      [input.playerId]: {
        tableauCardId: input.tableauCardId,
        reserveCardId: input.reserveCardId,
        position: input.position,
        activationOrder: input.activationOrder,
      },
    },
  };

  // Check if both players have selections and placements ready
  const pids = Object.keys(nextState.players);
  if (pids.length === 2) {
    const [p1Id, p2Id] = pids;
    const c1 = nextTurnState.choices[p1Id];
    const c2 = nextTurnState.choices[p2Id];

    if (c1?.position && c2?.position) {
      const p1PreVP = nextState.players[p1Id].vpTokens;
      const p2PreVP = nextState.players[p2Id].vpTokens;

      const resolved = resolveRound(
        nextState,
        c1.activationOrder,
        c2.activationOrder,
        c1.position,
        c2.position
      );

      const p1Score = resolved.players[p1Id].vpTokens - p1PreVP;
      const p2Score = resolved.players[p2Id].vpTokens - p2PreVP;

      const beeTokenRecipients: string[] = [];
      if (p1Score < p2Score) beeTokenRecipients.push(p1Id);
      else if (p2Score < p1Score) beeTokenRecipients.push(p2Id);
      else beeTokenRecipients.push(p1Id, p2Id);

      const roundSummary = resolved.roundSummaries?.[resolved.roundSummaries.length - 1];

      return {
        state: resolved,
        turnState: createInitialTurnState(),
        roundResolved: {
          p1Score,
          p2Score,
          beeTokenRecipients,
          round: gameState.round,
          roundScores: {
            [p1Id]: p1Score,
            [p2Id]: p2Score,
          },
          beeWinners: beeTokenRecipients,
          roundSummary,
        },
      };
    }
  }

  return {
    state: nextState,
    turnState: nextTurnState,
  };
}

export function executeConfirmPlacement(
  gameState: GameState,
  turnState: EngineTurnState,
  input: { playerId: string; position: GridPosition; activationOrder?: number[] }
): {
  state: GameState;
  turnState: EngineTurnState;
  roundResolved?: {
    p1Score: number;
    p2Score: number;
    beeTokenRecipients: string[];
    round: number;
    roundScores: Record<string, number>;
    beeWinners: string[];
    roundSummary?: RoundSummary;
  };
} {
  const nextState = submitPlacement(gameState, input.playerId, input.position, input.activationOrder);
  const nextTurnState: EngineTurnState = {
    choices: {
      ...turnState.choices,
      [input.playerId]: {
        ...turnState.choices[input.playerId],
        position: input.position,
        activationOrder: input.activationOrder,
      },
    },
  };

  const pids = Object.keys(nextState.players);
  if (pids.length === 2) {
    const [p1Id, p2Id] = pids;
    const c1 = nextTurnState.choices[p1Id];
    const c2 = nextTurnState.choices[p2Id];

    if (c1?.position && c2?.position) {
      const p1PreVP = nextState.players[p1Id].vpTokens;
      const p2PreVP = nextState.players[p2Id].vpTokens;

      const resolved = resolveRound(
        nextState,
        c1.activationOrder,
        c2.activationOrder,
        c1.position,
        c2.position
      );
      const p1Score = resolved.players[p1Id].vpTokens - p1PreVP;
      const p2Score = resolved.players[p2Id].vpTokens - p2PreVP;

      const beeTokenRecipients: string[] = [];
      if (p1Score < p2Score) beeTokenRecipients.push(p1Id);
      else if (p2Score < p1Score) beeTokenRecipients.push(p2Id);
      else beeTokenRecipients.push(p1Id, p2Id);

      const roundSummary = resolved.roundSummaries?.[resolved.roundSummaries.length - 1];

      return {
        state: resolved,
        turnState: createInitialTurnState(),
        roundResolved: {
          p1Score,
          p2Score,
          beeTokenRecipients,
          round: gameState.round,
          roundScores: {
            [p1Id]: p1Score,
            [p2Id]: p2Score,
          },
          beeWinners: beeTokenRecipients,
          roundSummary,
        },
      };
    }
  }

  return {
    state: nextState,
    turnState: nextTurnState,
  };
}

export function executeRefillDecision(
  gameState: GameState,
  turnState: EngineTurnState,
  input: { playerId: string; decision: 'keep' | 'discard' }
): { state: GameState; turnState: EngineTurnState } {
  const nextTurnState: EngineTurnState = {
    choices: {
      ...turnState.choices,
      [input.playerId]: {
        ...turnState.choices[input.playerId],
        decision: input.decision,
      },
    },
  };

  return {
    state: gameState,
    turnState: nextTurnState,
  };
}

export function restartGame(
  currentState: GameState
): { state: GameState; turnState: EngineTurnState } {
  const pids = Object.keys(currentState.players);
  const players = pids.map((id) => ({
    id,
    name: currentState.players[id].name,
  }));

  const newState = createInitialGameState(currentState.roomId, players);
  return {
    state: newState,
    turnState: createInitialTurnState(),
  };
}

