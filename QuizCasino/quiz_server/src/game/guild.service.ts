import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { Guild } from './guild.schema';
import { User } from './user.schema';

@Injectable()
export class GuildService {
  private readonly logger = new Logger(GuildService.name);

  constructor(
    @InjectModel(Guild.name) private guildModel: Model<Guild>,
    @InjectModel(User.name) private userModel: Model<User>,
  ) {}

  async createGuild(leaderUsername: string, name: string, tag: string) {
    // Check if name or tag taken
    const existing = await this.guildModel.findOne({ $or: [{ name }, { tag }] });
    if (existing) throw new Error('Guild name or tag already exists');

    const guild = new this.guildModel({
      name,
      tag,
      leaderUsername,
      shares: { [leaderUsername]: 1000 },
      totalShares: 1000,
    });

    await guild.save();
    
    // Update user to link to this guild
    await this.userModel.findOneAndUpdate({ username: leaderUsername }, { guildTag: tag });

    return guild;
  }

  async getGuildByTag(tag: string) {
    return this.guildModel.findOne({ tag }).exec();
  }

  async getUserGuild(username: string) {
    const user = await this.userModel.findOne({ username });
    if (!user || !user.guildTag) return null;
    return this.getGuildByTag(user.guildTag);
  }

  /**
   * Collects tax from match rewards and adds to guild vault.
   */
  async processTax(username: string, baseReward: number): Promise<number> {
    const user = await this.userModel.findOne({ username });
    if (!user || !user.guildTag) return baseReward;

    const guild = await this.getGuildByTag(user.guildTag);
    if (!guild) return baseReward;

    const taxAmount = Math.floor(baseReward * (guild.taxRate / 100));
    const netReward = baseReward - taxAmount;

    await this.guildModel.findOneAndUpdate(
      { tag: user.guildTag },
      { $inc: { vaultGold: taxAmount } }
    ).exec();

    this.logger.log(`Taxed ${taxAmount} gold from ${username} for guild ${guild.tag}`);
    return netReward;
  }

  /**
   * Distributes dividends from vaultGold to all shareholders.
   * Normally run weekly alongside resets.
   */
  async distributeDividends(guildTag: string) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild || guild.vaultGold <= 0) return;

    const totalDividends = guild.vaultGold;
    const shares: Map<string, number> = (guild as any).shares;

    for (const [username, shareCount] of shares.entries()) {
      const sharePercentage = shareCount / guild.totalShares;
      const payout = Math.floor(totalDividends * sharePercentage);

      if (payout > 0) {
        await this.userModel.findOneAndUpdate(
          { username },
          { $inc: { gold: payout } }
        ).exec();
        this.logger.log(`Distributed ${payout} gold dividend to ${username}`);
      }
    }

    // Reset vault
    await this.guildModel.findOneAndUpdate({ tag: guildTag }, { $set: { vaultGold: 0 } }).exec();
  }
}
