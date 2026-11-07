import type {
  GameState,
  Tableau,
  CardDefinition,
  CardColor,
  CardType,
  GamePhase,
  GameStatus,
  GameHistoryEntry,
  GridPosition,
  GameAction,
} from '../game/types';

// ==========================================
// Masked & Sanitized Game State Types
// ==========================================

export interface MaskedCard {
  id: number;
  name: string;
  color: CardColor;
  types: CardType[];
  beeHives: number;
  hasGoal: boolean;
  text: string;
  spriteIndex: number;
  hidden: true;
}

export type PublicOrMaskedCard = CardDefinition | MaskedCard;

export interface SanitizedPlayerState {
  id: string;
  name: string;
  hand: PublicOrMaskedCard[];
  reserveCard: PublicOrMaskedCard | null;
  tableau: Tableau;
  vpTokens: number;
  beeTokens: number;
  roundScore: number;
  connected?: boolean;
}

export interface SanitizedGameState {
  roomId: string;
  round: number;
  phase: GamePhase;
  players: Record<string, SanitizedPlayerState>;
  deck: MaskedCard[];
  discardPile: CardDefinition[];
  status: GameStatus;
  history: GameHistoryEntry[];
  winner: string[] | null;
}

// ==========================================
// Client -> Server Message Types
// ==========================================

export interface CreateRoomMessage {
  type: 'CREATE_ROOM';
  playerName: string;
}

export interface JoinRoomMessage {
  type: 'JOIN_ROOM';
  roomId: string;
  playerName: string;
}

export interface ReconnectMessage {
  type: 'RECONNECT';
  roomId: string;
  playerId: string;
  sessionToken: string;
}

export interface SubmitSelectionMessage {
  type: 'SUBMIT_SELECTION';
  roomId: string;
  playerId: string;
  sessionToken: string;
  tableauCardId: number;
  reserveCardId: number;
  position?: GridPosition;
}

export interface ChooseRefillOptionMessage {
  type: 'CHOOSE_REFILL_OPTION';
  roomId: string;
  playerId: string;
  sessionToken: string;
  decision: 'keep' | 'discard';
}

export interface RequestRematchMessage {
  type: 'REQUEST_REMATCH';
  roomId: string;
  playerId: string;
  sessionToken: string;
}

export interface ConfirmPlacementMessage {
  type: 'CONFIRM_PLACEMENT';
  roomId: string;
  playerId: string;
  sessionToken: string;
  position: GridPosition;
}

export interface GameActionMessage {
  type: 'GAME_ACTION';
  roomId: string;
  playerId: string;
  sessionToken: string;
  action: GameAction;
}

export type ClientMessage =
  | CreateRoomMessage
  | JoinRoomMessage
  | ReconnectMessage
  | SubmitSelectionMessage
  | ChooseRefillOptionMessage
  | RequestRematchMessage
  | ConfirmPlacementMessage
  | GameActionMessage;

// ==========================================
// Server -> Client Message Types
// ==========================================

export interface RoomCreatedMessage {
  type: 'ROOM_CREATED';
  roomId: string;
  playerId: string;
  sessionToken: string;
  inviteUrl: string;
}

export interface RoomJoinedMessage {
  type: 'ROOM_JOINED';
  roomId: string;
  playerId: string;
  sessionToken: string;
  hostName?: string;
}

export interface GameStartedMessage {
  type: 'GAME_STARTED';
  roomId: string;
  state: SanitizedGameState;
}

export interface StateUpdateMessage {
  type: 'STATE_UPDATE';
  roomId: string;
  state: SanitizedGameState;
  reason?: string;
}

export interface RoundResolvedMessage {
  type: 'ROUND_RESOLVED';
  roomId: string;
  round: number;
  roundScores: Record<string, number>;
  beeWinners: string[];
  state: SanitizedGameState;
}

export interface ErrorMessage {
  type: 'ERROR';
  code: string;
  message: string;
}

export interface OpponentDisconnectedMessage {
  type: 'OPPONENT_DISCONNECTED';
  playerId: string;
  playerName: string;
}

export interface OpponentReconnectedMessage {
  type: 'OPPONENT_RECONNECTED';
  playerId: string;
  playerName: string;
}

export type ServerMessage =
  | RoomCreatedMessage
  | RoomJoinedMessage
  | GameStartedMessage
  | StateUpdateMessage
  | RoundResolvedMessage
  | ErrorMessage
  | OpponentDisconnectedMessage
  | OpponentReconnectedMessage;

// ==========================================
// State Filtering / Sanitization Function
// ==========================================

export function createMaskedCard(color: CardColor = 'water', name = 'Hidden Card'): MaskedCard {
  return {
    id: -1,
    name,
    color,
    types: [],
    beeHives: 0,
    hasGoal: false,
    text: '',
    spriteIndex: -1,
    hidden: true,
  };
}

/**
 * Strips secret information (opponent hand, opponent secret reserve card, draw deck order)
 * before sending game state to a specific player.
 */
export function filterStateForPlayer(gameState: GameState, playerId: string): SanitizedGameState {
  const sanitizedPlayers: Record<string, SanitizedPlayerState> = {};

  for (const [id, player] of Object.entries(gameState.players)) {
    if (id === playerId) {
      // Current player sees their own cards fully
      sanitizedPlayers[id] = {
        id: player.id,
        name: player.name,
        hand: player.hand.map(c => ({ ...c })),
        reserveCard: player.reserveCard ? { ...player.reserveCard } : null,
        tableau: player.tableau.map(row => row.map(cell => (cell ? { ...cell } : null))),
        vpTokens: player.vpTokens,
        beeTokens: player.beeTokens,
        roundScore: player.roundScore,
        connected: player.connected,
      };
    } else {
      // Opponent cards are masked!
      sanitizedPlayers[id] = {
        id: player.id,
        name: player.name,
        hand: player.hand.map(card => createMaskedCard(card.color, 'Hidden Card')),
        reserveCard: player.reserveCard ? createMaskedCard(player.reserveCard.color, 'Hidden Reserve') : null,
        tableau: player.tableau.map(row => row.map(cell => (cell ? { ...cell } : null))),
        vpTokens: player.vpTokens,
        beeTokens: player.beeTokens,
        roundScore: player.roundScore,
        connected: player.connected,
      };
    }
  }

  // Draw deck is secret to everyone - mask all cards in deck while preserving count
  const sanitizedDeck: MaskedCard[] = gameState.deck.map(card => createMaskedCard(card.color, 'Draw Deck'));

  return {
    roomId: gameState.roomId,
    round: gameState.round,
    phase: gameState.phase,
    players: sanitizedPlayers,
    deck: sanitizedDeck,
    discardPile: gameState.discardPile.map(c => ({ ...c })),
    status: gameState.status,
    history: gameState.history.map(entry => ({ ...entry })),
    winner: gameState.winner ? [...gameState.winner] : null,
  };
}
