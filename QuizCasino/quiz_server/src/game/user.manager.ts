import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { User } from './user.schema';
import * as bcrypt from 'bcrypt';

export interface UserStats {
  username: string;
  totalCoins: number;
  gamesPlayed: number;
  victories: number;
}

@Injectable()
export class UserManager {
  private readonly saltRounds = 10;

  constructor(@InjectModel(User.name) private userModel: Model<User>) {}

  private mapToStats(user: User): UserStats {
    return {
      username: user.username,
      totalCoins: user.coins,
      gamesPlayed: user.matchesPlayed,
      victories: user.matchesWon,
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
      userId: username, // Mirror username to satisfy existing index
      password: hashedPassword,
      coins: 1000,
      matchesPlayed: 0,
      matchesWon: 0,
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

  async updateStats(username: string, won: boolean, coinsChange: number) {
    await this.userModel.findOneAndUpdate(
      { username },
      {
        $inc: {
          coins: coinsChange,
          matchesPlayed: 1,
          matchesWon: won ? 1 : 0,
        },
      },
    ).exec();
  }
}
