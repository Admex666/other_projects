
import { useState } from 'react';
import PlayingCard from './PlayingCard';

const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUITS = ['s', 'h', 'd', 'c']; // spades, hearts, diamonds, clubs

interface CardSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (card: string) => void;
    unavailableCards: string[];
}

export default function CardSelector({ isOpen, onClose, onSelect, unavailableCards }: CardSelectorProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-gray-800 rounded-xl shadow-2xl border border-gray-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-4 border-b border-gray-700 flex justify-between items-center sticky top-0 bg-gray-800 z-10">
                    <h3 className="text-xl font-bold text-white">Select a Card</h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white p-2"
                    >
                        ✕
                    </button>
                </div>

                <div className="p-6 grid gap-4">
                    {SUITS.map(suit => (
                        <div key={suit} className="flex flex-wrap gap-2">
                            {RANKS.map(rank => {
                                const cardCode = rank + suit;
                                const isUnavailable = unavailableCards.includes(cardCode);
                                return (
                                    <div key={cardCode} className={isUnavailable ? 'opacity-30 pointer-events-none grayscale' : ''}>
                                        <PlayingCard
                                            card={cardCode}
                                            size="md"
                                            onClick={() => {
                                                if (!isUnavailable) {
                                                    onSelect(cardCode);
                                                }
                                            }}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
