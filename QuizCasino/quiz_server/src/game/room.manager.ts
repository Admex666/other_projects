import { Injectable } from '@nestjs/common';
import { GameLogic } from './game.logic';
import { Player } from './game.types';
import { UserManager } from './user.manager';

@Injectable()
export class RoomManager {
  private rooms: Map<string, GameLogic> = new Map();
  private matchmakingQueue: { player: Player, socketId: string }[] = [];
  
  // Room ID generator
  private nextRoomId = 1;
  private queueStartTime: number | null = null;

  constructor(private readonly userManager: UserManager) {
    // Check queue every second
    setInterval(() => this.processQueue(), 1000);
  }

  joinQueue(player: Player, socketId: string) {
    if (!this.matchmakingQueue.find(p => p.player.id === player.id)) {
      this.matchmakingQueue.push({ player, socketId });
      console.log(`[RoomManager] Player ${player.username} added to queue. Queue size: ${this.matchmakingQueue.length}`);
      if (this.matchmakingQueue.length === 1) {
        this.queueStartTime = Date.now();
      }
    }
  }

  leaveQueue(playerId: string) {
    this.matchmakingQueue = this.matchmakingQueue.filter(p => p.player.id !== playerId);
    if (this.matchmakingQueue.length === 0) {
      this.queueStartTime = null;
    }
  }

  private processQueue() {
    if (this.matchmakingQueue.length === 0) return;

    // Check if we should start a match: either we have 4+ players, or 5 seconds have passed
    const now = Date.now();
    const shouldStart = this.matchmakingQueue.length >= 4 || (this.queueStartTime && (now - this.queueStartTime) >= 5000);

    if (!shouldStart) {
      if (this.matchmakingQueue.length > 0) {
        console.log(`[RoomManager] Waiting for more players or timeout... (${this.matchmakingQueue.length}/4)`);
      }
      return;
    }

    console.log(`[RoomManager] Starting match for ${this.matchmakingQueue.length} players...`);

    while (this.matchmakingQueue.length > 0 && shouldStart) {
      // If we don't have enough players and we decided to start (timeout), we still just take whoever is there
      const roomPlayers = this.matchmakingQueue.splice(0, 4);
      
      // Reset timer if there is someone left, or clear it
      if (this.matchmakingQueue.length > 0) {
        this.queueStartTime = Date.now();
      } else {
        this.queueStartTime = null;
      }
      
      const roomId = `room_${this.nextRoomId++}`;
      
      const logic = new GameLogic(roomId, {
        onStateUpdate: (state) => this.onRoomStateUpdate(roomId, state),
        onMatchEnded: (results) => this.onRoomMatchEnded(roomId, results),
        onTick: (time) => this.onRoomTick(roomId, time),
      });

      // Add real players and join socket room
      for (const p of roomPlayers) {
        logic.addPlayer(p.player);
        if (this.gatewayJoinRoom) {
          this.gatewayJoinRoom(p.socketId, roomId);
        }
      }

      // Backfill with bots
      let botIndex = 1;
      while (!logic.isFull) {
        logic.addPlayer({
          id: `bot_${roomId}_${botIndex}`,
          userId: `bot_persistent_${botIndex}`,
          username: `Bot ${['Anna', 'Ben', 'Kai', 'Zoe'][botIndex - 1]}`,
          stack: 100,
          isEliminated: false,
        });
        botIndex++;
      }

      this.rooms.set(roomId, logic);
      
      // Start match asynchronously
      logic.startMatch();
    }
  }

  getRoom(roomId: string): GameLogic | undefined {
    return this.rooms.get(roomId);
  }

  // --- Callbacks bound from the Gateway later ---

  public gatewayEmitToRoom?: (roomId: string, event: string, payload: any) => void;
  public gatewayEmitToUser?: (socketId: string, event: string, payload: any) => void;
  public gatewayJoinRoom?: (socketId: string, roomId: string) => void;

  private onRoomStateUpdate(roomId: string, state: any) {
    if (this.gatewayEmitToRoom) {
      this.gatewayEmitToRoom(roomId, 'state_update', state);
    }
  }

  private onRoomTick(roomId: string, time: number) {
    if (this.gatewayEmitToRoom) {
      this.gatewayEmitToRoom(roomId, 'tick', time);
    }
  }

  private async onRoomMatchEnded(roomId: string, results: Player[]) {
    console.log(`[RoomManager] onRoomMatchEnded for ${roomId}. Results received for ${results.length} players.`);
    if (this.gatewayEmitToRoom) {
      this.gatewayEmitToRoom(roomId, 'match_ended', results);
      console.log(`[RoomManager] match_ended event emitted to room ${roomId}.`);
      
      // Update persistent stats for real players
      for (const p of results) {
        if (p.id.startsWith('bot_')) continue;
        const won = results[0].id === p.id;
        const coinsChange = p.stack - 100; // Net profit/loss
        console.log(`[RoomManager] Updating stats for user ${p.username}: Won=${won}, CoinsChange=${coinsChange}`);
        await this.userManager.updateStats(p.username, won, coinsChange);
        
        // Notify the specific player of their new totals
        const stats = await this.userManager.getUser(p.username);
        if (stats && this.gatewayEmitToUser) {
          this.gatewayEmitToUser(p.id, 'user_stats', stats);
        }
      }

      // Clean up room after 10s
      setTimeout(() => {
        console.log(`[RoomManager] Deleting room ${roomId} (cleanup).`);
        this.rooms.delete(roomId);
      }, 10000);
    } else {
      console.error(`[RoomManager] gatewayEmitToRoom is NOT set! Cannot emit match_ended.`);
    }
  }
}
