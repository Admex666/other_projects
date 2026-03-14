import { GameState, Player, Question, Bet, RoundResult } from './game.types';
import axios from 'axios';
import * as he from 'he'; // HTML entities decode

interface GameEventCallbacks {
  onStateUpdate: (state: any) => void;
  onMatchEnded: (results: any, history: any) => void;
  onTick: (time: number) => void;
}

export class GameLogic {
  public roomId: string;
  public players: Player[] = [];
  public currentState: GameState = GameState.Waiting;

  // Match rules
  public currentRound = 1;
  public maxRounds = 7;
  public shieldRounds = 2; // Rounds 1 and 2 have no elimination
  public questionDurationSec = 15;
  public revealDurationSec = 5;

  private fetchedQuestions: Question[] = [];
  private currentQuestionIndex = 0;
  private currentTimer = 0;
  private tickInterval: NodeJS.Timeout | null = null;
  
  private currentQuestion: Question | null = null;
  private currentBets: Map<string, Bet> = new Map();
  private lastRoundResult: RoundResult | null = null;
  private carriedOverPot = 0;

  // Analytics history
  private startTime: Date;
  private roundHistory: any[] = [];
  private playerInitialStacks: Map<string, number> = new Map();

  private callbacks: GameEventCallbacks;

  constructor(roomId: string, callbacks: GameEventCallbacks) {
    this.roomId = roomId;
    this.callbacks = callbacks;
  }

  get currentMinBet(): number {
    return this.currentRound <= this.shieldRounds ? 10 : (this.currentRound - this.shieldRounds) * 10 + 10;
  }

  public get isFull(): boolean {
    return this.players.length >= 4;
  }

  public addPlayer(player: Player) {
    if (this.isFull) return;
    this.players.push(player);
  }

  public removePlayer(playerId: string) {
    const idx = this.players.findIndex(p => p.id === playerId);
    if (idx !== -1) {
      this.players[idx].isEliminated = true;
    }
    // In a real app we might disconnect them, but here we just mark as eliminated or let bots take over
  }

  public async startMatch() {
    this.currentRound = 1;
    this.currentQuestionIndex = 0;
    this.currentState = GameState.Waiting;
    this.startTime = new Date();
    this.roundHistory = [];
    this.carriedOverPot = 0;
    
    // Snapshot initial stacks
    this.playerInitialStacks.clear();
    for (const p of this.players) {
      this.playerInitialStacks.set(p.username, p.stack);
    }

    this.broadcastState();

    await this.fetchTriviaQuestions();

    this.changeState(GameState.QuestionActive);
  }

  private async fetchTriviaQuestions() {
    try {
      const resp = await axios.get('https://opentdb.com/api.php?amount=10');
      if (resp.status === 200 && resp.data.results) {
        const results = resp.data.results;
        
        this.fetchedQuestions = results.map((item: any) => {
          const qText = he.decode(item.question);
          const correct = he.decode(item.correct_answer);
          const incorrects = item.incorrect_answers.map((x: string) => he.decode(x));
          
          const allAnswers = [...incorrects, correct];
          // Snap initial chips (100 in V4)
          for (const p of this.players) {
            if (p.stack !== 100) p.stack = 100;
          }
          // Shuffle answers
          for (let i = allAnswers.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [allAnswers[i], allAnswers[j]] = [allAnswers[j], allAnswers[i]];
          }
          
          return {
            questionText: qText,
            answers: allAnswers,
            correctAnswerIndex: allAnswers.indexOf(correct)
          };
        });
        return;
      }
    } catch(e) {
      console.error("Failed to fetch questions", e);
    }

    // Fallback
    this.fetchedQuestions = [
      { questionText: "Fallback Q1?", answers: ["A","B","C","D"], correctAnswerIndex: 0 },
      { questionText: "Fallback Q2?", answers: ["A","B","C","D"], correctAnswerIndex: 1 },
      { questionText: "Fallback Q3?", answers: ["A","B","C","D"], correctAnswerIndex: 2 },
    ];
  }

  private changeState(newState: GameState) {
    this.currentState = newState;
    if (this.tickInterval) clearInterval(this.tickInterval);

    if (this.currentState === GameState.QuestionActive) {
      if (this.currentQuestionIndex >= this.fetchedQuestions.length) {
        this.currentQuestionIndex = 0;
      }
      this.currentQuestion = this.fetchedQuestions[this.currentQuestionIndex++];
      this.currentBets.clear();
      this.currentTimer = this.questionDurationSec;
      
      this.simulateBotsQuestions();
      this.tickInterval = setInterval(() => this.tick(), 1000);
      this.broadcastState();

    } else if (this.currentState === GameState.Reveal) {
      this.processRoundResults();
      this.currentTimer = this.revealDurationSec;
      this.tickInterval = setInterval(() => this.tick(), 1000);
      this.broadcastState();
    }
  }

