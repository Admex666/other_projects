import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { OnModuleInit } from '@nestjs/common';
import { Server, Socket } from 'socket.io';
import { RoomManager } from './room.manager';
import { UserManager } from './user.manager';
import { GuildService } from './guild.service';
import { Player } from './game.types';

@WebSocketGateway({
  cors: {
    origin: true,
    methods: ['GET', 'POST'],
    credentials: true,
  },
})
export class GameGateway implements OnGatewayConnection, OnGatewayDisconnect, OnModuleInit {
  @WebSocketServer()
  server: Server;

  onModuleInit() {
    console.log('GameGateway initialized and listening for connections');
  }

  // Map socketId -> roomId
  private clientRooms: Map<string, string> = new Map();

  constructor(
    private readonly roomManager: RoomManager,
    private readonly userManager: UserManager,
    private readonly guildService: GuildService,
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
    const activeRoomId = data.roomId === 'current' ? this.clientRooms.get(client.id) : data.roomId;
    const room = this.roomManager.getRoom(activeRoomId);
    if (room) {
      room.placeBet(client.id, data.amount);
    }
  }

  @SubscribeMessage('get_leaderboard')
  async handleGetLeaderboard(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { league: string },
  ) {
    const leaderboard = await this.userManager.getLeaderboard(data.league);
    client.emit('leaderboard_update', { league: data.league, players: leaderboard });
  }

  @SubscribeMessage('create_guild')
  async handleCreateGuild(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { username: string, name: string, tag: string },
  ) {
    try {
      const guild = await this.guildService.createGuild(data.username, data.name, data.tag);
      client.emit('guild_update', guild);
      // Also update user's own stats to reflect guild change
      const user = await this.userManager.getUser(data.username);
      client.emit('user_stats', user);
    } catch (e) {
      client.emit('error', { message: e.message || 'Guild creation failed' });
    }
  }

  @SubscribeMessage('get_guild')
  async handleGetGuild(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { tag: string },
  ) {
    const guild = await this.guildService.getGuildByTag(data.tag);
    if (guild) {
      client.emit('guild_update', guild);
    }
  }

  @SubscribeMessage('select_answer')
  handleSelectAnswer(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { roomId: string, index: number },
  ) {
    const activeRoomId = data.roomId === 'current' ? this.clientRooms.get(client.id) : data.roomId;
    const room = this.roomManager.getRoom(activeRoomId);
    if (room) {
      room.selectAnswer(client.id, data.index);
    }
  }
}
