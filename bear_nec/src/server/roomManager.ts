import { randomUUID } from 'crypto';
import type { WebSocket } from 'ws';
import type { GameState, GridPosition, GameAction } from '../game/types';
import {
  createInitialGameState,
  executeSelectCards,
  executeConfirmPlacement,
  executeRefillDecision,
  restartGame,
  isValidAction,
  createInitialTurnState,
  type EngineTurnState,
} from '../game/engine';
import { isValidPlacement } from '../game/validation';
import {
  filterStateForPlayer,
  type ServerMessage,
  type SanitizedGameState,
} from './protocol';

export interface RoomPlayer {
  id: string;
  name: string;
  sessionToken: string;
  connected: boolean;
  socket: WebSocket | null;
}

export interface GameRoom {
  roomId: string;
  createdAt: number;
  players: Record<string, RoomPlayer>;
  gameState: GameState | null;
  turnState: EngineTurnState;
  rematchRequests: Set<string>;
  disconnectTimeouts: Map<string, NodeJS.Timeout>;
}

export class RoomManager {
  private rooms = new Map<string, GameRoom>();
  private socketToPlayer = new Map<WebSocket, { roomId: string; playerId: string }>();
  private defaultHostUrl: string;

  constructor(defaultHostUrl = 'http://localhost:3001') {
    this.defaultHostUrl = defaultHostUrl;
  }

  public setBaseUrl(url: string): void {
    this.defaultHostUrl = url;
  }

  public getRoom(roomId: string): GameRoom | undefined {
    return this.rooms.get(roomId.toUpperCase());
  }

  public getAllRooms(): GameRoom[] {
    return Array.from(this.rooms.values());
  }

  private generateRoomCode(): string {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code: string;
    let attempts = 0;
    do {
      code = '';
      for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      attempts++;
      if (attempts > 1000) {
        throw new Error('Could not generate unique room code.');
      }
    } while (this.rooms.has(code));

    return code;
  }

  /**
   * Creates a new game room with host player.
   */
  public createRoom(hostPlayerName: string): {
    roomId: string;
    playerId: string;
    sessionToken: string;
    inviteUrl: string;
  } {
    if (!hostPlayerName || hostPlayerName.trim().length === 0) {
      throw new Error('Host player name cannot be empty.');
    }

    const roomId = this.generateRoomCode();
    const playerId = `p_${randomUUID().substring(0, 8)}`;
    const sessionToken = `tok_${randomUUID()}`;
    const inviteUrl = `${this.defaultHostUrl}/?room=${roomId}`;

    const hostPlayer: RoomPlayer = {
      id: playerId,
      name: hostPlayerName.trim(),
      sessionToken,
      connected: false,
      socket: null,
    };

    const room: GameRoom = {
      roomId,
      createdAt: Date.now(),
      players: { [playerId]: hostPlayer },
      gameState: null,
      turnState: createInitialTurnState(),
      rematchRequests: new Set(),
      disconnectTimeouts: new Map(),
    };

    this.rooms.set(roomId, room);

    return {
      roomId,
      playerId,
      sessionToken,
      inviteUrl,
    };
  }

  /**
   * Joins an existing room as the second player.
   */
  public joinRoom(
    roomId: string,
    playerName: string
  ): {
    roomId: string;
    playerId: string;
    sessionToken: string;
    gameState?: SanitizedGameState;
  } {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);

    if (!room) {
      throw new Error(`Room "${upperRoomId}" not found.`);
    }

    const playerKeys = Object.keys(room.players);
    if (playerKeys.length >= 2) {
      throw new Error(`Room "${upperRoomId}" is already full (maximum 2 players).`);
    }

    if (!playerName || playerName.trim().length === 0) {
      throw new Error('Player name cannot be empty.');
    }

    const playerId = `p_${randomUUID().substring(0, 8)}`;
    const sessionToken = `tok_${randomUUID()}`;

    const guestPlayer: RoomPlayer = {
      id: playerId,
      name: playerName.trim(),
      sessionToken,
      connected: false,
      socket: null,
    };

    room.players[playerId] = guestPlayer;

    // Both players are present: initialize game state!
    const hostPlayer = room.players[playerKeys[0]];
    room.gameState = createInitialGameState(room.roomId, [
      { id: hostPlayer.id, name: hostPlayer.name },
      { id: guestPlayer.id, name: guestPlayer.name },
    ]);
    room.turnState = createInitialTurnState();