  private tick() {
    if (this.currentTimer > 0) {
      this.currentTimer--;
      this.callbacks.onTick(this.currentTimer);
    } else {
      if (this.tickInterval) clearInterval(this.tickInterval);
      if (this.currentState === GameState.QuestionActive) {
        this.changeState(GameState.Reveal);
      } else if (this.currentState === GameState.Reveal) {
        this.recordRoundHistory();
        this.handleRoundEnd();
      }
    }
  }

  private recordRoundHistory() {
    if (!this.currentQuestion) return;

    const roundData = {
      questionText: this.currentQuestion.questionText,
      correctAnswerIndex: this.currentQuestion.correctAnswerIndex,
      bets: Array.from(this.currentBets.values()).map(b => {
        const p = this.players.find(x => x.id === b.playerId);
        return {
          username: p?.username || 'Unknown',
          amount: b.amount,
          answerIndex: b.answerIndex,
          isCorrect: b.answerIndex === this.currentQuestion?.correctAnswerIndex,
          isBot: b.playerId.startsWith('bot_'),
          timestamp: new Date()
        };
      })
    };
    this.roundHistory.push(roundData);
  }

  public placeBet(playerId: string, amount: number) {
    if (this.currentState !== GameState.QuestionActive) return;
    const player = this.players.find(p => p.id === playerId);
    if (!player || player.isEliminated) return;

    let betAmount = amount;
    if (betAmount < this.currentMinBet && player.stack > this.currentMinBet) {
      betAmount = this.currentMinBet;
    }
    
    const existing = this.currentBets.get(playerId);
    this.currentBets.set(playerId, {
      playerId,
      amount: betAmount,
      answerIndex: existing ? existing.answerIndex : -1
    });
    this.broadcastState();
  }

  public selectAnswer(playerId: string, index: number) {
    if (this.currentState !== GameState.QuestionActive) return;
    const player = this.players.find(p => p.id === playerId);
    if (!player || player.isEliminated) return;

    const existing = this.currentBets.get(playerId);
    // If they haven't manually placed a bet, default to forced min bet or stack
    let amt = existing ? existing.amount : this.currentMinBet;
    if (player.stack <= this.currentMinBet) {
      amt = player.stack;
    }

    this.currentBets.set(playerId, {
      playerId,
      amount: amt,
      answerIndex: index
    });
    this.broadcastState();
  }

  private processRoundResults() {
    // Collect missing bets (min bet if they didn't even click)
    for (const p of this.players) {
      if (!p.isEliminated && !this.currentBets.has(p.id)) {
        let amt = this.currentMinBet;
        if (p.stack <= this.currentMinBet) amt = p.stack;
        this.currentBets.set(p.id, { playerId: p.id, amount: amt, answerIndex: -1 });
      }
    }

    // 1. Collect all bets
    const totalPot = Array.from(this.currentBets.values()).reduce((sum, b) => sum + b.amount, 0);
    const netChanges: Record<string, number> = {};

    console.log(`[Room ${this.roomId}] Processing results. Total Pot: ${totalPot}`);
    console.log(`Bets:`, Array.from(this.currentBets.values()));

    // First deduct bets from everyone who bet
    for (const [pId, bet] of this.currentBets.entries()) {
      const p = this.players.find(x => x.id === pId);
      if (p) {
        p.stack -= bet.amount;
        netChanges[pId] = -bet.amount;
      }
    }

    // 2. Distribute to winners
    const correctIndex = this.currentQuestion?.correctAnswerIndex ?? -1;
    const winningBets: Bet[] = [];
    for (const bet of this.currentBets.values()) {
      if (bet.answerIndex === correctIndex) {
        winningBets.push(bet);
      }
    }

    const availablePot = totalPot + this.carriedOverPot;

    if (winningBets.length > 0) {
      const winningPool = winningBets.reduce((sum, b) => sum + b.amount, 0);
      for (const winBet of winningBets) {
        const proportion = winBet.amount / winningPool;
        const reward = Math.floor(availablePot * proportion);
        const p = this.players.find(x => x.id === winBet.playerId);
        if (p) {
          p.stack += reward;
          netChanges[p.id] = (netChanges[p.id] || 0) + reward;
        }
      }
      this.carriedOverPot = 0;
    } else {
      // If nobody won, pot is carried over
      this.carriedOverPot = availablePot;
      console.log(`[Room ${this.roomId}] NO WINNERS. Pot ${this.carriedOverPot} carried over to next round.`);
    }

    this.lastRoundResult = { totalPot: availablePot, netChanges };
  }

