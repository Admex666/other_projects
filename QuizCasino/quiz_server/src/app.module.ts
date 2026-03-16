import { Module, Get, Controller } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { MongooseModule } from '@nestjs/mongoose';
import { GameModule } from './game/game.module';

@Controller()
export class HealthController {
  @Get()
  health() {
    return { status: 'ok', timestamp: new Date().toISOString() };
  }

  @Get('version')
  getVersion() {
    return {
      version: '1.0.1',
      url: 'https://github.com/Admex666/other_projects/releases/latest', // Példa link, ide jöhet az APK direkt linkje is
      mandatory: false,
    };
  }
}

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    MongooseModule.forRoot(process.env.MONGODB_URI || 'mongodb://localhost:27017/quizcasino'),
    GameModule
  ],
  controllers: [HealthController],
  providers: [],
})
export class AppModule {}
