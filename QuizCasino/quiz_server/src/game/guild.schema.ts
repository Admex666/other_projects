import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class Guild extends Document {
  @Prop({ required: true, unique: true })
  name: string;

  @Prop({ required: true, unique: true })
  tag: string;

  @Prop({ default: '' })
  description: string;

  @Prop({ required: true })
  leaderUsername: string;

  @Prop({ type: Map, of: Number, default: {} })
  shares: Map<string, number>; // username -> number of shares

  @Prop({ default: 1000 })
  totalShares: number;

  @Prop({ default: 0 })
  vaultGold: number;

  @Prop({ default: 5 }) // Default 5% tax
  taxRate: number;

  @Prop({ type: [String], default: [] })
  perks: string[];
}

export const GuildSchema = SchemaFactory.createForClass(Guild);
