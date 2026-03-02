import React from 'react'
import { useRouter } from 'next/navigation'
import { Game } from '@/store/gameStore'
import { GameResult } from '@/lib/game/scoring'
import { cn } from '@/lib/utils'

interface ScorePanelProps {
    game: Game
    myId: string
    onNextGame?: () => void
}

export function ScorePanel({ game, myId, onNextGame }: ScorePanelProps) {
    const router = useRouter()
    const result: GameResult | undefined = game.state.finalResult

    if (!result) {
        return (
            <div className="bg-slate-900 border-2 border-slate-700 p-8 rounded-3xl text-center text-white">
                <h2 className="text-2xl font-bold mb-4">A játék véget ért!</h2>
                <p className="opacity-70">A pontok kiszámítása folyamatban van...</p>
            </div>
        )
    }

    const myScore = result.scores[myId]
    const isWinner = myScore.moneyDelta > 0

    return (
        <div className="bg-slate-900 text-white border border-slate-700 p-6 sm:p-8 rounded-3xl shadow-2xl max-w-lg w-full mx-auto">
            <div className="text-center mb-6">
                <h2 className={cn("text-3xl font-black mb-2", isWinner ? "text-green-400" : "text-red-400")}>
                    {isWinner ? "🏅 NYERTÉL!" : "💀 VESZTETTÉL"}
                </h2>
                <p className="text-xl font-bold">
                    Egyenleg: <span className={isWinner ? "text-green-400" : "text-red-400"}>
                        {myScore.moneyDelta > 0 ? '+' : ''}{myScore.moneyDelta} Egység
                    </span>
                </p>
            </div>

            <div className="bg-slate-800 rounded-xl p-4 mb-6 text-sm sm:text-base border border-slate-600">
                <h3 className="font-bold text-amber-400 mb-2 border-b border-slate-600 pb-1">Játék Összesítő</h3>
                <div className="flex justify-between mb-1">
                    <span className="opacity-70">Bemondás:</span>
                    <span className="font-bold">{result.bid.name}</span>
                </div>
                <div className="flex justify-between mb-1">
                    <span className="opacity-70">Adu Szín:</span>
                    <span className="font-bold capitalize">{result.trumpSuit || 'Színnélküli'}</span>
                </div>
                <div className="flex justify-between mb-1">
                    <span className="opacity-70">Teljesítve:</span>
                    <span className={cn("font-bold", result.bidSuccessful ? "text-green-400" : "text-red-400")}>
                        {result.bidSuccessful ? 'Igen' : 'Elbukva'}
                    </span>
                </div>
                <div className="flex justify-between font-bold text-red-300 mt-2 pt-2 border-t border-slate-600">
                    <span>Szorzó (Kontrák):</span>
                    <span>{result.multiplier}x</span>
                </div>
            </div>

            <div className="space-y-3 mb-8">
                <h3 className="font-bold text-amber-400 border-b border-slate-600 pb-1">Játékosok Eredménye</h3>
                {Object.values(result.scores).map(score => {
                    const isMe = score.playerId === myId
                    return (
                        <div key={score.playerId} className={cn("flex justify-between p-2 rounded", isMe ? "bg-slate-700 font-bold" : "bg-slate-800/50")}>
                            <div>
                                <span>{isMe ? 'TE' : 'Játékos'} </span>
                                {score.isBidWinner && <span className="text-xs bg-blue-600 px-1 py-0.5 rounded ml-2">Felvevő</span>}
                            </div>
                            <div className="text-right">
                                <span className="opacity-70 text-xs mr-2">{score.totalPoints} Pont</span>
                                <span className={score.moneyDelta > 0 ? "text-green-400" : "text-red-400"}>
                                    {score.moneyDelta > 0 ? '+' : ''}{score.moneyDelta}
                                </span>
                            </div>
                        </div>
                    )
                })}
            </div>

            <div className="flex gap-4">
                <button
                    onClick={() => router.push(`/room/${game.room_id}`)}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition"
                >
                    Vissza a Szobába
                </button>
                {onNextGame && (
                    <button
                        onClick={onNextGame}
                        className="flex-1 bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl transition shadow-lg shadow-green-900/50"
                    >
                        Új Osztás
                    </button>
                )}
            </div>
        </div>
    )
}
