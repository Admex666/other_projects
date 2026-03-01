import { Card, Suit, Rank } from './deck'

/**
 * Szabály 1: Színre színt kell adni.
 * Szabály 2: Ha nincs a hívott színből, ADUT kell tenni (ha van).
 * Szabály 3: Ha van a szükséges színből (akár hívott, akár adu), FELÜLÜTNI (íberelni) kötelező!
 */

export interface ValidationResult {
    isValid: boolean
    error?: string
}

/**
 * Validates if the card played is allowed according to the current trick state.
 * 
 * @param playedCard The card the player intends to play
 * @param playerHand The remaining cards in the player's hand
 * @param leadCard The first card played in this trick (if any)
 * @param trickCards The cards already played in this trick (including leadCard)
 * @param trumpSuit The current trump suit (null if Színnélküli)
 */
export function validatePlay(
    playedCard: Card,
    playerHand: Card[],
    leadCard: Card | null,
    trickCards: Card[],
    trumpSuit: Suit | null
): ValidationResult {
    // 1. If leadCard is null, this is the first card of the trick. Anything goes.
    if (!leadCard) return { isValid: true }

    const hasLedSuit = playerHand.some(c => c.suit === leadCard.suit)
    const hasTrumpSuit = trumpSuit !== null ? playerHand.some(c => c.suit === trumpSuit) : false

    // Determine the current highest card in the trick that matters.
    // The trick is won by: the highest trump card, OR the highest card of the lead suit (if no trumps).
    let currentWinner = leadCard
    for (const card of trickCards) {
        if (trumpSuit && card.suit === trumpSuit && currentWinner.suit !== trumpSuit) {
            currentWinner = card // First trump played beats non-trump
        } else if (card.suit === currentWinner.suit && card.basePowerLevel > currentWinner.basePowerLevel) {
            currentWinner = card // Higher card of the winning suit
        }
    }

    // 1. Must follow suit (színre szín)
    if (hasLedSuit) {
        if (playedCard.suit !== leadCard.suit) {
            return { isValid: false, error: `Színre színt kell adni! Van ${leadCard.suit} a kezedben.` }
        }

        // 3. Must overtrick (íberelni) if possible
        if (playedCard.suit === currentWinner.suit) { // Winner is also the led suit
            const canOvertrickLead = playerHand.some(c => c.suit === leadCard.suit && c.basePowerLevel > currentWinner.basePowerLevel)
            if (canOvertrickLead && playedCard.basePowerLevel <= currentWinner.basePowerLevel) {
                return { isValid: false, error: 'Felül kell ütni (íberelni), mert van rá lehetőséged a hivatott színből!' }
            }
        }
        return { isValid: true }
    }

    // 2. Cannot follow suit. Must play trump if available.
    if (hasTrumpSuit) {
        if (playedCard.suit !== trumpSuit) {
            return { isValid: false, error: `Nincs színed, adut (${trumpSuit}) kell tenned!` }
        }

        // Must overtrick an existing trump if possible
        if (currentWinner.suit === trumpSuit) {
            const canOvertrickTrump = playerHand.some(c => c.suit === trumpSuit && c.basePowerLevel > currentWinner.basePowerLevel)
            if (canOvertrickTrump && playedCard.basePowerLevel <= currentWinner.basePowerLevel) {
                return { isValid: false, error: 'Adut aduba felül kell ütni!' }
            }
        }
        return { isValid: true }
    }

    // 3. Cannot follow suit and no trumps. Can play anything.
    return { isValid: true }
}

export interface Bid {
    id: string
    player_id: string
    name: string // e.g., 'Passz', 'Parti', '40-100', 'Ulti', 'Durchmars'
    baseValue: number
    includesTrump: boolean
}

// Egyszerűsített licitszokások, amik egyenlőre csak a hivatalos ULTI_szabályzat legfontosabbjait tükrözik
export const AVAILABLE_BIDS: Bid[] = [
    { id: 'pass', player_id: '', name: 'Passz', baseValue: 0, includesTrump: false },
    { id: 'parti', player_id: '', name: 'Parti', baseValue: 1, includesTrump: true },
    { id: 'ulti', player_id: '', name: 'Ulti', baseValue: 4, includesTrump: true }, // Ulti magában nem játszható a szabály szerint, de mint legkisebb licit használatos. A játékos e mellé automatikusan partit is vállal
    { id: '40-100', player_id: '', name: '40-100', baseValue: 4, includesTrump: true },
    { id: 'betli', player_id: '', name: 'Betli', baseValue: 5, includesTrump: false },
    { id: 'durchmars', player_id: '', name: 'Durchmars', baseValue: 6, includesTrump: true },
    { id: '20-100', player_id: '', name: '20-100', baseValue: 8, includesTrump: true },
    { id: 'rebetli', player_id: '', name: 'ReBetli', baseValue: 10, includesTrump: false },
    { id: 'teritett_durchmars', player_id: '', name: 'Terített Durchmars', baseValue: 12, includesTrump: true },
    { id: 'teritett_betli', player_id: '', name: 'Terített Betli', baseValue: 20, includesTrump: false }
]

export function isValidNextBid(currentHighestBid: Bid | null, newBid: Bid): boolean {
    if (newBid.id === 'pass') return true
    if (!currentHighestBid) return true
    return newBid.baseValue > currentHighestBid.baseValue
}
