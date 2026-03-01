import { create } from 'zustand'
import { Card } from '@/lib/game/deck'
import { Bid } from '@/lib/game/rules'

export type GameStatus = 'dealing' | 'bidding' | 'playing' | 'finished'

export interface TrickCard {
    player_id: string
    card: Card
}

export interface GameStateData {
    hands?: Record<string, Card[]>  // Usually only contains OUR hand securely
    talon?: Card[]
    biddingHistory?: { player_id: string, bid: Bid | 'pass' }[]
    currentTrick?: TrickCard[]
    tricksWon?: { winner: string, cards: TrickCard[] }[]
}

export interface Game {
    id: string
    room_id: string
    dealer_id: string
    active_player_id: string
    status: GameStatus
    state: GameStateData
    current_bid: Bid | null
    trump_suit: string | null
}

interface GameStoreState {
    currentGame: Game | null
    setCurrentGame: (game: Game | null) => void
    myHand: Card[]
    setMyHand: (hand: Card[]) => void
}

export const useGameStore = create<GameStoreState>((set) => ({
    currentGame: null,
    setCurrentGame: (game) => set({ currentGame: game }),
    myHand: [],
    setMyHand: (hand) => set({ myHand: hand }),
}))
