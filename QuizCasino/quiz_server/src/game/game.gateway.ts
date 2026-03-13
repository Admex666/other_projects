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

@WebSocketGateway({
  cors: {
    origin: '*',
    methods: ['GET', 'POST'],
    credentials: true,
  },
})
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
      const room = this.roomManager.getRoom(roomId);
      if (room) {
        room.removePlayer(client.id);
      }
      this.clientRooms.delete(client.id);
    }
  }

  @SubscribeMessage('auth_register')
  async handleRegister(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { username: string, password: string },
  ) {
    try {
      const user = await this.userManager.register(data.username, data.password);
      client.emit('auth_success', user);
    } catch (e) {
      client.emit('auth_error', { message: e.message || 'Registration failed' });
    }
  }

  @SubscribeMessage('auth_login')
  async handleLogin(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { username: string, password: string },
  ) {
    try {
      const user = await this.userManager.login(data.username, data.password);
      client.emit('auth_success', user);
    } catch (e) {
      client.emit('auth_error', { message: e.message || 'Login failed' });
    }
  }

  @SubscribeMessage('join_queue')
  async handleJoinQueue(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { username: string },
  ) {
    console.log(`[GameGateway] ${client.id} joining queue as ${data.username}`);
    
    const user = await this.userManager.getUser(data.username);
    if (!user) {
      client.emit('error', { message: 'User not found. Please login.' });
      return;
    }

    const player: Player = {
      id: client.id,
      userId: user.username, // Using username as the persistent ID in game logic
      username: user.username,
      stack: 100,
      isEliminated: false,
    };
    this.roomManager.joinQueue(player, client.id);
    client.emit('user_stats', user);
  }

  @SubscribeMessage('leave_queue')
  handleLeaveQueue(@ConnectedSocket() client: Socket) {
    this.roomManager.leaveQueue(client.id);
  }

  @SubscribeMessage('get_stats')
  async handleGetStats(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { username: string },
  ) {
    const user = await this.userManager.getUser(data.username);
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
