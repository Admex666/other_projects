import { Injectable } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';

export interface UserStats {
  userId: string;
  username: string;
  totalCoins: number;
  gamesPlayed: number;
  victories: number;
}

@Injectable()
export class UserManager {
  private users: Map<string, UserStats> = new Map();
  private readonly dbPath = path.join(process.cwd(), 'users.json');

  constructor() {
    this.loadUsers();
  }

  private loadUsers() {
    if (fs.existsSync(this.dbPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(this.dbPath, 'utf8'));
        for (const u of data) {
          this.users.set(u.userId, u);
        }
      } catch (e) {
        console.error('Failed to load users.json', e);
      }
    }
  }

  private saveUsers() {
    try {
      const data = Array.from(this.users.values());
      fs.writeFileSync(this.dbPath, JSON.stringify(data, null, 2));
    } catch (e) {
      console.error('Failed to save users.json', e);
    }
  }

  getUser(userId: string): UserStats | undefined {
    return this.users.get(userId);
  }

  getOrCreateUser(userId: string, username: string): UserStats {
    let user = this.users.get(userId);
    if (!user) {
      user = {
        userId,
        username,
        totalCoins: 1000, // Starting balance
        gamesPlayed: 0,
        victories: 0,
      };
      this.users.set(userId, user);
      this.saveUsers();
    }
    return user;
  }

  updateStats(userId: string, won: boolean, coinsChange: number) {
    const user = this.users.get(userId);
    if (user) {
      user.totalCoins += coinsChange;
      user.gamesPlayed += 1;
      if (won) user.victories += 1;
      this.saveUsers();
    }
  }
}
