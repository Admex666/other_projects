import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { User } from './user.schema';

@Injectable()
export class LeagueService {
  private readonly logger = new Logger(LeagueService.name);

  constructor(@InjectModel(User.name) private userModel: Model<User>) {}

  /**
   * Processes a match result to update weekly scores.
   * Rank migration is now handled instantly in UserManager.
   */
  async processMatchResult(username: string, chipsRemaining: number, rank: number) {
    const user = await this.userModel.findOne({ username });
    if (!user) return;

    // 1. Calculate Match Score: Chips * Rank Multiplier (For Leaderboard)
    const multipliers = [0, 3, 2, 1, 0.5];
    const rankMultiplier = multipliers[rank] || 0;
    const matchScore = Math.floor(chipsRemaining * rankMultiplier);

    // 2. Add to weekly scores
    const weeklyScores = [...(user.weeklyScores || []), matchScore];

    await this.userModel.findOneAndUpdate(
      { username },
      { $set: { weeklyScores } }
    ).exec();
  }

  /**
   * Returns the current weekly score for a user (Sum of Top 5 matches).
   */
  calculateWeeklyTotal(weeklyScores: number[]): number {
    if (!weeklyScores || weeklyScores.length === 0) return 0;
    const sorted = [...weeklyScores].sort((a, b) => b - a);
    const top5 = sorted.slice(0, 5);
    return top5.reduce((sum, score) => sum + score, 0);
  }

  /**
   * Weekly Reset: Clears scores and distributes rewards based on ranking.
   * Promotions/Demotions are now INSTANT during gameplay.
   */
  async performWeeklyReset() {
    this.logger.log('Starting weekly rewards distribution...');
    const leagues = ['bronze', 'silver', 'gold', 'platinum', 'diamond'];

    for (const leagueName of leagues) {
      const users = await this.userModel.find({ league: leagueName }).exec();
      if (users.length === 0) continue;

      const userRankings = users.map(u => ({
        username: u.username,
        totalScore: this.calculateWeeklyTotal(u.weeklyScores),
      }));

      userRankings.sort((a, b) => b.totalScore - a.totalScore);

      // Reward Top 3 players in each league with Diamonds
      const rewardGems = [500, 250, 100];
      
      for (let i = 0; i < Math.min(3, userRankings.length); i++) {
        if (userRankings[i].totalScore > 0) {
          await this.userModel.findOneAndUpdate(
            { username: userRankings[i].username },
            { $inc: { diamonds: rewardGems[i] } }
          ).exec();
          this.logger.log(`Rewarded ${userRankings[i].username} with ${rewardGems[i]} gems for ${i + 1}th place in ${leagueName}`);
        }
      }

      // Clear all weekly scores for this league
      await this.userModel.updateMany(
        { league: leagueName },
        { 
          $set: { 
            weeklyScores: [],
            lastWeeklyUpdate: new Date() 
          } 
        }
      ).exec();
    }
    this.logger.log('Weekly rewards and reset completed.');
  }

  /**
   * Seasonal Reset (Monthly): Resets players to their division floor.
   */
  async performSeasonalReset() {
    this.logger.log('Starting monthly seasonal ELO reset...');
    const users = await this.userModel.find({ league: { $ne: 'unranked' } }).exec();

    for (const user of users) {
      if (!user.elo) continue;

      // Soft reset to the floor of their current division
      const floorElo = this.calculateDivisionFloor(user.elo);
      
      await this.userModel.findOneAndUpdate(
        { username: user.username },
        { $set: { elo: floorElo } }
      ).exec();
    }
    this.logger.log('Seasonal reset completed.');
  }

  private calculateDivisionFloor(elo: number): number {
    if (elo >= 3000) return 3000; // Diamond floor
    
    // Main league floors
    const floors = [0, 500, 1000, 1500, 1666, 1833, 2000, 2166, 2333, 2500, 2666, 2833];
    
    let currentFloor = 0;
    for (const f of floors) {
      if (elo >= f) currentFloor = f;
      else break;
    }
    return currentFloor;
  }
}
