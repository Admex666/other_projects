import { describe, it, expect, beforeEach, vi, beforeAll, afterAll } from 'vitest';
import {
  saveLocalGameSession,
  loadLocalGameSession,
  clearLocalGameSession,
  saveMultiplayerSession,
  loadMultiplayerSession,
  clearMultiplayerSession,
  LOCAL_GAME_SESSION_KEY,
  MULTIPLAYER_SESSION_KEY,
} from '../persistence';
import { createInitialGameState } from '../hotseat';

// In-memory mock for localStorage
function createMockLocalStorage() {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => (key in store ? store[key] : null),
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] || null,
  };
}

describe('Local and Multiplayer Session Persistence', () => {
  const mockStorage = createMockLocalStorage();

  beforeAll(() => {
    (globalThis as any).localStorage = mockStorage;
    (globalThis as any).window = { localStorage: mockStorage };
  });

  afterAll(() => {
    delete (globalThis as any).localStorage;
    delete (globalThis as any).window;
  });

  beforeEach(() => {
    mockStorage.clear();
    vi.restoreAllMocks();
  });

  describe('Local Game Session (Hotseat / AI Bot)', () => {
    it('persists and restores active hotseat game session with all state', () => {
      const initialGameState = createInitialGameState('Alice', 'Bob');

      saveLocalGameSession({
        mode: 'hotseat',
        gameState: initialGameState,
        botDifficulty: 'medium',
        playerName: 'Alice',
        player2Name: 'Bob',
        activeHotseatPlayer: 'p1',
        p1Selection: {
          tableauCardId: 10,
          reserveCardId: 15,
          position: { row: 1, col: 1 },
        },
        selectedTableauCardId: 5,
        selectedReserveCardId: 8,
        selectedPlacement: { row: 2, col: 2 },
        activationOrder: [1, 2],
        showPassScreen: false,
        pendingRoundSummary: null,
        lastBeeWinnerName: 'Alice',
        roundNotification: 'Test notification',
      });

      const restored = loadLocalGameSession();
      expect(restored).not.toBeNull();
      expect(restored?.mode).toBe('hotseat');
      expect(restored?.playerName).toBe('Alice');
      expect(restored?.player2Name).toBe('Bob');
      expect(restored?.selectedTableauCardId).toBe(5);
      expect(restored?.selectedReserveCardId).toBe(8);
      expect(restored?.selectedPlacement).toEqual({ row: 2, col: 2 });
      expect(restored?.activationOrder).toEqual([1, 2]);
      expect(restored?.p1Selection?.tableauCardId).toBe(10);
      expect(restored?.roundNotification).toBe('Test notification');
      expect(restored?.gameState.round).toBe(1);
    });

    it('persists and restores bot game session with botDifficulty', () => {
      const initialGameState = createInitialGameState('Explorer', 'BearBot (Hard)');

      saveLocalGameSession({
        mode: 'bot',
        gameState: initialGameState,
        botDifficulty: 'hard',
        playerName: 'Explorer',
        player2Name: 'BearBot (Hard)',
        activeHotseatPlayer: 'p1',
        p1Selection: null,
        selectedTableauCardId: null,
        selectedReserveCardId: null,
        selectedPlacement: null,
        activationOrder: [],
        showPassScreen: false,
        pendingRoundSummary: null,
        lastBeeWinnerName: null,
        roundNotification: null,
      });

      const restored = loadLocalGameSession();
      expect(restored).not.toBeNull();
      expect(restored?.mode).toBe('bot');
      expect(restored?.botDifficulty).toBe('hard');
      expect(restored?.playerName).toBe('Explorer');
    });

    it('clears session when saving a game in GAME_OVER phase', () => {
      const gameOverState = createInitialGameState('Alice', 'Bob');
      gameOverState.phase = 'GAME_OVER';

      saveLocalGameSession({
        mode: 'hotseat',
        gameState: gameOverState,
        botDifficulty: 'medium',
        playerName: 'Alice',
        player2Name: 'Bob',
        activeHotseatPlayer: 'p1',
        p1Selection: null,
        selectedTableauCardId: null,
        selectedReserveCardId: null,
        selectedPlacement: null,
        activationOrder: [],
        showPassScreen: false,
        pendingRoundSummary: null,
        lastBeeWinnerName: null,
        roundNotification: null,
      });

      expect(mockStorage.getItem(LOCAL_GAME_SESSION_KEY)).toBeNull();
      expect(loadLocalGameSession()).toBeNull();
    });

    it('clears and ignores corrupted or invalid JSON in storage', () => {
      mockStorage.setItem(LOCAL_GAME_SESSION_KEY, '{invalidJson:::');
      expect(loadLocalGameSession()).toBeNull();
      expect(mockStorage.getItem(LOCAL_GAME_SESSION_KEY)).toBeNull();

      mockStorage.setItem(LOCAL_GAME_SESSION_KEY, JSON.stringify({ mode: 'unknown' }));
      expect(loadLocalGameSession()).toBeNull();
      expect(mockStorage.getItem(LOCAL_GAME_SESSION_KEY)).toBeNull();
    });

    it('clearLocalGameSession deletes the stored key', () => {
      mockStorage.setItem(LOCAL_GAME_SESSION_KEY, '{"test":1}');
      clearLocalGameSession();
      expect(mockStorage.getItem(LOCAL_GAME_SESSION_KEY)).toBeNull();
    });
  });

  describe('Multiplayer Session Persistence', () => {
    it('persists and restores multiplayer session credentials and draft selections', () => {
      saveMultiplayerSession({
        roomId: 'WOOD12',
        playerId: 'p_12345678',
        sessionToken: 'tok_abcdef',
        inviteUrl: 'http://localhost:3001/?room=WOOD12',
        round: 3,
        selectedTableauCardId: 12,
        selectedReserveCardId: 19,
        selectedPlacement: { row: 0, col: 1 },
        hasSubmittedRound: false,
      });

      const restored = loadMultiplayerSession();
      expect(restored).not.toBeNull();
      expect(restored?.roomId).toBe('WOOD12');
      expect(restored?.playerId).toBe('p_12345678');
      expect(restored?.sessionToken).toBe('tok_abcdef');
      expect(restored?.round).toBe(3);
      expect(restored?.selectedTableauCardId).toBe(12);
      expect(restored?.selectedReserveCardId).toBe(19);
      expect(restored?.hasSubmittedRound).toBe(false);
    });

    it('merges subsequent updates into existing session', () => {
      saveMultiplayerSession({
        roomId: 'TEST99',
        playerId: 'p_host',
        sessionToken: 'tok_secret',
      });

      saveMultiplayerSession({
        roomId: 'TEST99',
        playerId: 'p_host',
        sessionToken: 'tok_secret',
        hasSubmittedRound: true,
      });

      const restored = loadMultiplayerSession();
      expect(restored?.hasSubmittedRound).toBe(true);
      expect(restored?.sessionToken).toBe('tok_secret');
    });

    it('handles corrupted multiplayer session gracefully', () => {
      mockStorage.setItem(MULTIPLAYER_SESSION_KEY, 'bad_json');
      expect(loadMultiplayerSession()).toBeNull();
      expect(mockStorage.getItem(MULTIPLAYER_SESSION_KEY)).toBeNull();
    });

    it('clearMultiplayerSession deletes the stored key', () => {
      mockStorage.setItem(MULTIPLAYER_SESSION_KEY, '{"roomId":"ABC"}');
      clearMultiplayerSession();
      expect(mockStorage.getItem(MULTIPLAYER_SESSION_KEY)).toBeNull();
    });
  });
});
