import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class User extends Document {
  @Prop({ required: true, unique: true })
  username: string;

  @Prop({ unique: true, sparse: true })
  userId: string;

  @Prop({ required: true })
  password: string;

  @Prop({ default: 1000 })
  coins: number; // For backward compatibility if needed, but we will mostly use gold

  @Prop({ default: 500 })
  gold: number;

  @Prop({ default: 0 })
  diamonds: number;

  @Prop({ default: 0 })
  matchesPlayed: number;

  @Prop({ default: 0 })
  matchesWon: number;

  @Prop({ default: 1500 })
  elo: number;

  @Prop({ default: 1500 })
  hiddenElo: number;

  @Prop({ default: 'unranked' })
  league: string;

  @Prop({ default: 'III' })
  division: string;

  @Prop({ default: 0 })
  placementMatches: number;

  @Prop({ type: [Number], default: [] })
  weeklyScores: number[]; // Scores of all matches this week (for Top 5 calculation)

  @Prop()
  lastWeeklyUpdate: Date;

  @Prop({ type: [String], default: [] })
  inventory: string[];

  @Prop({ default: 'default' })
  equippedSkin: string;

  @Prop({ default: 'none' })
  equippedTrail: string;

  @Prop({ default: 'none' })
  equippedAnimation: string;

  @Prop({ default: null })
  guildTag: string;
}

export const UserSchema = SchemaFactory.createForClass(User);
