import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { User } from './user.schema';
import { LeagueService } from './league.service';
import { GuildService } from './guild.service';
import * as bcrypt from 'bcrypt';

export interface UserStats {
  username: string;
  totalCoins: number; // Legacy/Chips
  gold: number;
  diamonds: number;
  gamesPlayed: number;
  victories: number;
  elo: number;
  league: string;
  placementMatches: number;
  weeklyTotal: number;
  guildTag: string;
  inventory: string[];
  equippedSkin: string;
  equippedTrail: string;
}

@Injectable()
export class UserManager {
  private readonly saltRounds = 10;

  constructor(
    @InjectModel(User.name) private userModel: Model<User>,
    private readonly leagueService: LeagueService,
    private readonly guildService: GuildService,
  ) {}

  private mapToStats(user: User): UserStats {
    return {
      username: user.username,
      totalCoins: user.coins,
      gold: user.gold,
      diamonds: user.diamonds,
      gamesPlayed: user.matchesPlayed,
      victories: user.matchesWon,
      elo: user.elo,
      league: user.league,
      placementMatches: user.placementMatches,
      weeklyTotal: this.leagueService.calculateWeeklyTotal(user.weeklyScores),
      guildTag: user.guildTag,
      inventory: user.inventory || [],
      equippedSkin: user.equippedSkin || 'default',
      equippedTrail: user.equippedTrail || 'none',
    };
  }

  async register(username: string, password: string): Promise<UserStats> {
    const existing = await this.userModel.findOne({ username }).exec();
    if (existing) {
      throw new ConflictException('Username already taken');
    }

    const hashedPassword = await bcrypt.hash(password, this.saltRounds);
    const user = await this.userModel.create({
      username,
      userId: username,
      password: hashedPassword,
      coins: 100, // Matching V4 chips
      gold: 500,
      diamonds: 0,
      matchesPlayed: 0,
      matchesWon: 0,
      elo: 1500,
      hiddenElo: 1500,
    });

    return this.mapToStats(user);
  }

  async login(username: string, password: string): Promise<UserStats> {
    const user = await this.userModel.findOne({ username }).exec();
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      throw new UnauthorizedException('Invalid credentials');
    }

    return this.mapToStats(user);
  }

  async getUser(username: string): Promise<UserStats | undefined> {
    const user = await this.userModel.findOne({ username }).exec();
    return user ? this.mapToStats(user) : undefined;
  }

  // Fallback for bots or legacy (if needed)
  async getOrCreateUser(username: string): Promise<UserStats> {
    let user = await this.userModel.findOne({ username }).exec();
    if (!user) {
      // For bots, we use a fixed password
      const hashedPassword = await bcrypt.hash('bot_password', this.saltRounds);
      user = await this.userModel.create({
        username,
        userId: username,
        password: hashedPassword,
        coins: 1000,
        matchesPlayed: 0,
        matchesWon: 0,
      });
    }
    return this.mapToStats(user);
  }

  async updateStats(username: string, won: boolean, chipsRemaining: number, rank: number) {
    // Gold rewards: Rank multiplier * Remaining Chips
    // Ranks: 1st=x3, 2nd=x2, 3rd=x1, 4th=x0.5
    const multipliers = [0, 3, 2, 1, 0.5];
    const rankMultiplier = multipliers[rank] || 0;
    const baseGoldReward = Math.floor(chipsRemaining * rankMultiplier);

    // Process Guild Tax
    const goldReward = await this.guildService.processTax(username, baseGoldReward);

    // ELO (Baseline 1500, Floor 0)
    let eloChange = won ? 25 : (rank <= 2 ? 10 : -15);

    const user = await this.userModel.findOne({ username });
    if (user) {
      const newElo = Math.max(0, user.elo + eloChange);
      const newHiddenElo = user.hiddenElo + eloChange; // Hidden ELO can be negative for dev tracking if you want, but public remains 0+

      await this.userModel.findOneAndUpdate(
        { username },
        {
          $set: {
            elo: newElo,
            hiddenElo: newHiddenElo,
          },
          $inc: {
            gold: goldReward,
            matchesPlayed: 1,
            matchesWon: won ? 1 : 0,
          },
        },
      ).exec();

      // Update League/Placement stats
      await this.leagueService.processMatchResult(username, chipsRemaining, rank);
    }
  }

  async getLeaderboard(league: string): Promise<UserStats[]> {
    const users = await this.userModel.find({ league }).exec();
    const stats = users.map(u => this.mapToStats(u));
    // Sort by weeklyTotal descending
    return stats.sort((a, b) => b.weeklyTotal - a.weeklyTotal);
  }
}