  private handleRoundEnd() {
    console.log(`[Room ${this.roomId}] handleRoundEnd - Round: ${this.currentRound}`);
    this.processEliminations();

    const activePlayers = this.players.filter(p => !p.isEliminated).length;
    const realPlayersActive = this.players.filter(p => !p.isEliminated && !p.id.startsWith('bot_')).length;

    console.log(`[Room ${this.roomId}] Active: ${activePlayers}, Real Active: ${realPlayersActive}`);

    if (activePlayers <= 1 || realPlayersActive === 0 || this.currentRound >= this.maxRounds) {
      console.log(`[Room ${this.roomId}] Triggering endMatch. Reason: ${activePlayers <= 1 ? '1 or 0 players left' : realPlayersActive === 0 ? 'No real players' : 'Max rounds reached'}`);
      this.endMatch();
      return;
    }

    this.currentRound++;
    console.log(`[Room ${this.roomId}] Moving to Round ${this.currentRound}`);
    this.changeState(GameState.QuestionActive);
  }

  private processEliminations() {
    if (this.currentRound <= this.shieldRounds) return;

    for (const p of this.players) {
      if (p.stack <= 0) p.isEliminated = true;
    }

    const activeList = this.players.filter(p => !p.isEliminated);
    if (activeList.length > 1) {
      const toEliminate = Math.ceil(activeList.length * 0.2);
      if (toEliminate > 0) {
        activeList.sort((a, b) => a.stack - b.stack);
        for (let i = 0; i < toEliminate; i++) {
          activeList[i].isEliminated = true;
        }
      }
    }
  }

  private endMatch() {
    console.log(`[Room ${this.roomId}] Ending match...`);
    this.currentState = GameState.Result;
    if (this.tickInterval) clearInterval(this.tickInterval);

    this.players.sort((a, b) => {
      if (a.isEliminated && !b.isEliminated) return 1;
      if (!a.isEliminated && b.isEliminated) return -1;
      return b.stack - a.stack;
    });

    console.log(`[Room ${this.roomId}] Final players sorted. Emitting state and match_ended.`);
    this.broadcastState();

    const history = {
      startTime: this.startTime,
      endTime: new Date(),
      players: this.players.map(p => {
        const rank = this.players.indexOf(p) + 1;
        return {
          username: p.username,
          isBot: p.id.startsWith('bot_'),
          startStack: this.playerInitialStacks.get(p.username) || 100,
          endStack: p.stack,
          rank
        }
      }),
      rounds: this.roundHistory
    };

    this.callbacks.onMatchEnded(this.players, history);
  }

  private simulateBotsQuestions() {
    for (const p of this.players) {
      if (p.isEliminated || !p.id.startsWith('bot_')) continue;

      const limitMultiplier = this.currentRound <= this.shieldRounds ? 0.4 : 1.0;
      let maxBet = Math.floor(p.stack * limitMultiplier);
      
      let botBet = 0;
      if (p.stack <= this.currentMinBet) {
        botBet = p.stack;
      } else {
        if (maxBet < this.currentMinBet) maxBet = this.currentMinBet;
        botBet = maxBet > this.currentMinBet ? Math.floor(Math.random() * (maxBet - this.currentMinBet)) + this.currentMinBet : maxBet;
      }

      // Bots answer slightly later to make it look real
      setTimeout(() => {
        if (this.currentState !== GameState.QuestionActive) return;
        const isCorrect = Math.random() > 0.4; // 60% accurate
        const answerIndex = isCorrect ? (this.currentQuestion?.correctAnswerIndex ?? 0) : ((this.currentQuestion?.correctAnswerIndex ?? 0) + 1) % 4;
        
        this.currentBets.set(p.id, {
          playerId: p.id,
          amount: botBet,
          answerIndex
        });
        this.broadcastState();
      }, 2000 + Math.random() * 5000);
    }
  }

  private broadcastState() {
    // Only send what the UI needs, scrub correct answer if in QuestionActive state!
    let q = this.currentQuestion;
    if (q && this.currentState === GameState.QuestionActive) {
      q = { ...q, correctAnswerIndex: -1 }; // Hide it!
    }

    this.callbacks.onStateUpdate({
      roomId: this.roomId,
      currentState: this.currentState,
      currentRound: this.currentRound,
      currentTimer: this.currentTimer,
      players: this.players,
      currentQuestion: q,
      currentBets: Array.from(this.currentBets.values()),
      lastRoundResult: this.lastRoundResult,
      currentMinBet: this.currentMinBet
    });
  }
}
