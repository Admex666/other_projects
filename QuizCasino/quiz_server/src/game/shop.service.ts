import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { User } from './user.schema';

export interface ShopItem {
  id: string;
  name: string;
  type: 'skin' | 'trail' | 'animation' | 'chest';
  price: number;
  currency: 'gold' | 'diamonds';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

@Injectable()
export class ShopService {
  private readonly logger = new Logger(ShopService.name);

  private readonly catalog: ShopItem[] = [
    // Dot Skins
    { id: 'skin_neon_ring', name: 'Neon Ring', type: 'skin', price: 500, currency: 'gold', rarity: 'rare' },
    { id: 'skin_star', name: 'Star Shape', type: 'skin', price: 100, currency: 'diamonds', rarity: 'epic' },
    { id: 'skin_diamond_3d', name: '3D Diamond', type: 'skin', price: 250, currency: 'diamonds', rarity: 'legendary' },
    
    // Trails
    { id: 'trail_ghost', name: 'Ghost Trail', type: 'trail', price: 300, currency: 'gold', rarity: 'rare' },
    { id: 'trail_fire', name: 'Fire Trail', type: 'trail', price: 150, currency: 'diamonds', rarity: 'epic' },
    
    // Animations
    { id: 'anim_confetti', name: 'Confetti Rain', type: 'animation', price: 200, currency: 'gold', rarity: 'rare' },
    { id: 'anim_lightning', name: 'Lightning Strike', type: 'animation', price: 100, currency: 'diamonds', rarity: 'epic' },
    
    // Chests
    { id: 'chest_silver', name: 'Silver Chest', type: 'chest', price: 200, currency: 'gold', rarity: 'common' },
    { id: 'chest_gold', name: 'Gold Chest', type: 'chest', price: 50, currency: 'diamonds', rarity: 'rare' },
  ];

  constructor(
    @InjectModel(User.name) private userModel: Model<User>,
  ) {
    // ADMIN: Give test1 some starting funds as requested
    this.userModel.findOneAndUpdate(
      { username: 'test1' },
      { $set: { gold: 10000, diamonds: 5000 } }
    ).exec().then(() => this.logger.log('Granted 10k gold and 5k gems to test1'));
  }

  getCatalog(): ShopItem[] {
    return this.catalog;
  }

  async purchaseItem(username: string, itemId: string) {
    const item = this.catalog.find(i => i.id === itemId);
    if (!item) throw new Error('Item not found');

    const user = await this.userModel.findOne({ username });
    if (!user) throw new Error('User not found');

    // Check if already owned (except chests)
    if (item.type !== 'chest' && user.inventory.includes(itemId)) {
      throw new Error('You already own this item');
    }

    // Check funds
    if (item.currency === 'gold') {
      if (user.gold < item.price) throw new Error('Not enough gold');
      user.gold -= item.price;
    } else {
      if (user.diamonds < item.price) throw new Error('Not enough diamonds');
      user.diamonds -= item.price;
    }

    let rewards = null;

    // Add to inventory (if not chest)
    if (item.type !== 'chest') {
      user.inventory.push(itemId);
    } else {
      rewards = this.openChest(item.id);
      user.gold += rewards.gold;
      user.diamonds += rewards.diamonds;
      if (rewards.item && !user.inventory.includes(rewards.item.id)) {
        user.inventory.push(rewards.item.id);
      }
      this.logger.log(`${username} opened ${item.name} and got ${JSON.stringify(rewards)}`);
    }

    await user.save();
    return { user, rewards };
  }

  private openChest(chestId: string) {
    const isGold = chestId === 'chest_gold';
    const gold = isGold ? Math.floor(Math.random() * 500) + 100 : Math.floor(Math.random() * 1000) + 200;
    const diamonds = isGold ? Math.floor(Math.random() * 100) + 50 : Math.floor(Math.random() * 20) + 5;
    
    // 20% chance for an item in Silver, 50% in Gold
    const itemChance = isGold ? 0.5 : 0.2;
    let rewardItem = null;
    
    if (Math.random() < itemChance) {
      const cosmetics = this.catalog.filter(i => i.type !== 'chest');
      rewardItem = cosmetics[Math.floor(Math.random() * cosmetics.length)];
    }

    return { gold, diamonds, item: rewardItem };
  }

  async equipItem(username: string, itemId: string) {
    const user = await this.userModel.findOne({ username });
    if (!user) throw new Error('User not found');

    if (!user.inventory.includes(itemId) && itemId !== 'default' && itemId !== 'none') {
      throw new Error('Item not found in inventory');
    }

    const item = this.catalog.find(i => i.id === itemId);
    if (!item && itemId !== 'default' && itemId !== 'none') throw new Error('Item data not found');

    const type = item?.type || (itemId === 'default' ? 'skin' : 'trail');

    if (type === 'skin') user.equippedSkin = itemId;
    else if (type === 'trail') user.equippedTrail = itemId;
    else if (type === 'animation') user.equippedAnimation = itemId;

    await user.save();
    return user;
  }
}
