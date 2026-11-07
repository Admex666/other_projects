/**
 * Bear Necessities - Game Core Types
 * Based on official Mojito Studios rulebook
 */

export type CardColor = 'city' | 'desert' | 'mountain' | 'water';

export type CardType = 'bearfolk' | 'building' | 'item' | 'plant' | 'animal';

export interface CardEffect {
  type: string;
  points?: number;
  [key: string]: unknown;
}

export interface CardDefinition {
  id: number;
  slotIndex?: number;
  name: string;
  color: CardColor;
  types: CardType[];
  beeHives: number; // 0, 1, or 2 Bee Hive multiplier symbols
  hasGoal: boolean; // whether the card contains a Goal requirement
  text: string;
  spriteIndex: number;
  effect?: CardEffect;
}

export interface GridPosition {
  row: number; // 0 to 2 for a 3-row grid (or within dynamic 3-row bounds)
  col: number; // 0 to 3 for a 4-col grid (or within dynamic 4-col bounds)
}

/**
 * 4x3 grid representation (3 rows by 4 columns).
 * Tableau entries are either a CardDefinition or null for empty slots.
 */
export type Tableau = (CardDefinition | null)[][];

export interface PlayerState {
  id: string;
  name: string;
  hand: CardDefinition[];
  reserveCard: CardDefinition | null;
  tableau: Tableau;
  vpTokens: number;
  beeTokens: number;
  roundScore: number;
  connected?: boolean;
}

export type GamePhase =
  | 'DRAFT'                    // Select 1 card for tableau, 1 for reserve
  | 'PLACEMENT'                // Place chosen card in tableau
  | 'ACTIVATION'               // Sequence activation of newly placed card & adjacent cards
  | 'BEE_RESOLUTION'           // Award bee token to lowest scorer of round
  | 'PASS_HANDS'               // Pass remaining cards to neighbor, retrieve reserve
  | 'RESERVE_DECISION'         // At end of round 4 & 8: keep or discard reserve card
  | 'GAME_OVER';

export type GameStatus = 'waiting' | 'in_progress' | 'completed' | 'game_over' | 'abandoned';

export interface ActivationContext {
  isPlacement?: boolean;
  activationOrder?: number[];
  allOpponents?: PlayerState[];
}

export interface RoundSelection {
  tableauCard: CardDefinition;
  reserveCard: CardDefinition;
  placement?: GridPosition;
}

export interface GameHistoryEntry {
  round: number;
  phase: GamePhase;
  playerId: string;
  action: string;
  timestamp: number;
  details?: Record<string, unknown>;
}

export interface GameState {
  roomId: string;
  round: number; // 1 to 12
  phase: GamePhase;
  players: Record<string, PlayerState>;
  deck: CardDefinition[];
  discardPile: CardDefinition[];
  status: GameStatus;
  history: GameHistoryEntry[];
  winner: string[] | null; // Array of playerIds sharing victory, or null if ongoing
  pendingSelections?: Record<string, RoundSelection>;
}

// Player Actions (Client -> Server)
export type GameAction =
  | {
      type: 'SELECT_CARDS';
      playerId: string;
      tableauCardId: number;
      reserveCardId: number;
    }
  | {
      type: 'CONFIRM_PLACEMENT';
      playerId: string;
      position: GridPosition;
    }
  | {
      type: 'ORDER_ACTIVATION';
      playerId: string;
      cardActivationOrder: number[]; // Array of card IDs in the chosen activation order
    }
  | {
      type: 'KEEP_OR_DISCARD_RESERVE';
      playerId: string;
      decision: 'keep' | 'discard';
    }
  | {
      type: 'REMATCH';
      playerId: string;
    };
