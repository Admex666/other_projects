import React, { useState } from 'react';
import { useGame } from '../context/GameContext';
import { useNavigate } from 'react-router-dom';
import { Ghost, Search, CheckCircle2, UserCheck } from 'lucide-react';
import { cn } from '../lib/utils';

export const Lobby = () => {
    const { gameState, joinGame, role, startGame } = useGame();
    // No navigate on click anymore, we want them to stay in lobby until game starts or they explore specific views via sidebar

    const handleJoin = (selectedRole) => {
        if (!gameState.status || gameState.status === 'lobby') {
            joinGame(selectedRole);
        }
    };

    // If game is playing, show status
    if (gameState.status === 'playing' && role) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
                <h1 className="text-4xl font-black text-jetlag mb-4">GAME IN PROGRESS</h1>
                <p className="text-gray-400 mb-8 max-w-md">
                    Good luck, <span className="capitalize font-bold text-white">{role}</span>! Use the sidebar tools to play.
                </p>
                <div className="p-6 bg-gray-900 rounded-xl max-w-md w-full text-left border border-gray-800">
                    <h3 className="text-lg font-bold text-white mb-4 uppercase tracking-wider border-b border-gray-700 pb-2">Current Objectives</h3>
                    <ul className="space-y-3 text-gray-300">
                        {role === 'hider' ? (
                            <>
                                <li className="flex items-start gap-2">
                                    <span className="text-jetlag mt-1">●</span>
                                    <span>Stay hidden from the Seekers.</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-jetlag mt-1">●</span>
                                    <span>Draw cards to gain advantages.</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-jetlag mt-1">●</span>
                                    <span>Wait for Seekers to ask questions.</span>
                                </li>
                            </>
                        ) : (
                            <>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-500 mt-1">●</span>
                                    <span>Find the Hider's exact location!</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-500 mt-1">●</span>
                                    <span>Use Investigation tools (Radar, Thermometer, etc).</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-blue-500 mt-1">●</span>
                                    <span>Narrow down the location on The Grid.</span>
                                </li>
                            </>
                        )}
                    </ul>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-full p-8 overflow-y-auto">
            <h1 className="text-5xl font-black text-white mb-2 uppercase tracking-tight">Lobby</h1>
            <p className="text-gray-400 mb-12 text-xl">Choose your side to begin.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
                {/* Hider Selection */}
                <button
                    onClick={() => handleJoin('hider')}
                    disabled={gameState.hiderId && gameState.hiderId !== 'me' && role !== 'hider'}
                    className={cn(
                        "group relative p-8 rounded-3xl border-2 transition-all duration-300 overflow-hidden text-left h-80 flex flex-col justify-between",
                        role === 'hider'
                            ? "bg-jetlag border-jetlag text-black scale-[1.02] shadow-[0_0_40px_rgba(230,185,30,0.3)]"
                            : gameState.hiderId && gameState.hiderId !== 'me'
                                ? "bg-gray-900 border-gray-800 opacity-50 cursor-not-allowed"
                                : "bg-gray-900 border-gray-800 hover:border-jetlag/50 hover:bg-gray-800/80 text-white"
                    )}
                >
                    <div className="relative z-10 w-full">
                        <div className="flex justify-between items-start mb-4">
                            <span className="text-xs font-bold uppercase tracking-widest opacity-60">Role</span>
                            {gameState.hiderId && (
                                <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded">TAKEN</span>
                            )}
                        </div>
                        <h2 className="text-4xl font-black italic mb-2">THE HIDER</h2>
                        <p className={cn("text-sm", role === 'hider' ? "text-black/80" : "text-gray-400")}>
                            Evade the seekers, manage your deck, and stay hidden until time runs out.
                        </p>
                    </div>
                    {role === 'hider' && (
                        <div className="absolute bottom-4 right-4 bg-black/20 p-2 rounded-full">
                            <UserCheck size={24} />
                        </div>
                    )}
                </button>

                {/* Seeker Selection */}
                <button
                    onClick={() => handleJoin('seeker')}
                    className={cn(
                        "group relative p-8 rounded-3xl border-2 transition-all duration-300 overflow-hidden text-left h-80 flex flex-col justify-between",
                        role === 'seeker'
                            ? "bg-blue-600 border-blue-500 text-white scale-[1.02] shadow-[0_0_40px_rgba(37,99,235,0.3)]"
                            : "bg-gray-900 border-gray-800 hover:border-blue-500/50 hover:bg-gray-800/80 text-white"
                    )}
                >
                    <div className="relative z-10 w-full">
                        <div className="flex justify-between items-start mb-4">
                            <span className="text-xs font-bold uppercase tracking-widest opacity-60">Role</span>
                            <span className="text-xs font-bold opacity-60">{gameState.seekers.length} Joined</span>
                        </div>
                        <h2 className="text-4xl font-black italic mb-2">THE SEEKERS</h2>
                        <p className={cn("text-sm", role === 'seeker' ? "text-white/80" : "text-gray-400")}>
                            Investigate the grid, ask questions, and pinpoint the hider's location.
                        </p>
                    </div>
                    {role === 'seeker' && (
                        <div className="absolute bottom-4 right-4 bg-black/20 p-2 rounded-full">
                            <UserCheck size={24} />
                        </div>
                    )}
                </button>
            </div>

            {/* Start Game Action */}
            {role === 'hider' && gameState.status === 'lobby' && (
                <div className="mt-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <button
                        onClick={startGame}
                        className="bg-white text-black font-black text-2xl py-4 px-16 rounded-full shadow-2xl hover:scale-105 hover:bg-gray-100 transition-all flex items-center gap-4"
                    >
                        START GAME
                        <CheckCircle2 size={32} className="text-green-600" />
                    </button>
                    <p className="text-center text-gray-500 mt-4 text-sm">
                        Make sure you have set a hiding spot on "The Grid" first!
                    </p>
                </div>
            )}

            {role === 'seeker' && gameState.status === 'lobby' && (
                <div className="mt-12 text-gray-500 animate-pulse">
                    Waiting for Hider to start the game...
                </div>
            )}
        </div>
    );
};
