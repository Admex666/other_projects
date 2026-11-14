import { GameState, GridPosition, RoundSummary } from './types';
import { PlayerTurnSelection } from './hotseat';
import { BotDifficulty } from './ai/bot';

export const LOCAL_GAME_SESSION_KEY = 'bn_local_game_session';
export const MULTIPLAYER_SESSION_KEY = 'bn_session';

export interface LocalGameSession {
  version: number;
  mode: 'hotseat' | 'bot';
  gameState: GameState;
  botDifficulty: BotDifficulty;
  playerName: string;
  player2Name: string;
  activeHotseatPlayer: 'p1' | 'p2';
  p1Selection: PlayerTurnSelection | null;
  selectedTableauCardId: number | null;
  selectedReserveCardId: number | null;
  selectedPlacement: GridPosition | null;
  activationOrder: number[];
  showPassScreen: boolean;
  pendingRoundSummary: RoundSummary | null;
  lastBeeWinnerName: string | null;
  roundNotification: string | null;
  savedAt: number;
}

export type SaveLocalGameSessionInput = Omit<LocalGameSession, 'version' | 'savedAt'>;

export interface MultiplayerSession {
  roomId: string;
  playerId: string;
  sessionToken: string;
  inviteUrl?: string | null;
  round?: number;
  selectedTableauCardId?: number | null;
  selectedReserveCardId?: number | null;
  selectedPlacement?: GridPosition | null;
  activationOrder?: number[];
  hasSubmittedRound?: boolean;
}

/**
 * Persists an active Hotseat or Bot session to localStorage.
 * If the game is already in GAME_OVER phase, the saved session is removed.
 */
export function saveLocalGameSession(sessionData: SaveLocalGameSessionInput): void {
  if (typeof window === 'undefined' || !window.localStorage) return;

  try {
    if (!sessionData.gameState || sessionData.gameState.phase === 'GAME_OVER') {
      clearLocalGameSession();
      return;
    }

    const payload: LocalGameSession = {
      ...sessionData,
      version: 1,
      savedAt: Date.now(),
    };

    window.localStorage.setItem(LOCAL_GAME_SESSION_KEY, JSON.stringify(payload));
  } catch (err) {
    console.warn('Failed to save local game session to localStorage:', err);
  }
}

/**
 * Loads a persisted Hotseat or Bot game session from localStorage.
 * Returns null if no session exists, the session is corrupted, or the game is finished.
 */
export function loadLocalGameSession(): LocalGameSession | null {
  if (typeof window === 'undefined' || !window.localStorage) return null;

  try {
    const raw = window.localStorage.getItem(LOCAL_GAME_SESSION_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as Partial<LocalGameSession>;

    if (
      !parsed ||
      typeof parsed !== 'object' ||
      (parsed.mode !== 'hotseat' && parsed.mode !== 'bot') ||
      !parsed.gameState ||
      !parsed.gameState.players ||
      !parsed.gameState.phase ||
      parsed.gameState.phase === 'GAME_OVER'
    ) {
      clearLocalGameSession();
      return null;
    }

    return parsed as LocalGameSession;
  } catch (err) {
    console.warn('Failed to load local game session from localStorage:', err);
    clearLocalGameSession();
    return null;
  }
}

/**
 * Clears the persisted local game session from localStorage.
 */
export function clearLocalGameSession(): void {
  if (typeof window === 'undefined' || !window.localStorage) return;
  try {
    window.localStorage.removeItem(LOCAL_GAME_SESSION_KEY);
  } catch (err) {
    console.warn('Failed to remove local game session:', err);
  }
}

/**
 * Saves or updates multiplayer session data in localStorage under 'bn_session'.
 */
export function saveMultiplayerSession(sessionData: Partial<MultiplayerSession> & { roomId: string; playerId: string; sessionToken: string }): void {
  if (typeof window === 'undefined' || !window.localStorage) return;

  try {
    const existing = loadMultiplayerSession() || {};
    const updated: MultiplayerSession = {
      ...existing,
      ...sessionData,
    };
    window.localStorage.setItem(MULTIPLAYER_SESSION_KEY, JSON.stringify(updated));
  } catch (err) {
    console.warn('Failed to save multiplayer session to localStorage:', err);
  }
}

/**
 * Loads multiplayer session credentials and sub-screen state from localStorage.
 */
export function loadMultiplayerSession(): MultiplayerSession | null {
  if (typeof window === 'undefined' || !window.localStorage) return null;

  try {
    const raw = window.localStorage.getItem(MULTIPLAYER_SESSION_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && parsed.roomId && parsed.playerId && parsed.sessionToken) {
      return parsed as MultiplayerSession;
    }
    return null;
  } catch (err) {
    console.warn('Failed to parse multiplayer session from localStorage:', err);
    clearMultiplayerSession();
    return null;
  }
}

/**
 * Clears the multiplayer session from localStorage.
 */
export function clearMultiplayerSession(): void {
  if (typeof window === 'undefined' || !window.localStorage) return;
  try {
    window.localStorage.removeItem(MULTIPLAYER_SESSION_KEY);
  } catch (err) {
    console.warn('Failed to remove multiplayer session:', err);
  }
}
