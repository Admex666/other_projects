import { Module } from '@nestjs/common';
import { GameGateway } from './game.gateway';
import { RoomManager } from './room.manager';
import { UserManager } from './user.manager';

@Module({
  providers: [GameGateway, RoomManager, UserManager],
})
export class GameModule {}
