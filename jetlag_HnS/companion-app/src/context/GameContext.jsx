import React, { createContext, useContext, useState, useEffect } from 'react';
import { db } from '../firebase';
import deckData from '../data/deck.json';
import questionsData from '../data/questions.json';
import stationsData from '../data/stations.json';
import { getDistance } from 'geolib';

const GameContext = createContext();

export const useGame = () => useContext(GameContext);

export const GameProvider = ({ children }) => {
    const [gameState, setGameState] = useState({
        status: 'lobby', // 'lobby' | 'playing' | 'ended'
        hiderId: null,
        seekers: [],
        round: 1,
        feed: [], // Unified chat and logs
        previewData: null, // For map previews { type: 'Radar'|'Thermometer', center, radius: number | number[] }
    });
    const [role, setRole] = useState(null); // 'hider' | 'seeker'

    // Questions Data
    const questions = questionsData;

    // Hider Specific State
    const [hiderState, setHiderState] = useState({
        drawPool: 3,
        hand: [],
        discard: [],
        deck: [...deckData],
        draft: [],
        hidingSpot: null // { id, name, lat, lng }
    });

    const setPreview = (data) => {
        setGameState(prev => ({ ...prev, previewData: data }));
    };

    const shuffleDeck = () => {
        let newDeck = [...deckData];
        for (let i = newDeck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [newDeck[i], newDeck[j]] = [newDeck[j], newDeck[i]];
        }
        setHiderState(prev => ({ ...prev, deck: newDeck, hand: [], discard: [], draft: [] }));
    };

    const drawCards = (count) => {
        setHiderState(prev => {
            const cardsToDraw = prev.deck.slice(0, count);
            const remainingDeck = prev.deck.slice(count);
            return {
                ...prev,
                hand: [...prev.hand, ...cardsToDraw],
                deck: remainingDeck,
            };
        });
    };

    const draftCards = (count) => {
        setHiderState(prev => {
            const cardsDrafted = prev.deck.slice(0, count);
            const remainingDeck = prev.deck.slice(count);
            return {
                ...prev,
                draft: cardsDrafted,
                deck: remainingDeck,
            };
        });
    };

    const commitDraft = (keptCard) => {
        setHiderState(prev => {
            const others = prev.draft.filter(c => c.id !== keptCard.id);
            return {
                ...prev,
                hand: [...prev.hand, keptCard],
                discard: [...prev.discard, ...others],
                draft: [],
            };
        });
    };

    const claimHidingSpot = (station) => {
        if (gameState.status === 'playing') return; // Cannot change hiding spot once game started
        setHiderState(prev => ({ ...prev, hidingSpot: station }));

        const newLog = {
            id: Date.now(),
            type: 'event',
            role: 'hider',
            text: `Hider has selected a starting location.`,
            timestamp: new Date().toISOString()
        };

        setGameState(prev => ({
            ...prev,
            feed: [newLog, ...prev.feed]
        }));
    };

    const joinGame = (newRole) => {
        if (gameState.status === 'playing') {
            console.warn("Game already started!");
            return;
        }
        setRole(newRole);
        if (newRole === 'hider') {
            shuffleDeck();
            setGameState(prev => ({ ...prev, hiderId: 'me' }));
        } else {
            setGameState(prev => ({ ...prev, seekers: [...prev.seekers, 'me'] }));
        }
    };

    const startGame = () => {
        if (!hiderState.hidingSpot) {
            alert("Hider must set a hiding spot first!");
            return;
        }
        setGameState(prev => ({
            ...prev,
            status: 'playing',
            feed: [{
                id: Date.now(),
                type: 'event',
                role: 'system',
                text: 'GAME STARTED! Good luck.',
                timestamp: new Date().toISOString()
            }, ...prev.feed]
        }));
    };

    const endGame = (winner) => {
        setGameState(prev => ({
            ...prev,
            status: 'ended',
            feed: [{
                id: Date.now(),
                type: 'event',
                role: 'system',
                text: `GAME OVER! Winner: ${winner}`,
                timestamp: new Date().toISOString()
            }, ...prev.feed]
        }));
    };

    const calculateAnswer = (question, params, hiderLoc, seekerLoc) => {
        if (!hiderLoc) return "Hider location not set.";

        const hiderCoords = { latitude: hiderLoc.lat, longitude: hiderLoc.lng };

        if (question.type === 'Radar') {
            let rangeMeters = 1000;
            const opt = params.option;
            if (opt.includes('0.25mi')) rangeMeters = 402;
            else if (opt.includes('0.50mi')) rangeMeters = 805;
            else if (opt.includes('1mi')) rangeMeters = 1609;
            else if (opt.includes('3mi')) rangeMeters = 4828;
            else if (opt.includes('5mi')) rangeMeters = 8046;
            else if (opt.includes('10mi')) rangeMeters = 16093;

            if (!seekerLoc) return "Seeker location unknown";
            const seekerCoords = { latitude: seekerLoc.lat, longitude: seekerLoc.lng };

            const dist = getDistance(hiderCoords, seekerCoords);
            const isInside = dist <= rangeMeters;
            return isInside ? "YES (Inside Range)" : "NO (Outside Range)";
        }

        if (question.type === 'Thermometer') {
            if (!seekerLoc) return "Seeker location unknown";
            const seekerCoords = { latitude: seekerLoc.lat, longitude: seekerLoc.lng };
            const dist = getDistance(hiderCoords, seekerCoords);

            if (dist <= 500) return "BOILING (Within 500m)";
            if (dist <= 2000) return "HOT (Within 2km)";
            if (dist <= 5000) return "WARM (Within 5km)";
            return "COLD (More than 5km away)";
        }

        if (question.type === 'Matching' && params.station) {
            const targetStation = params.station;
            const dist = getDistance(hiderCoords, { latitude: targetStation.lat, longitude: targetStation.lng });
            // In Hide + Seek, "Is this your nearest station?"
            // We'd need to check ALL stations to be 100% accurate, but for now let's just use the distance.
            // Simplified: "Are you within 1km of this station?"
            return dist <= 1000 ? "YES (Within 1km)" : "NO (Further than 1km)";
        }

        return "PENDING (Manual Hider Response)";
    };

    const submitQuestion = (question, params, seekerLoc) => {
        const answer = calculateAnswer(question, params, hiderState.hidingSpot, seekerLoc);

        const newLog = {
            id: Date.now(),
            type: 'question',
            role: seekerLoc ? 'seeker' : 'system',
            text: `Asked ${question.type} ${params.option || params.station?.name || ''}`,
            answer: answer,
            timestamp: new Date().toISOString()
        };

        setGameState(prev => ({
            ...prev,
            feed: [newLog, ...prev.feed],
            previewData: null // Clear preview on ask
        }));

        return { result: "OK", answer };
    };

    const sendChat = (message, imageUrl = null) => {
        const newMsg = {
            id: Date.now(),
            type: 'chat',
            role: role || 'spectator',
            sender: role || "Spectator",
            text: message,
            image: imageUrl,
            timestamp: new Date().toISOString()
        };
        setGameState(prev => ({
            ...prev,
            feed: [newMsg, ...prev.feed]
        }));
    };

    const value = {
        gameState,
        role,
        hiderState,
        joinGame,
        startGame,
        endGame,
        drawCards,
        draftCards,
        commitDraft,
        claimHidingSpot,
        questions,
        submitQuestion,
        sendChat,
        setPreview,
    };

    return (
        <GameContext.Provider value={value}>
            {children}
        </GameContext.Provider>
    );
};
