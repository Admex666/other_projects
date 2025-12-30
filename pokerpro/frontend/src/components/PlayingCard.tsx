
import { useState } from 'react';

interface CardProps {
    card: string; // e.g., "Ah", "Td", "2s"
    size?: 'sm' | 'md' | 'lg';
    onClick?: () => void;
    selected?: boolean;
}

const SUIT_COLORS = {
    h: 'text-red-500',
    d: 'text-blue-500', // Four-color deck blue for diamonds
    c: 'text-green-500', // Four-color deck green for clubs
    s: 'text-gray-900', // Black
};

const SUIT_SYMBOLS = {
    h: '♥',
    d: '♦',
    c: '♣',
    s: '♠',
};

export default function PlayingCard({ card, size = 'md', onClick, selected }: CardProps) {
    if (!card || card.length !== 2) {
        return (
            <div
                onClick={onClick}
                className={`
                    ${size === 'lg' ? 'w-24 h-36' : size === 'md' ? 'w-16 h-24' : 'w-10 h-14'}
                    bg-gray-800 border-2 border-dashed border-gray-600 rounded-lg 
                    flex items-center justify-center cursor-pointer hover:border-poker-gold transition-colors
                    ${selected ? 'ring-2 ring-poker-gold border-solid border-poker-gold' : ''}
                `}
            >
                <span className="text-gray-600 text-2xl">+</span>
            </div>
        );
    }

    const rank = card[0];
    const suit = card[1].toLowerCase() as keyof typeof SUIT_COLORS;

    // Size classes
    const containerClasses = size === 'lg' ? 'w-24 h-36 text-4xl' : size === 'md' ? 'w-16 h-24 text-2xl' : 'w-10 h-14 text-sm';
    const cornerClasses = size === 'lg' ? 'text-lg' : size === 'md' ? 'text-sm' : 'text-[0.6rem]';

    return (
        <div
            onClick={onClick}
            className={`
                ${containerClasses}
                relative bg-white rounded-lg shadow-md select-none transform transition-transform hover:-translate-y-1
                flex items-center justify-center font-bold font-serif border border-gray-300
                ${selected ? 'ring-4 ring-poker-gold' : ''}
                ${onClick ? 'cursor-pointer' : ''}
            `}
        >
            {/* Top Left Corner */}
            <div className={`absolute top-1 left-1 flex flex-col items-center leading-none ${cornerClasses} ${SUIT_COLORS[suit]}`}>
                <span>{rank}</span>
                <span>{SUIT_SYMBOLS[suit]}</span>
            </div>

            {/* Center Suit */}
            <div className={`${SUIT_COLORS[suit]}`}>
                {SUIT_SYMBOLS[suit]}
            </div>

            {/* Bottom Right Corner (Rotated) */}
            <div className={`absolute bottom-1 right-1 flex flex-col items-center leading-none transform rotate-180 ${cornerClasses} ${SUIT_COLORS[suit]}`}>
                <span>{rank}</span>
                <span>{SUIT_SYMBOLS[suit]}</span>
            </div>
        </div>
    );
}
