import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { User } from './user.schema';

@Injectable()
export class LeagueService {
  private readonly logger = new Logger(LeagueService.name);

  constructor(@InjectModel(User.name) private userModel: Model<User>) {}

  /**
   * Processes a match result to update weekly scores and handle seeding.
   */
  async processMatchResult(username: string, chipsRemaining: number, rank: number) {
    const user = await this.userModel.findOne({ username });
    if (!user) return;

    // 1. Calculate Match Score: Chips * Rank Multiplier
    // Ranks: 1st=x3, 2nd=x2, 3rd=x1, 4th=x0.5
    const multipliers = [0, 3, 2, 1, 0.5];
    const rankMultiplier = multipliers[rank] || 0;
    const matchScore = Math.floor(chipsRemaining * rankMultiplier);

    // 2. Add to weekly scores
    const weeklyScores = [...(user.weeklyScores || []), matchScore];

    // 3. Handle Placement Matches (Seeding)
    let league = user.league;
    let placementMatches = (user.placementMatches || 0) + 1;

    if (league === 'unranked' && placementMatches >= 5) {
      // Seeding logic based on current ELO (which baseline is 1500)
      if (user.elo >= 1550) {
        league = 'silver';
      } else {
        league = 'bronze';
      }
      this.logger.log(`User ${username} seeded into ${league} league.`);
    }

    await this.userModel.findOneAndUpdate(
      { username },
      {
        $set: {
          weeklyScores,
          league,
          placementMatches,
        }
      }
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
   * Main Weekly Reset logic (usually run by a Cron job).
   * Promotes top 10% and demotes bottom 20%.
   */
  async performWeeklyReset() {
    this.logger.log('Starting weekly league reset...');
    const leagues = ['bronze', 'silver', 'gold', 'platinum', 'diamond'];

    for (const leagueName of leagues) {
      const users = await this.userModel.find({ league: leagueName }).exec();
      if (users.length === 0) continue;

      // Calculate totals for all users in this league
      const userRankings = users.map(u => ({
        username: u.username,
        totalScore: this.calculateWeeklyTotal(u.weeklyScores),
      }));

      // Sort by total score descending
      userRankings.sort((a, b) => b.totalScore - a.totalScore);

      const totalCount = userRankings.length;
      const topCount = Math.max(1, Math.floor(totalCount * 0.1)); // Top 10%
      const bottomCount = Math.max(0, Math.floor(totalCount * 0.2)); // Bottom 20%

      for (let i = 0; i < totalCount; i++) {
        const ranking = userRankings[i];
        let nextLeague = leagueName;
        let eloAdjustment = 0;

        if (i < topCount && leagueName !== 'diamond') {
          // Promote
          const currentIndex = leagues.indexOf(leagueName);
          nextLeague = leagues[currentIndex + 1];
          eloAdjustment = 50; // Bonus for promotion
        } else if (i >= totalCount - bottomCount && leagueName !== 'bronze') {
          // Demote
          const currentIndex = leagues.indexOf(leagueName);
          nextLeague = leagues[currentIndex - 1];
          eloAdjustment = -50; 
        }

        // Soft Reset: Reset ELO to the bottom of the (next) league if promoted/demoted?
        // Actually the concept says: reset to floor of target league.
        // For simplicity now, we just clear weekly scores and set the league.
        
        await this.userModel.findOneAndUpdate(
          { username: ranking.username },
          {
            $set: {
              league: nextLeague,
              weeklyScores: [],
              lastWeeklyUpdate: new Date(),
            },
            // Note: In V4, public ELO resets to floor. For now we just keep it simple.
          }
        ).exec();
      }
    }
    this.logger.log('Weekly league reset completed.');
  }
}
