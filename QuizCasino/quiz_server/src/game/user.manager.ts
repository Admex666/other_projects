import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { User } from './user.schema';

export interface UserStats {
  userId: string;
  username: string;
  totalCoins: number;
  gamesPlayed: number;
  victories: number;
}

@Injectable()
export class UserManager {
  constructor(@InjectModel(User.name) private userModel: Model<User>) {}

  private mapToStats(user: User): UserStats {
    return {
      userId: user.userId,
      username: user.username,
      totalCoins: user.coins,
      gamesPlayed: user.matchesPlayed,
      victories: user.matchesWon,
    };
  }

  async getUser(userId: string): Promise<UserStats | undefined> {
    const user = await this.userModel.findOne({ userId }).exec();
    return user ? this.mapToStats(user) : undefined;
  }

  async getOrCreateUser(userId: string, username: string): Promise<UserStats> {
    let user = await this.userModel.findOne({ userId }).exec();
    if (!user) {
      user = await this.userModel.create({
        userId,
        username,
        coins: 1000,
        matchesPlayed: 0,
        matchesWon: 0,
      });
    }
    return this.mapToStats(user);
  }

  async updateStats(userId: string, won: boolean, coinsChange: number) {
    await this.userModel.findOneAndUpdate(
      { userId },
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