    return {
      roomId: upperRoomId,
      playerId,
      sessionToken,
      gameState: filterStateForPlayer(room.gameState!, playerId),
    };
  }

  /**
   * Binds a WebSocket connection to a room player.
   */
  public bindSocket(socket: WebSocket, roomId: string, playerId: string): boolean {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);
    if (!room || !room.players[playerId]) {
      return false;
    }

    const player = room.players[playerId];
    player.socket = socket;
    player.connected = true;
    if (room.gameState?.players[playerId]) {
      room.gameState.players[playerId].connected = true;
    }

    // Clear any disconnect timeout
    const timeout = room.disconnectTimeouts.get(playerId);
    if (timeout) {
      clearTimeout(timeout);
      room.disconnectTimeouts.delete(playerId);
    }

    this.socketToPlayer.set(socket, { roomId: upperRoomId, playerId });
    return true;
  }

  /**
   * Reconnects an existing player using their session token.
   */
  public reconnectPlayer(
    roomId: string,
    playerId: string,
    sessionToken: string,
    socket?: WebSocket
  ): {
    success: boolean;
    state?: SanitizedGameState;
    error?: string;
  } {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);

    if (!room) {
      return { success: false, error: `Room "${upperRoomId}" not found.` };
    }

    const player = room.players[playerId];
    if (!player) {
      return { success: false, error: `Player "${playerId}" not in room.` };
    }

    if (player.sessionToken !== sessionToken) {
      return { success: false, error: 'Invalid session token.' };
    }

    if (socket) {
      this.bindSocket(socket, upperRoomId, playerId);
    } else {
      player.connected = true;
      if (room.gameState?.players[playerId]) {
        room.gameState.players[playerId].connected = true;
      }
      const timeout = room.disconnectTimeouts.get(playerId);
      if (timeout) {
        clearTimeout(timeout);
        room.disconnectTimeouts.delete(playerId);
      }
    }

    // Notify opponent of reconnection
    const opponentId = Object.keys(room.players).find(id => id !== playerId);
    if (opponentId) {
      this.sendToPlayer(upperRoomId, opponentId, {
        type: 'OPPONENT_RECONNECTED',
        playerId,
        playerName: player.name,
      });
    }

    const sanitized = room.gameState ? filterStateForPlayer(room.gameState, playerId) : undefined;
    return {
      success: true,
      state: sanitized,
    };
  }

  /**
   * Handles action submission and validation via the game engine.
   */
  public handleAction(
    roomId: string,
    playerId: string,
    action:
      | GameAction
      | { type: 'SUBMIT_SELECTION'; tableauCardId: number; reserveCardId: number; position?: GridPosition }
      | { type: 'CHOOSE_REFILL_OPTION'; decision: 'keep' | 'discard' }
  ): {
    success: boolean;
    error?: string;
  } {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);

    if (!room || !room.gameState) {
      return { success: false, error: 'Game not found or not active.' };
    }

    if (!room.players[playerId]) {
      return { success: false, error: `Player ${playerId} not in room.` };
    }

    // Convert client protocol message into engine action
    if (action.type === 'SUBMIT_SELECTION') {
      const selectAction: GameAction = {
        type: 'SELECT_CARDS',
        playerId,
        tableauCardId: action.tableauCardId,
        reserveCardId: action.reserveCardId,
      };

      const validation = isValidAction(room.gameState, selectAction);
      if (!validation.valid) {
        return { success: false, error: validation.reason };
      }

      // If position is provided, validate placement coordinate bounds and adjacency
      if (action.position) {
        if (!isValidPlacement(room.gameState.players[playerId].tableau, action.position.row, action.position.col)) {
          return {
            success: false,
            error: `Placement at (${action.position.row}, ${action.position.col}) is not valid.`,
          };
        }
      }

      try {
        const result = executeSelectCards(room.gameState, room.turnState, {
          playerId,
          tableauCardId: action.tableauCardId,
          reserveCardId: action.reserveCardId,
          position: action.position,
        });

        room.gameState = result.state;
        room.turnState = result.turnState;

        if (result.roundResolved) {
          this.broadcastRoundResolved(upperRoomId, result.roundResolved);
        } else {
          this.broadcastState(upperRoomId, 'CARD_SELECTED');
        }

        return { success: true };
      } catch (err: any) {
        return { success: false, error: err.message };
      }
    }

    if (action.type === 'CONFIRM_PLACEMENT') {
      const placementAction: GameAction = {
        type: 'CONFIRM_PLACEMENT',
        playerId,
        position: action.position,
      };

      const validation = isValidAction(room.gameState, placementAction);
      if (!validation.valid) {
        return { success: false, error: validation.reason };
      }

      const result = executeConfirmPlacement(room.gameState, room.turnState, {
        playerId,
        position: action.position,
      });

      room.gameState = result.state;
      room.turnState = result.turnState;

      if (result.roundResolved) {
        this.broadcastRoundResolved(upperRoomId, result.roundResolved);
      } else {
        this.broadcastState(upperRoomId, 'PLACEMENT_CONFIRMED');
      }

      return { success: true };
    }

    if (action.type === 'CHOOSE_REFILL_OPTION' || action.type === 'KEEP_OR_DISCARD_RESERVE') {
      const refillAction: GameAction = {
        type: 'KEEP_OR_DISCARD_RESERVE',
        playerId,
        decision: action.decision,
      };

      const validation = isValidAction(room.gameState, refillAction);
      if (!validation.valid) {
        return { success: false, error: validation.reason };
      }

      const result = executeRefillDecision(room.gameState, room.turnState, {
        playerId,
        decision: action.decision,
      });

      room.gameState = result.state;
      room.turnState = result.turnState;

      this.broadcastState(upperRoomId, 'REFILL_DECIDED');
      return { success: true };
    }

    if (action.type === 'REMATCH') {
      return this.handleRematch(upperRoomId, playerId);
    }

    return { success: false, error: `Unhandled action type: ${(action as any).type}` };
  }

  /**
   * Handles rematch requests. When both players confirm, restarts the game.
   */
  public handleRematch(
    roomId: string,
    playerId: string
  ): {
    success: boolean;
    restarted: boolean;
    error?: string;
  } {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);

    if (!room || !room.gameState) {
      return { success: false, restarted: false, error: 'Room not found.' };
    }

    if (!room.players[playerId]) {
      return { success: false, restarted: false, error: 'Player not in room.' };
    }

    room.rematchRequests.add(playerId);

    const playerIds = Object.keys(room.players);
    if (playerIds.length === 2 && room.rematchRequests.size === 2) {
      // Both confirmed: reset game!
      const restarted = restartGame(room.gameState);
      room.gameState = restarted.state;
      room.turnState = restarted.turnState;
      room.rematchRequests.clear();

      this.broadcastGameStarted(upperRoomId);
      return { success: true, restarted: true };
    }

    // Rematch vote registered, waiting for second player
    return { success: true, restarted: false };
  }

  /**
   * Handles client socket disconnection.
   */
  public handleDisconnect(socket: WebSocket, timeoutMs = 60000): void {
    const binding = this.socketToPlayer.get(socket);
    if (!binding) return;

    this.socketToPlayer.delete(socket);
    const { roomId, playerId } = binding;
    const room = this.rooms.get(roomId);
    if (!room) return;

    const player = room.players[playerId];
    if (player) {
      player.connected = false;
      player.socket = null;
    }

    if (room.gameState?.players[playerId]) {
      room.gameState.players[playerId].connected = false;
    }

    // Notify opponent
    const opponentId = Object.keys(room.players).find(id => id !== playerId);
    if (opponentId) {
      this.sendToPlayer(roomId, opponentId, {
        type: 'OPPONENT_DISCONNECTED',
        playerId,
        playerName: player ? player.name : 'Opponent',
      });
    }

    // Set timeout to handle abandonment
    const existingTimeout = room.disconnectTimeouts.get(playerId);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
    }

    const timeout = setTimeout(() => {
      room.disconnectTimeouts.delete(playerId);
      if (room.gameState && !player?.connected) {
        room.gameState.status = 'abandoned';
        this.broadcastState(roomId, 'PLAYER_ABANDONED');
      }
    }, timeoutMs);

    room.disconnectTimeouts.set(playerId, timeout);
  }

  /**
   * Sends a message to a specific player's socket.
   */
  public sendToPlayer(roomId: string, playerId: string, message: ServerMessage): boolean {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);
    if (!room) return false;

    const player = room.players[playerId];
    if (!player || !player.socket || player.socket.readyState !== 1) {
      return false; // Ready state 1 is OPEN
    }

    try {
      player.socket.send(JSON.stringify(message));
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Broadcasts sanitized state updates to all connected players in the room.
   */
  public broadcastState(roomId: string, reason?: string): void {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);
    if (!room || !room.gameState) return;

    for (const pid of Object.keys(room.players)) {
      const sanitized = filterStateForPlayer(room.gameState, pid);
      this.sendToPlayer(upperRoomId, pid, {
        type: 'STATE_UPDATE',
        roomId: upperRoomId,
        state: sanitized,
        reason,
      });
    }
  }

  /**
   * Broadcasts GAME_STARTED with sanitized state to both players.
   */
  public broadcastGameStarted(roomId: string): void {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);
    if (!room || !room.gameState) return;

    for (const pid of Object.keys(room.players)) {
      const sanitized = filterStateForPlayer(room.gameState, pid);
      this.sendToPlayer(upperRoomId, pid, {
        type: 'GAME_STARTED',
        roomId: upperRoomId,
        state: sanitized,
      });
    }
  }

  /**
   * Broadcasts ROUND_RESOLVED to all connected players with each player's sanitized state.
   */
  public broadcastRoundResolved(
    roomId: string,
    roundData: { round: number; roundScores: Record<string, number>; beeWinners: string[] }
  ): void {
    const upperRoomId = roomId.trim().toUpperCase();
    const room = this.rooms.get(upperRoomId);
    if (!room || !room.gameState) return;

    for (const pid of Object.keys(room.players)) {
      const sanitized = filterStateForPlayer(room.gameState, pid);
      this.sendToPlayer(upperRoomId, pid, {
        type: 'ROUND_RESOLVED',
        roomId: upperRoomId,
        round: roundData.round,
        roundScores: roundData.roundScores,
        beeWinners: roundData.beeWinners,
        state: sanitized,
      });
    }
  }
}
