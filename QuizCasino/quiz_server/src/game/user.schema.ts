import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class User extends Document {
  @Prop({ required: true, unique: true })
  userId: string;

  @Prop({ required: true })
  username: string;

  @Prop({ default: 100 })
  coins: number;

  @Prop({ default: 0 })
  matchesPlayed: number;

  @Prop({ default: 0 })
  matchesWon: number;
}

export const UserSchema = SchemaFactory.createForClass(User);
