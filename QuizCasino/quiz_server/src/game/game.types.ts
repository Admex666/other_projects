export enum GameState {
  Waiting = 'waiting',
  QuestionActive = 'questionActive',
  Reveal = 'reveal',
  Result = 'result',
}

export interface Player {
  id: string; // current socketId
  userId: string; // persistentId
  username: string;
  stack: number;
  isEliminated: boolean;
  elo: number;
  hiddenElo: number;
  equippedSkin?: string;
  equippedTrail?: string;
  equippedAnimation?: string;
}

export interface Question {
  questionText: string;
  answers: string[];
  correctAnswerIndex: number;
}

export interface Bet {
  playerId: string;
  amount: number;
  answerIndex: number; // 0..3 (-1 if didn't bet/timeout)
}

export interface RoundResult {
  totalPot: number;
  netChanges: Record<string, number>;
}
