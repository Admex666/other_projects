export type Suit = 'piros' | 'tok' | 'zold' | 'makk'
export type Rank = 'vii' | 'viii' | 'ix' | 'x' | 'also' | 'felso' | 'kiraly' | 'asz'

export interface Card {
    id: string // e.g., 'piros_asz'
    suit: Suit
    rank: Rank
    // Base values for counting points at the end of the game
    value: number // 10 for Ász and X, 0 for others

    // Power is used to determine which card wins the trick.
    // Power depends on the game type (Adu, Színnélküli) -> calculated dynamically.
    // Base power: VII < VIII < IX < Also < Felso < Kiraly < X < Asz
    basePowerLevel: number
}

const SUITS: Suit[] = ['piros', 'tok', 'zold', 'makk']
const RANKS: Rank[] = ['vii', 'viii', 'ix', 'x', 'also', 'felso', 'kiraly', 'asz']

const rankPowers: Record<Rank, number> = {
    'vii': 1,
    'viii': 2,
    'ix': 3,
    'also': 4,
    'felso': 5,
    'kiraly': 6,
    'x': 7, // Notice X is stronger than Kiraly in Adujáték
    'asz': 8
}

const rankValues: Record<Rank, number> = {
    'vii': 0,
    'viii': 0,
    'ix': 0,
    'also': 0,
    'felso': 0,
    'kiraly': 0,
    'x': 10,
    'asz': 10
}

/**
 * Generates a full 32-card Hungarian deck.
 */
export function generateDeck(): Card[] {
    const deck: Card[] = []
    for (const suit of SUITS) {
        for (const rank of RANKS) {
            deck.push({
                id: `${suit}_${rank}`,
                suit,
                rank,
                value: rankValues[rank],
                basePowerLevel: rankPowers[rank]
            })
        }
    }
    return deck
}

/**
 * Shuffles the deck using Fisher-Yates algorithm.
 */
export function shuffleDeck(deck: Card[]): Card[] {
    const shuffled = [...deck]
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
    }
    return shuffled
}

export interface DealResult {
    player1: Card[] // Takes 12 cards if they are the first bidder (osztó után jobbra)
    player2: Card[] // 10 cards
    player3: Card[] // 10 cards
    talon?: Card[]  // The 2 cards the first player puts down. Initially empty, as P1 gets 12.
}

/**
 * Deals the cards. Player1 gets 12 cards, Player2 gets 10, Player3 gets 10.
 * In a real game, 'dealer' determines who gets 12 cards (dealer + 1).
 * We will assume the API maps Player1 to the first bidder.
 */
export function dealCards(deck: Card[]): DealResult {
    if (deck.length !== 32) throw new Error("Deck must have exactly 32 cards")

    // Dealing pattern: e.g., 7-5-5-5-5-5 or similar. For simplicity, just slice.
    return {
        player1: deck.slice(0, 12),
        player2: deck.slice(12, 22),
        player3: deck.slice(22, 32),
    }
}
