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
      isPublic: true,
      pendingRequests: [],
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

  /**
   * Returns a list of public guilds.
   */
  async searchGuilds(query?: string) {
    const filter: any = { isPublic: true };
    if (query) {
      filter.$or = [
        { name: { $regex: query, $options: 'i' } },
        { tag: { $regex: query, $options: 'i' } },
      ];
    }
    return this.guildModel.find(filter).limit(20).exec();
  }

  /**
   * User requests to join a guild.
   */
  async requestToJoin(username: string, guildTag: string) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild) throw new Error('Guild not found');

    const user = await this.userModel.findOne({ username });
    if (!user) throw new Error('User not found');
    if (user.guildTag && user.guildTag !== 'none') throw new Error('User already in a guild');

    if (guild.pendingRequests.includes(username)) throw new Error('Request already pending');

    // If public, join immediately
    if (guild.isPublic) {
      await this.userModel.findOneAndUpdate({ username }, { guildTag });
      // Add as shareholder with 0 initial shares (can buy later)
      const shares = (guild as any).shares;
      shares.set(username, 0);
      await guild.save();
      return { status: 'joined', guild };
    } else {
      // Add to pending
      await this.guildModel.findOneAndUpdate(
        { tag: guildTag },
        { $addToSet: { pendingRequests: username } }
      ).exec();
      return { status: 'pending' };
    }
  }

  /**
   * Leader handles a join request.
   */
  async handleJoinRequest(leaderUsername: string, guildTag: string, applicantUsername: string, accept: boolean) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild) throw new Error('Guild not found');
    if (guild.leaderUsername !== leaderUsername) throw new Error('Only leader can handle requests');

    if (!guild.pendingRequests.includes(applicantUsername)) throw new Error('Request not found');

    // Remove from pending
    await this.guildModel.findOneAndUpdate(
      { tag: guildTag },
      { $pull: { pendingRequests: applicantUsername } }
    ).exec();

    if (accept) {
      const applicant = await this.userModel.findOne({ username: applicantUsername });
      if (!applicant || (applicant.guildTag && applicant.guildTag !== 'none')) {
        throw new Error('Applicant already in a guild or not found');
      }

      await this.userModel.findOneAndUpdate({ username: applicantUsername }, { guildTag });
      const shares = (guild as any).shares;
      shares.set(applicantUsername, 0);
      await guild.save();
      return { status: 'accepted', guild };
    }

    return { status: 'declined' };
  }

  /**
   * Updates guild settings (e.g., privacy).
   */
  async updateSettings(leaderUsername: string, guildTag: string, settings: { isPublic?: boolean }) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild) throw new Error('Guild not found');
    if (guild.leaderUsername !== leaderUsername) throw new Error('Only leader can update settings');

    if (settings.isPublic !== undefined) {
      guild.isPublic = settings.isPublic;
    }

    await guild.save();
    return guild;
  }

  /**
   * User leaves the guild voluntarily.
   */
  async leaveGuild(username: string, guildTag: string) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild) throw new Error('Guild not found');

    if (guild.leaderUsername === username) {
      throw new Error('Leader cannot leave. You must promote someone else or delete the guild.');
    }

    // Remove user's association
    const user = await this.userModel.findOne({ username });
    if (user && user.guildTag === guildTag) {
      user.guildTag = null;
      await user.save();
    }

    // Remove from shares
    const shares: Map<string, number> = (guild as any).shares;
    if (shares.has(username)) {
      shares.delete(username);
      await guild.save();
    }

    return { status: 'left' };
  }

  /**
   * Leader kicks a member from the guild.
   */
  async kickMember(leaderUsername: string, guildTag: string, targetUsername: string) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild) throw new Error('Guild not found');
    if (guild.leaderUsername !== leaderUsername) throw new Error('Only leader can kick members');
    if (leaderUsername === targetUsername) throw new Error('Cannot kick yourself');

    const targetUser = await this.userModel.findOne({ username: targetUsername });
    if (targetUser && targetUser.guildTag === guildTag) {
      targetUser.guildTag = null;
      await targetUser.save();
    }

    const shares: Map<string, number> = (guild as any).shares;
    if (shares.has(targetUsername)) {
      shares.delete(targetUsername);
      await guild.save();
    }

    return { status: 'kicked', guild };
  }

  /**
   * Leader deletes the guild.
   */
  async deleteGuild(leaderUsername: string, guildTag: string) {
    const guild = await this.getGuildByTag(guildTag);
    if (!guild) throw new Error('Guild not found');
    if (guild.leaderUsername !== leaderUsername) throw new Error('Only leader can delete the guild');

    // Reset all members
    await this.userModel.updateMany({ guildTag }, { $set: { guildTag: null } });

    // Delete guild
    await this.guildModel.deleteOne({ tag: guildTag });

    return { status: 'deleted' };
  }
}
