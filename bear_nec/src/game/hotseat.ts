import { GameState, GridPosition } from './types';
import { initGame, submitCardSelection, resolveRound } from './engine';

export interface PlayerTurnSelection {
  tableauCardId: number;
  reserveCardId: number;
  position: GridPosition;
}

export interface TurnResolutionResult {
  nextState: GameState;
  p1VpScored: number;
  p2VpScored: number;
  beeTokenRecipients: string[];
  logMessage: string;
}

/**
 * Creates initial 2-player local hotseat game
 */
export function createInitialGameState(player1Name = 'Player 1', player2Name = 'Player 2'): GameState {
  const state = initGame('p1', 'p2');
  state.players.p1.name = player1Name;
  state.players.p2.name = player2Name;
  state.roomId = 'LOCAL-' + Math.random().toString(36).substring(2, 8).toUpperCase();
  return state;
}

/**
 * Resolves a full round once both players have chosen their moves in local hotseat
 */
export function resolveHotseatRound(
  currentState: GameState,
  p1Choice: PlayerTurnSelection,
  p2Choice: PlayerTurnSelection
): TurnResolutionResult {
  let state = submitCardSelection(
    currentState,
    'p1',
    p1Choice.tableauCardId,
    p1Choice.reserveCardId,
    p1Choice.position
  );

  state = submitCardSelection(
    state,
    'p2',
    p2Choice.tableauCardId,
    p2Choice.reserveCardId,
    p2Choice.position
  );

  const prevP1Bees = state.players.p1.beeTokens;
  const prevP2Bees = state.players.p2.beeTokens;

  const nextState = resolveRound(state);

  const p1VpScored = nextState.players.p1.roundScore;
  const p2VpScored = nextState.players.p2.roundScore;

  const beeTokenRecipients: string[] = [];
  if (nextState.players.p1.beeTokens > prevP1Bees) {
    beeTokenRecipients.push('p1');
  }
  if (nextState.players.p2.beeTokens > prevP2Bees) {
    beeTokenRecipients.push('p2');
  }

  const roundNum = currentState.round;
  const logMessage = `Round ${roundNum} complete: ${nextState.players.p1.name} scored ${p1VpScored} VP, ${nextState.players.p2.name} scored ${p2VpScored} VP.`;

  return {
    nextState,
    p1VpScored,
    p2VpScored,
    beeTokenRecipients,
    logMessage,
  };
}
