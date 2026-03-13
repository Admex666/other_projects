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
  coins: number;

  @Prop({ default: 0 })
  matchesPlayed: number;

  @Prop({ default: 0 })
  matchesWon: number;
}

export const UserSchema = SchemaFactory.createForClass(User);
