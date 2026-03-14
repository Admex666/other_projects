import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema()
class BetRecord {
  @Prop({ required: true })
  username: string;

  @Prop({ required: true })
  amount: number;

  @Prop({ required: true })
  answerIndex: number;

  @Prop({ required: true })
  isCorrect: boolean;

  @Prop({ required: true })
  isBot: boolean;

  @Prop({ default: Date.now })
  timestamp: Date;
}

@Schema()
class RoundRecord {
  @Prop({ required: true })
  questionText: string;

  @Prop({ required: true })
  correctAnswerIndex: number;

  @Prop({ type: [BetRecord], default: [] })
  bets: BetRecord[];
}

@Schema()
class PlayerResult {
  @Prop({ required: true })
  username: string;

  @Prop({ required: true })
  isBot: boolean;

  @Prop({ required: true })
  startStack: number;

  @Prop({ required: true })
  endStack: number;

  @Prop({ required: true })
  rank: number;
}

@Schema({ timestamps: true })
export class Match extends Document {
  @Prop({ required: true })
  roomId: string;

  @Prop({ type: [PlayerResult], required: true })
  players: PlayerResult[];

  @Prop({ type: [RoundRecord], required: true })
  rounds: RoundRecord[];

  @Prop({ default: Date.now })
  startTime: Date;

  @Prop({ default: Date.now })
  endTime: Date;
}

export const MatchSchema = SchemaFactory.createForClass(Match);
