import { Module, Get, Controller } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { MongooseModule } from '@nestjs/mongoose';
import { GameModule } from './game/game.module';
import axios from 'axios';

@Controller()
export class HealthController {
  @Get()
  health() {
    return { status: 'ok', timestamp: new Date().toISOString() };
  }

  @Get('version')
  async getVersion() {
    try {
      // Automatikusan lekérjük a legfrissebb release-t a GitHubról
      const response = await axios.get('https://api.github.com/repos/Admex666/other_projects/releases/latest');
      const latestRelease = response.data;
      
      // Megkeressük az APK fájlt az assetek között
      const apkAsset = latestRelease.assets.find(asset => asset.name.endsWith('.apk'));
      
      return {
        version: latestRelease.tag_name.replace('v', ''), // Pl: 'v1.0.1' -> '1.0.1'
        url: apkAsset ? apkAsset.browser_download_url : latestRelease.html_url,
        mandatory: false,
      };
    } catch (error) {
      // Fallback ha a GitHub API nem elérhető
      return {
        version: '1.0.1',
        url: 'https://github.com/Admex666/other_projects/releases/latest',
        mandatory: false,
      };
    }
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
