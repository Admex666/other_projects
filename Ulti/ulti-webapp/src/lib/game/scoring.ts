import { Card } from './deck'
import { Bid } from './rules'
import { TrickCard, GameStateData } from '@/store/gameStore'

export interface PlayerScore {
    playerId: string
    isBidWinner: boolean
    cardPoints: number // 10k, Ászok (max 80)
    announcePoints: number // bemondott 20-ak, 40-ek értéke
    totalPoints: number // cardPoints + announcePoints
    wonTricksCount: number
    wonLastTrick: boolean
    moneyDelta: number // The final calculation of win/loss in units (points/money)
}

export interface GameResult {
    bid: Bid
    trumpSuit: string | null
    bidWinnerId: string
    defendersIds: string[]
    scores: Record<string, PlayerScore>
    baseBidValue: number
    multiplier: number // Kontrák miatt (1, 2, 4, 8)
    bidSuccessful: boolean
    silentUltiWinner?: string // Különdíjas csendes ulti nyertes (ha van)
    silentUltiLoser?: string  // Ha valaki elbukta az adu hetest az utolsó ütésben
}

function getCardPointValue(card: Card): number {
    if (card.rank === 'asz' || card.rank === 'x') return 10
    return 0
}

export function calculateGameScore(
    state: GameStateData,
    currentBid: Bid,
    trumpSuit: string | null,
    p1: string, p2: string, p3: string
): GameResult {
    const players = [p1, p2, p3]
    const bidWinnerId = currentBid.player_id
    const defendersIds = players.filter(p => p !== bidWinnerId)

    // 1. Initialize Scores
    const scores: Record<string, PlayerScore> = {}
    players.forEach(p => {
        scores[p] = {
            playerId: p, isBidWinner: p === bidWinnerId,
            cardPoints: 0, announcePoints: 0, totalPoints: 0,
            wonTricksCount: 0, wonLastTrick: false, moneyDelta: 0
        }
    })

    // 2. Tally Trick Points (Ász, Tízes) & Trick Counts
    const tricks = state.tricksWon || []
    tricks.forEach((trick, index) => {
        const winner = trick.winner
        scores[winner].wonTricksCount += 1

        trick.cards.forEach(tc => {
            scores[winner].cardPoints += getCardPointValue(tc.card)
        })

        if (index === 9) {
            scores[winner].wonLastTrick = true
        }
    })

    // Talon pontok a Védőké (ha van benne Ász vagy Tízes)
    if (state.talon && state.talon.length > 0) {
        let talonPts = 0
        state.talon.forEach(c => talonPts += getCardPointValue(c))
        // Adjuk hozzá az első védőhöz technikailag (a csapatpont számításnál úgyis összeadódik)
        scores[defendersIds[0]].cardPoints += talonPts
    }

    // 3. Tally Announcements (20, 40)
    const announcements = state.announcements || []
    announcements.forEach(ann => {
        const pts = ann.type === '40' ? 40 : 20
        scores[ann.player_id].announcePoints += pts
    })

    // Sum up totals
    players.forEach(p => {
        scores[p].totalPoints = scores[p].cardPoints + scores[p].announcePoints
    })

    // 4. Calculate Multipliers from Doubles
    let multiplier = 1
    const doubles = state.doubles || []
    if (doubles.length > 0) {
        // kontra = 2x, rekontra = 4x, szubkontra = 8x stb.
        multiplier = Math.pow(2, doubles.length)
    }

    // 5. Evaluate Bid Success
    let bidSuccessful = false
    let baseBidValue = currentBid.baseValue

    const bidderTotal = scores[bidWinnerId].totalPoints
    const defendersTotal = scores[defendersIds[0]].totalPoints + scores[defendersIds[1]].totalPoints

    if (currentBid.id === 'pass') {
        bidSuccessful = true // Nincs értelme, de fallback
    } else if (currentBid.id === 'parti') {
        bidSuccessful = bidderTotal > defendersTotal
    } else if (currentBid.id === '40-100') {
        bidSuccessful = bidderTotal >= 100
    } else if (currentBid.id === '20-100') {
        bidSuccessful = bidderTotal >= 100
    } else if (currentBid.id.includes('betli')) {
        bidSuccessful = scores[bidWinnerId].wonTricksCount === 0
    } else if (currentBid.id.includes('durchmars')) {
        bidSuccessful = scores[bidWinnerId].wonTricksCount === 10
    } else if (currentBid.id === 'ulti') {
        // Ulti: Az utolsó ütést a felvevőnek kell vinnie az adu hetessel
        const lastTrickCards = tricks[9]?.cards || []
        const wonLast = scores[bidWinnerId].wonLastTrick
        const playedTrumpSeven = lastTrickCards.some(tc => tc.player_id === bidWinnerId && tc.card.suit === trumpSuit && tc.card.rank === 'vii')
        bidSuccessful = wonLast && playedTrumpSeven
    }

    // 6. Calculate Financial/Point Deltas
    // Simple logic: Winner gets (BidValue * Multiplier) from BOTH losers.
    // If bidder wins, they get +2 * (Val*Mult), defenders get -(Val*Mult).
    // If bidder loses, they pay BOTH defenders, so bidder gets -2 * (Val*Mult), defenders get +(Val*Mult).

    let deltaUnit = baseBidValue * multiplier

    if (bidSuccessful) {
        scores[bidWinnerId].moneyDelta = deltaUnit * 2
        scores[defendersIds[0]].moneyDelta = -deltaUnit
        scores[defendersIds[1]].moneyDelta = -deltaUnit
    } else {
        scores[bidWinnerId].moneyDelta = -deltaUnit * 2
        scores[defendersIds[0]].moneyDelta = deltaUnit
        scores[defendersIds[1]].moneyDelta = deltaUnit
    }

    return {
        bid: currentBid,
        trumpSuit,
        bidWinnerId,
        defendersIds,
        scores,
        baseBidValue,
        multiplier,
        bidSuccessful
    }
}
