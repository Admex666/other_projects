import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { GameGateway } from './game.gateway';
import { RoomManager } from './room.manager';
import { UserManager } from './user.manager';
import { User, UserSchema } from './user.schema';

@Module({
  imports: [
    MongooseModule.forFeature([{ name: User.name, schema: UserSchema }])
  ],
  providers: [GameGateway, RoomManager, UserManager],
  exports: [UserManager],
})
export class GameModule {}
