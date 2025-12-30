import React, { useState } from 'react';
import { useGame } from '../context/GameContext';
import { cn } from '../lib/utils';
import { Clock, Zap, Skull, Check } from 'lucide-react';

const Card = ({ card, onClick, selectable, selected }) => {
    const isTime = card.type === 'time_bonus';
    const isCurse = card.type === 'curse';

    // Determine color based on time or type
    let bgClass = "bg-white text-black";
    if (isCurse) bgClass = "bg-gray-900 border-2 border-red-600 text-red-500";
    else if (isTime) {
        if (card.name.includes("Red")) bgClass = "bg-red-500 text-white";
        else if (card.name.includes("Orange")) bgClass = "bg-orange-500 text-white";
        else if (card.name.includes("Yellow")) bgClass = "bg-yellow-400 text-black";
        else if (card.name.includes("Green")) bgClass = "bg-green-500 text-white";
        else if (card.name.includes("Blue")) bgClass = "bg-blue-600 text-white";
    }
    else {
        // Powerups
        bgClass = "bg-purple-600 text-white";
    }

    return (
        <div
            onClick={selectable ? onClick : undefined}
            className={cn(
                "relative rounded-xl p-4 aspect-[2/3] flex flex-col justify-between shadow-lg transition-all",
                bgClass,
                selectable && "cursor-pointer hover:scale-105 hover:shadow-xl",
                selected && "ring-4 ring-white scale-105"
            )}
        >
            <div className="flex justify-between items-start">
                <span className="text-[10px] font-bold uppercase tracking-widest border border-current px-1.5 py-0.5 rounded opacity-70">
                    {card.type.replace('_', ' ')}
                </span>
                {isTime && <Clock size={16} />}
                {isCurse && <Skull size={16} />}
                {!isTime && !isCurse && <Zap size={16} />}
            </div>

            <div className="text-center">
                <h3 className="text-xl font-black leading-tight uppercase mb-1">
                    {card.name.replace('Time Bonus', '')}
                </h3>
            </div>

            <div className="text-xs font-medium opacity-90 leading-snug">
                {card.description}
            </div>

            {selected && (
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center rounded-xl">
                    <Check size={48} className="text-white drop-shadow-lg" />
                </div>
            )}
        </div>
    );
};

export const DeckView = () => {
    const { hiderState, draftCards, commitDraft } = useGame();
    const [selectedDraft, setSelectedDraft] = useState(null);

    const handleDraw = () => {
        draftCards(3);
    };

    const handleConfirmDraft = () => {
        if (selectedDraft) {
            commitDraft(selectedDraft);
            setSelectedDraft(null);
        }
    };

    if (hiderState.draft && hiderState.draft.length > 0) {
        return (
            <div className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center p-6">
                <h2 className="text-3xl font-black text-white mb-2">CHOOSE ONE</h2>
                <p className="text-gray-400 mb-8">The others will be discarded.</p>

                <div className="grid grid-cols-3 gap-4 w-full max-w-4xl mb-8">
                    {hiderState.draft.map((card, i) => (
                        <Card
                            key={i}
                            card={card}
                            selectable
                            selected={selectedDraft?.id === card.id}
                            onClick={() => setSelectedDraft(card)}
                        />
                    ))}
                </div>

                <button
                    disabled={!selectedDraft}
                    onClick={handleConfirmDraft}
                    className="bg-jetlag text-black font-black py-4 px-12 rounded-full text-xl disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform"
                >
                    CONFIRM SELECTION
                </button>
            </div>
        );
    }

    return (
        <div className="p-8 h-full overflow-y-auto">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white">My Hand</h1>
                    <div className="text-sm text-gray-400 mt-1">
                        Deck: {hiderState.deck.length} | Discard: {hiderState.discard.length}
                    </div>
                </div>
                <button
                    onClick={handleDraw}
                    className="bg-jetlag hover:bg-jetlag-light text-black font-black py-3 px-6 rounded-lg shadow-lg flex items-center gap-2 transition-transform active:scale-95"
                >
                    <Zap size={20} />
                    DRAW 3
                </button>
            </header>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
                {hiderState.hand.length === 0 ? (
                    <div className="col-span-full py-20 text-center text-gray-600 border-2 border-dashed border-gray-800 rounded-xl">
                        Your hand is empty.
                    </div>
                ) : (
                    hiderState.hand.map((card, i) => (
                        <Card key={i} card={card} />
                    ))
                )}
            </div>
        </div>
    );
};
