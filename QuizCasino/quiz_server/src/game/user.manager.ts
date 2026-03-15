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
  hiddenElo: number;
  league: string;
  division: string;
  placementMatches: number;
  weeklyTotal: number;
  guildTag: string;
  inventory: string[];
  equippedSkin: string;
  equippedTrail: string;
  equippedAnimation: string;
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
      hiddenElo: user.hiddenElo,
      league: user.league,
      division: user.division || 'III',
      placementMatches: user.placementMatches,
      weeklyTotal: this.leagueService.calculateWeeklyTotal(user.weeklyScores),
      guildTag: user.guildTag,
      inventory: user.inventory || [],
      equippedSkin: user.equippedSkin || 'default',
      equippedTrail: user.equippedTrail || 'none',
      equippedAnimation: user.equippedAnimation || 'none',
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

  async updateStats(username: string, won: boolean, chipsRemaining: number, rank: number, matchResults: any[]) {
    // 1. Gold rewards: Rank multiplier * Remaining Chips
    const multipliers = [0, 3, 2, 1, 0.5];
    const rankMultiplier = multipliers[Math.min(rank, 4)] || 0; // Caps at 4th for multiplier purposes
    if (rank > 4) multipliers[4]; // Fallback if we want some tiny reward for 5th+
    
    const baseGoldReward = Math.floor(chipsRemaining * rankMultiplier);
    const goldReward = await this.guildService.processTax(username, baseGoldReward);

    // 2. Advanced Match-Wide ELO Calculation (You vs every other player)
    const user = await this.userModel.findOne({ username });
    if (!user) return;

    const K = 32;
    const N = matchResults.length;
    let totalEloChange = 0;
    let totalHiddenEloChange = 0;

    for (let i = 0; i < matchResults.length; i++) {
      const opponent = matchResults[i];
      if (opponent.username === username) continue;

      const opponentRank = i + 1; // Index in the sorted results array defines their rank

      // Public ELO calc
      const Ea = 1 / (1 + Math.pow(10, (opponent.elo - user.elo) / 400));
      const Sa = rank < opponentRank ? 1 : 0; // Better rank = win
      totalEloChange += (K / (N - 1)) * (Sa - Ea);

      // Hidden ELO calc
      const EaH = 1 / (1 + Math.pow(10, (opponent.hiddenElo - user.hiddenElo) / 400));
      totalHiddenEloChange += (K / (N - 1)) * (Sa - EaH);
    }

    const newElo = Math.max(0, user.elo + Math.round(totalEloChange));
    const newHiddenElo = user.hiddenElo + Math.round(totalHiddenEloChange);

    // Instant Promotion / League Shield Logic
    const currentLeague = user.league;
    const { league: nextLeague, division: nextDivision } = this.getLeagueAndDivision(newElo);
    
    const leagueOrder = ['unranked', 'bronze', 'silver', 'gold', 'platinum', 'diamond'];
    const currentIdx = leagueOrder.indexOf(currentLeague);
    const nextIdx = leagueOrder.indexOf(nextLeague);

    let finalElo = newElo;
    let finalLeague = currentLeague;
    let finalDivision = user.division || 'III';

    // 1. Placement Phase
    if (currentLeague === 'unranked') {
      finalLeague = nextLeague;
      finalDivision = nextDivision;
    } 
    // 2. Promotion (Instant)
    else if (nextIdx > currentIdx || (nextIdx === currentIdx && this.isDivisionBetter(nextDivision, finalDivision))) {
      finalLeague = nextLeague;
      finalDivision = nextDivision;
    }
    // 3. League Shield (Don't drop below current league floor during season)
    else if (nextIdx < currentIdx) {
       const floorElo = this.getLeagueFloor(currentLeague);
       finalElo = Math.max(finalElo, floorElo);
       finalLeague = currentLeague; 
       // Division might drop to III within the league, but not league itself
       finalDivision = this.getLeagueAndDivision(finalElo).division;
    } else {
       // Regular division movement (down within the same league is allowed)
       finalLeague = nextLeague;
       finalDivision = nextDivision;
    }

    await this.userModel.findOneAndUpdate(
      { username },
      {
        $set: {
          elo: finalElo,
          hiddenElo: newHiddenElo,
          league: finalLeague,
          division: finalDivision,
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

  private getLeagueAndDivision(elo: number): { league: string, division: string } {
    if (elo >= 3000) return { league: 'diamond', division: 'I' };
    
    if (elo >= 2500) {
      if (elo >= 2833) return { league: 'platinum', division: 'I' };
      if (elo >= 2666) return { league: 'platinum', division: 'II' };
      return { league: 'platinum', division: 'III' };
    }
    if (elo >= 2000) {
      if (elo >= 2333) return { league: 'gold', division: 'I' };
      if (elo >= 2166) return { league: 'gold', division: 'II' };
      return { league: 'gold', division: 'III' };
    }
    if (elo >= 1500) {
      if (elo >= 1833) return { league: 'silver', division: 'I' };
      if (elo >= 1666) return { league: 'silver', division: 'II' };
      return { league: 'silver', division: 'III' };
    }
    
    if (elo >= 1000) return { league: 'bronze', division: 'I' };
    if (elo >= 500) return { league: 'bronze', division: 'II' };
    return { league: 'bronze', division: 'III' };
  }

  private getLeagueFloor(league: string): number {
    const floors: Record<string, number> = {
      'bronze': 0,
      'silver': 1500,
      'gold': 2000,
      'platinum': 2500,
      'diamond': 3000
    };
    return floors[league] || 0;
  }

  private isDivisionBetter(next: string, current: string): boolean {
    const order = ['III', 'II', 'I'];
    return order.indexOf(next) > order.indexOf(current);
  }

  async getLeaderboard(league: string): Promise<UserStats[]> {
    const users = await this.userModel.find({ league }).exec();
    const stats = users.map(u => this.mapToStats(u));
    // Sort by weeklyTotal descending
    return stats.sort((a, b) => b.weeklyTotal - a.weeklyTotal);
  }
}
