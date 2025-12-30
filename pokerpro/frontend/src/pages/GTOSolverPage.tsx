import { useState } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { gtoService, SolverResult } from '../services/gto';
import PlayingCard from '../components/PlayingCard';
import CardSelector from '../components/CardSelector';

export default function GTOSolverPage() {
    const [heroCard1, setHeroCard1] = useState('');
    const [heroCard2, setHeroCard2] = useState('');
    const [boardCards, setBoardCards] = useState<string[]>(['', '', '', '', '']); // Initialize with 5 empty slots for board

    // Selectors state
    const [selectingFor, setSelectingFor] = useState<'hero1' | 'hero2' | 'board' | null>(null);
    const [boardIndex, setBoardIndex] = useState<number>(-1);

    const [trainingMode, setTrainingMode] = useState(false);
    const [trainingAnswer, setTrainingAnswer] = useState<string | null>(null);
    const [showExplanation, setShowExplanation] = useState(false);


    const [villains, setVillains] = useState(1);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<SolverResult | null>(null);
    const [error, setError] = useState('');

    const openSelector = (target: 'hero1' | 'hero2' | 'board', index: number = -1) => {
        setSelectingFor(target);
        setBoardIndex(index);
    };

    const handleCardSelect = (card: string) => {
        if (selectingFor === 'hero1') setHeroCard1(card);
        else if (selectingFor === 'hero2') setHeroCard2(card);
        else if (selectingFor === 'board' && boardIndex !== -1) {
            const newBoard = [...boardCards];
            newBoard[boardIndex] = card;
            setBoardCards(newBoard);
        }
        setSelectingFor(null);
    };

    // Derived full strings for API
    const getHeroHandStr = () => (heroCard1 && heroCard2) ? heroCard1 + heroCard2 : '';
    const getBoardStr = () => boardCards.filter(c => !!c).join('');

    // Unavailable cards logic
    const unavailable = [heroCard1, heroCard2, ...boardCards].filter(c => !!c);


    // Drill State
    const [drillType, setDrillType] = useState('btn_vs_bb_srp');
    const [drillDesc, setDrillDesc] = useState('');

    const [potSize, setPotSize] = useState<number>(10);
    const [stackSize, setStackSize] = useState<number>(100);
    const [facingBet, setFacingBet] = useState<number>(0);

    const solveInternal = async (hHand: string, bStr: string, vs: number, p: number = 10, s: number = 100, fb: number = 0) => {
        setLoading(true);
        setError('');
        setResult(null);
        setTrainingAnswer(null);
        setShowExplanation(false);

        try {
            const data = await gtoService.solveSpot({
                hero_hand: hHand,
                board: bStr,
                villains: vs,
                pot: p,
                stack: s,
                facing_bet: fb
            });
            if ((data as any).error) {
                setError((data as any).error);
            } else {
                setResult(data);
            }
        } catch (err: any) {
            setError(err.response?.data?.message || 'Failed to solve spot');
        } finally {
            setLoading(false);
        }
    };

    const handleTrainingGuess = (action: string) => {
        if (!result) return;
        setTrainingAnswer(action);
        setShowExplanation(true);
    };

    const histogramData = result?.details?.equity_histogram?.map((val: number, index: number) => ({
        name: `${index * 10}-${(index + 1) * 10}%`,
        value: val * 100
    })) || [];

    const handleSolve = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        const hHand = getHeroHandStr();
        if (hHand.length !== 4) {
            setError('Please select exactly 2 cards for Hero.');
            return;
        }
        await solveInternal(hHand, getBoardStr(), villains, potSize, stackSize, facingBet);
    };

    const handleRandomSpot = async () => {
        setLoading(true);
        try {
            const drill = await gtoService.getDrill(drillType);

            // Parse board (e.g. "AhKs2d" -> ["Ah", "Ks", "2d", "", ""])
            const bCards = ['', '', '', '', ''];
            if (drill.board.length % 2 === 0) {
                for (let i = 0; i < drill.board.length / 2; i++) {
                    bCards[i] = drill.board.slice(i * 2, i * 2 + 2);
                }
            }

            setHeroCard1(drill.hero_hand.slice(0, 2));
            setHeroCard2(drill.hero_hand.slice(2, 4));
            setBoardCards(bCards);

            setPotSize(drill.pot);
            setStackSize(drill.stack);
            setFacingBet(drill.facing_bet);
            setDrillDesc(drill.description);
            setVillains(drill.villains);

            setResult(null);

            // Auto-solve
            await solveInternal(drill.hero_hand, drill.board, drill.villains, drill.pot, drill.stack, drill.facing_bet);

        } catch (err) {
            console.error(err);
            setError("Failed to generate drill");
            setLoading(false);
        }
    };

    const getActionColor = (action: string) => {
        switch (action) {
            case 'BET': return '#ef4444'; // Red-500
            case 'RAISE': return '#ef4444';
            case 'CHECK': return '#22c55e'; // Green-500
            case 'CALL': return '#22c55e';
            case 'FOLD': return '#3b82f6'; // Blue-500
            default: return '#9ca3af';
        }
    };

    // Helper to render board slot
    const renderBoardSlot = (index: number) => {
        const card = boardCards[index] || '';
        return (
            <PlayingCard
                key={`board-${index}`}
                card={card}
                onClick={() => openSelector('board', index)}
                size="md"
            />
        );
    };

    // Calculate Feedback
    const getFeedback = () => {
        if (!result || !trainingAnswer) return null;

        // Check if we have EV data
        if (result.evs) {
            const userEv = result.evs[trainingAnswer] || -999;
            const maxEv = Math.max(...Object.values(result.evs).filter(v => v > -900)); // Filter out invalid
            const diff = maxEv - userEv;

            const isCorrect = diff < 0.5; // Tolerance
            const isBlunder = diff > 2.0; // Big mistake

            return {
                isCorrect,
                title: isCorrect ? "Excellent!" : isBlunder ? "Blunder!" : "Inaccuracy",
                msg: isCorrect
                    ? `You captured ${userEv.toFixed(1)} EV.`
                    : `You lost ${diff.toFixed(1)} BB in EV compared to the optimal line.`,
                color: isCorrect ? "green" : isBlunder ? "red" : "yellow"
            };
        }

        // Fallback to simple matching
        const correct = trainingAnswer === result.recommended_action || (result.recommended_action === 'RAISE' && trainingAnswer === 'BET') || (result.recommended_action === 'CALL' && trainingAnswer === 'CHECK');
        return {
            isCorrect: correct,
            title: correct ? "Correct!" : "Mistake",
            msg: correct ? "You followed the solver's preferred line." : `The solver prefers ${result.recommended_action}.`,
            color: correct ? "green" : "red"
        };
    };

    const feedback = getFeedback();

    return (
        <div className="min-h-screen bg-gray-900 text-white relative">
            <CardSelector isOpen={!!selectingFor} onClose={() => setSelectingFor(null)} onSelect={handleCardSelect} unavailableCards={unavailable} />

            <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link to="/dashboard" className="text-gray-400 hover:text-white transition-colors">← Back</Link>
                        <h1 className="text-xl font-bold">QuickGTO Solver</h1>
                    </div>

                    {/* Training Toggle */}
                    <div className="flex items-center bg-gray-900 rounded-lg p-1 border border-gray-700">
                        <button
                            onClick={() => { setTrainingMode(false); setTrainingAnswer(null); setShowExplanation(false); }}
                            className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${!trainingMode ? 'bg-gray-700 text-white shadow' : 'text-gray-400 hover:text-gray-200'}`}
                        >
                            Solver
                        </button>
                        <button
                            onClick={() => { setTrainingMode(true); setTrainingAnswer(null); setShowExplanation(false); }}
                            className={`px-4 py-1.5 rounded-md text-sm font-bold transition-all ${trainingMode ? 'bg-poker-gold text-gray-900 shadow' : 'text-gray-400 hover:text-gray-200'}`}
                        >
                            Training
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8 pb-32">
                {/* Main Table View */}
                <div className={`bg-gray-800 rounded-3xl p-8 mb-8 border-[12px] border-gray-900 shadow-2xl relative overflow-hidden transition-all duration-500 ${trainingMode ? 'ring-4 ring-poker-gold/30' : ''}`}
                    style={{
                        background: 'radial-gradient(circle, #064e3b 0%, #064e3b 40%, #022c22 100%)',
                        boxShadow: 'inset 0 0 100px rgba(0,0,0,0.5)'
                    }}>

                    {/* ... (Table content same as before) */}

                    <div className="relative z-10 flex flex-col items-center gap-12">
                        {/* Board & Hero Cards (Same as before) */}
                        <div className="flex flex-col items-center gap-4">
                            <span className="text-green-100/50 uppercase tracking-widest text-sm font-bold">Community Cards</span>
                            <div className="flex gap-3 bg-black/20 p-4 rounded-xl backdrop-blur-sm border border-white/10">
                                {renderBoardSlot(0)} {renderBoardSlot(1)} {renderBoardSlot(2)}
                                <div className="w-2" /> {renderBoardSlot(3)} <div className="w-2" /> {renderBoardSlot(4)}
                            </div>
                        </div>

                        {/* Scenario Info (Training Mode) */}
                        {trainingMode && (
                            <div className="flex flex-col items-center gap-2">
                                {drillDesc && (
                                    <div className="text-poker-gold font-bold uppercase tracking-wider text-xs bg-poker-gold/10 px-3 py-1 rounded-full border border-poker-gold/20">
                                        {drillDesc}
                                    </div>
                                )}
                                <div className="flex gap-6 text-sm font-mono bg-black/40 px-6 py-2 rounded-full border border-white/10">
                                    <div className="flex flex-col items-center">
                                        <span className="text-gray-400 text-xs">POT</span>
                                        <span className="text-poker-gold font-bold">{potSize} BB</span>
                                    </div>
                                    <div className="w-px bg-white/10" />
                                    <div className="flex flex-col items-center">
                                        <span className="text-gray-400 text-xs">STACK</span>
                                        <span className="text-white font-bold">{stackSize} BB</span>
                                    </div>
                                    <div className="w-px bg-white/10" />
                                    <div className="flex flex-col items-center">
                                        <span className="text-gray-400 text-xs">FACING</span>
                                        <span className={`${facingBet > 0 ? 'text-red-400' : 'text-gray-300'} font-bold`}>{facingBet > 0 ? `BET ${facingBet} BB` : 'CHECK'}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="flex flex-col items-center gap-4">
                            <span className="text-green-100/50 uppercase tracking-widest text-sm font-bold">Hero Hand</span>
                            <div className="flex gap-4 p-4 rounded-xl border-2 border-dashed border-white/10 hover:border-white/30 transition-colors">
                                <PlayingCard card={heroCard1} size="lg" onClick={() => openSelector('hero1')} />
                                <PlayingCard card={heroCard2} size="lg" onClick={() => openSelector('hero2')} />
                            </div>
                        </div>

                        {/* Controls / Quiz Area */}
                        <div className="flex gap-6 items-center bg-gray-900/90 p-4 rounded-2xl border border-gray-700 shadow-xl backdrop-blur-md min-w-[300px] justify-center">

                            {!result && (
                                <>
                                    <div className="flex items-center gap-3">
                                        <span className="text-xs text-gray-400 uppercase font-bold">Villains</span>
                                        <div className="flex items-center bg-gray-800 rounded-lg border border-gray-700">
                                            <button onClick={() => setVillains(Math.max(1, villains - 1))} className="px-3 py-1 hover:bg-gray-700 text-gray-300">-</button>
                                            <span className="px-3 py-1 font-mono">{villains}</span>
                                            <button onClick={() => setVillains(Math.min(9, villains + 1))} className="px-3 py-1 hover:bg-gray-700 text-gray-300">+</button>
                                        </div>
                                    </div>
                                    <div className="w-px h-8 bg-gray-700" />

                                    {!trainingMode ? (
                                        <button
                                            onClick={() => handleSolve()}
                                            disabled={loading}
                                            className={`px-8 py-2 rounded-lg font-bold text-lg shadow-lg transform transition-all active:scale-95
                                                ${loading ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 'bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-400 hover:to-yellow-500 text-gray-900 border-b-4 border-yellow-800 hover:border-yellow-700'}
                                            `}
                                        >
                                            {loading ? 'CALCULATING...' : 'SOLVE SPOT'}
                                        </button>
                                    ) : (
                                        <div className="flex flex-col gap-2">
                                            <select
                                                value={drillType}
                                                onChange={(e) => setDrillType(e.target.value)}
                                                className="bg-gray-800 text-gray-200 border border-gray-600 rounded px-2 py-1 text-xs font-bold focus:ring-1 focus:ring-purple-500 outline-none w-full mb-1"
                                            >
                                                <option value="random">🎲 Pure Random</option>
                                                <option value="btn_vs_bb_srp">🔘 BTN vs BB (SRP)</option>
                                                <option value="sb_vs_bb_limp">⚔️ SB vs BB (Limp)</option>
                                                <option value="3bet_pot_oop">💥 3-Bet Pot (OOP)</option>
                                            </select>
                                            <button
                                                onClick={() => handleRandomSpot()}
                                                disabled={loading}
                                                className="px-8 py-2 rounded-lg font-bold text-lg shadow-lg transform transition-all active:scale-95 bg-purple-600 hover:bg-purple-500 text-white border-b-4 border-purple-800 hover:border-purple-700 flex items-center justify-center gap-2"
                                            >
                                                <span>🚀</span> {loading ? 'DEALING...' : 'START DRILL'}
                                            </button>
                                        </div>
                                    )}

                                    <button onClick={() => { setHeroCard1(''); setHeroCard2(''); setBoardCards(['', '', '', '', '']); setBoardIndex(-1); setResult(null); setError(''); }} className="text-xs text-gray-500 hover:text-gray-300 underline">Clear</button>
                                </>
                            )}

                            {result && trainingMode && !trainingAnswer && (
                                <div className="flex flex-col gap-4 animate-fade-in w-full max-w-md">
                                    <div className="text-white font-bold text-center text-sm uppercase tracking-widest text-gray-400">Choose Action</div>

                                    <div className="grid grid-cols-2 gap-3">
                                        {/* FOLD / CHECK-CALL Group */}
                                        <div className="flex flex-col gap-2">
                                            {facingBet > 0 && (
                                                <button onClick={() => handleTrainingGuess('FOLD')} className="btn-action bg-blue-600 hover:bg-blue-500 py-3 rounded-lg font-bold shadow-lg border-b-4 border-blue-800 active:border-b-0 active:translate-y-1">FOLD</button>
                                            )}
                                            <button onClick={() => handleTrainingGuess(facingBet > 0 ? 'CALL' : 'CHECK')} className="btn-action bg-green-600 hover:bg-green-500 py-3 rounded-lg font-bold shadow-lg border-b-4 border-green-800 active:border-b-0 active:translate-y-1">
                                                {facingBet > 0 ? 'CALL' : 'CHECK'}
                                            </button>
                                        </div>

                                        {/* AGGRESSION Group */}
                                        <div className="grid grid-cols-2 gap-2">
                                            <button onClick={() => handleTrainingGuess(facingBet > 0 ? 'RAISE_SMALL' : 'BET_SMALL')} className="bg-red-500 hover:bg-red-400 text-white font-bold text-xs rounded shadow border-b-2 border-red-700 active:border-b-0 active:translate-y-0.5">
                                                SMALL (33%)
                                            </button>
                                            <button onClick={() => handleTrainingGuess(facingBet > 0 ? 'RAISE_POT' : 'BET_POT')} className="bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded shadow border-b-2 border-red-800 active:border-b-0 active:translate-y-0.5">
                                                POT (100%)
                                            </button>
                                            <button onClick={() => handleTrainingGuess(facingBet > 0 ? 'RAISE_BIG' : 'BET_BIG')} className="bg-red-700 hover:bg-red-600 text-white font-bold text-xs rounded shadow border-b-2 border-red-900 active:border-b-0 active:translate-y-0.5">
                                                BIG (200%)
                                            </button>
                                            <button onClick={() => handleTrainingGuess(facingBet > 0 ? 'RAISE_ALLIN' : 'BET_ALLIN')} className="bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded shadow border-b-2 border-purple-800 active:border-b-0 active:translate-y-0.5">
                                                ALL-IN
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {result && (!trainingMode || trainingAnswer) && (
                                <div className="flex items-center gap-4 animate-fade-in">
                                    <button
                                        onClick={() => { setResult(null); setTrainingAnswer(null); setShowExplanation(false); }}
                                        className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-bold text-white transition-colors"
                                    >
                                        New Hand
                                    </button>
                                </div>
                            )}
                        </div>

                        {error && <div className="bg-red-500/90 text-white px-6 py-2 rounded-full font-bold animate-bounce shadow-lg">⚠️ {error}</div>}
                    </div>
                </div>

                {/* Training Feedback & Explanation */}
                {result && showExplanation && trainingMode && feedback && (
                    <div className={`mb-8 p-6 rounded-2xl border-l-8 shadow-xl animate-slide-up ${feedback.color === 'green' ? 'bg-green-900/40 border-green-500' :
                        feedback.color === 'red' ? 'bg-red-900/40 border-red-500' :
                            'bg-yellow-900/40 border-yellow-500'
                        }`}>
                        <div className="flex items-start gap-4">
                            <div className="text-4xl">
                                {feedback.isCorrect ? '🎉' : '❌'}
                            </div>
                            <div>
                                <h3 className={`text-xl font-bold mb-2 ${feedback.color === 'green' ? 'text-green-400' :
                                    feedback.color === 'red' ? 'text-red-400' : 'text-yellow-400'
                                    }`}>
                                    {feedback.title}
                                </h3>
                                <p className="text-white font-bold text-lg mb-2">
                                    {feedback.msg}
                                </p>
                                <p className="text-gray-300 text-lg leading-relaxed">
                                    {result.explanation}
                                </p>
                            </div>
                        </div>
                    </div>
                )}


                {/* Detailed Results (Show if not in training mode OR if question answered) */}
                {result && (!trainingMode || showExplanation) && (
                    <div className="space-y-6 animate-fade-in">
                        {/* Top Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 text-center">
                                <div className="text-gray-400 text-sm mb-1">Equity</div>
                                <div className="text-3xl font-bold text-poker-gold">{(result.equity * 100).toFixed(1)}%</div>
                            </div>
                            <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 text-center">
                                <div className="text-gray-400 text-sm mb-1">GTO Action</div>
                                <div className={`text-3xl font-bold`} style={{ color: getActionColor(result.recommended_action) }}>
                                    {result.recommended_action}
                                </div>
                            </div>
                            {result.explanation && !trainingMode && (
                                <div className="bg-gray-800 p-5 rounded-xl border border-gray-700 col-span-1 md:col-span-1 text-left flex flex-col justify-center">
                                    <div className="text-xs text-gray-500 uppercase font-bold mb-1">Analysis</div>
                                    <p className="text-sm text-gray-300 leading-snug">{result.explanation}</p>
                                </div>
                            )}
                        </div>

                        {/* Strategy Bars */}
                        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                            <h3 className="text-lg font-bold mb-4">Optimal Strategy</h3>
                            <div className="space-y-4">
                                {Object.entries(result.strategy).map(([action, freq]) => (
                                    <div key={action}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="font-medium">{action}</span>
                                            <span>{(freq * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="h-4 bg-gray-700 rounded-full overflow-hidden">
                                            <div className="h-full transition-all duration-500" style={{ width: `${freq * 100}%`, backgroundColor: getActionColor(action) }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Histogram */}
                        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                            <h3 className="text-lg font-bold mb-4">Equity Distribution</h3>
                            <div className="h-64 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={histogramData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                        <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tick={{ fill: '#9ca3af' }} />
                                        <YAxis stroke="#9ca3af" fontSize={12} tick={{ fill: '#9ca3af' }} unit="%" />
                                        <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }} itemStyle={{ color: '#fbbf24' }} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                                        <Bar dataKey="value" fill="#fbbf24" radius={[4, 4, 0, 0]}>
                                            {histogramData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.value > 20 ? '#fbbf24' : '#d97706'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty State / Intro */}
                {!result && !loading && (
                    <div className="mt-8 text-center text-gray-500">
                        <p className="text-lg">Select your cards and board to {trainingMode ? 'start a training drill.' : 'analyze the spot.'}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

