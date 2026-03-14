import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { GameGateway } from './game.gateway';
import { RoomManager } from './room.manager';
import { UserManager } from './user.manager';
import { User, UserSchema } from './user.schema';
import { Match, MatchSchema } from './match.schema';
import { LeagueService } from './league.service';
import { Guild, GuildSchema } from './guild.schema';
import { GuildService } from './guild.service';
import { ShopService } from './shop.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: User.name, schema: UserSchema },
      { name: Match.name, schema: MatchSchema },
      { name: Guild.name, schema: GuildSchema },
    ]),
  ],
  providers: [GameGateway, RoomManager, UserManager, LeagueService, GuildService, ShopService],
  exports: [UserManager, LeagueService, GuildService, ShopService],
})
export class GameModule {}
