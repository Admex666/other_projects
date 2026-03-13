import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { RoomManager } from './room.manager';
import { UserManager } from './user.manager';
import { Player } from './game.types';

@WebSocketGateway({ cors: true })
export class GameGateway implements OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server;

  // Map socketId -> roomId
  private clientRooms: Map<string, string> = new Map();

  constructor(
    private readonly roomManager: RoomManager,
    private readonly userManager: UserManager,
  ) {}

  afterInit() {
    this.roomManager.gatewayEmitToRoom = (roomId, event, payload) => {
      this.server.to(roomId).emit(event, payload);
    };

    this.roomManager.gatewayEmitToUser = (socketId, event, payload) => {
      this.server.to(socketId).emit(event, payload);
    };

    this.roomManager.gatewayJoinRoom = (socketId, roomId) => {
      const socket = this.server.sockets.sockets.get(socketId);
      if (socket) {
        socket.join(roomId);
        this.clientRooms.set(socketId, roomId);
        socket.emit('match_found', { roomId });
      }
    };
  }

  handleConnection(client: Socket) {
    console.log(`[GameGateway] Client connected: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    console.log(`[GameGateway] Client disconnected: ${client.id}`);
    const roomId = this.clientRooms.get(client.id);
    this.roomManager.leaveQueue(client.id);

    if (roomId) {
      // Could notify room logic to handle disconnect (e.g. mark eliminated)
      const room = this.roomManager.getRoom(roomId);
      if (room) {
        room.removePlayer(client.id);
      }
      this.clientRooms.delete(client.id);
    }
  }

  @SubscribeMessage('join_queue')
  async handleJoinQueue(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { username: string, userId: string },
  ) {
    console.log(`[GameGateway] ${client.id} joined queue as ${data.username} (UID: ${data.userId})`);
    
    // Google Play / User Management base
    const user = await this.userManager.getOrCreateUser(data.userId || client.id, data.username);
    
    const player: Player = {
      id: client.id,
      userId: user.userId,
      username: user.username,
      stack: 100, // Starting stack for the match
      isEliminated: false,
    };
    this.roomManager.joinQueue(player, client.id);

    // Send user stats back immediately
    client.emit('user_stats', user);
  }

  @SubscribeMessage('get_stats')
  async handleGetStats(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { userId: string },
  ) {
    const user = await this.userManager.getUser(data.userId);
    if (user) {
      client.emit('user_stats', user);
    }
  }

  @SubscribeMessage('place_bet')
  handlePlaceBet(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { roomId: string, amount: number },
  ) {
    const room = this.roomManager.getRoom(data.roomId);
    if (room) {
      room.placeBet(client.id, data.amount);
    }
  }

  @SubscribeMessage('select_answer')
  handleSelectAnswer(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { roomId: string, index: number },
  ) {
    const room = this.roomManager.getRoom(data.roomId);
    if (room) {
      room.selectAnswer(client.id, data.index);
    }
  }
}
