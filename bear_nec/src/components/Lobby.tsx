import React, { useState, useEffect } from 'react';
import { Copy, Check, Play, Globe, Sparkles, Bot } from 'lucide-react';

export interface LobbyProps {
  playerName: string;
  onPlayerNameChange: (name: string) => void;
  onCreateRoom: () => void;
  onJoinRoom: (roomId: string) => void;
  onStartLocalHotseat: () => void;
  onStartBotGame?: (difficulty: 'easy' | 'medium' | 'hard') => void;
  currentRoomId?: string | null;
  isConnecting?: boolean;
  error?: string | null;
}

export const Lobby: React.FC<LobbyProps> = ({
  playerName,
  onPlayerNameChange,
  onCreateRoom,
  onJoinRoom,
  onStartLocalHotseat,
  onStartBotGame,
  currentRoomId,
  isConnecting = false,
  error = null,
}) => {
  const [joinCode, setJoinCode] = useState('');
  const [copied, setCopied] = useState(false);
  const [botDifficulty, setBotDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium');

  // Check URL query parameters for ?room=CODE
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const roomParam = params.get('room');
    if (roomParam && !joinCode) {
      setJoinCode(roomParam.toUpperCase().slice(0, 6));
    }
  }, []);

  const handleCopyLink = () => {
    if (!currentRoomId) return;
    const url = `${window.location.origin}${window.location.pathname}?room=${currentRoomId}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  return (
    <div className="w-full max-w-xl mx-auto px-4 py-8">
      {/* Decorative Wood Frame Box */}
      <div className="wood-panel rounded-3xl p-6 sm:p-8 text-[#3c2a18]">
        {/* Title Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-b from-amber-400 to-amber-600 text-white shadow-lg mb-3 border-2 border-[#fffdf6]">
            <span className="text-3xl">🐻</span>
          </div>
          <h1 className="font-serif font-black text-3xl sm:text-4xl text-[#4e3218] tracking-tight">
            Bear Necessities
          </h1>
          <p className="font-serif text-sm sm:text-base text-stone-600 mt-1 max-w-sm mx-auto">
            A serene woodland tableau-building journey for 2 players.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-3 rounded-xl bg-rose-100 border border-rose-300 text-rose-800 text-xs sm:text-sm font-serif">
            {error}
          </div>
        )}

        {/* Player Name Input */}
        <div className="mb-6">
          <label className="block text-xs font-bold font-serif uppercase tracking-wider text-[#6b4a2c] mb-2">
            Your Explorer Name
          </label>
          <input
            type="text"
            value={playerName}
            onChange={(e) => onPlayerNameChange(e.target.value)}
            placeholder="Enter your name..."
            maxLength={18}
            className="w-full px-4 py-3 rounded-xl bg-white/90 border-2 border-[#6b4a2c]/40 focus:border-amber-600 focus:outline-none font-serif text-base text-[#3c2a18] shadow-inner"
          />
        </div>

        {/* Main Options: Online Multiplayer vs Local Hotseat */}
        <div className="space-y-4">
          {/* 1. Local 2-Player Hotseat Mode (Recommended for testing & single-screen play) */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-emerald-500/80 shadow-md">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-emerald-600 text-white mb-1 shadow-sm">
                  Recommended for Testing
                </span>
                <h3 className="font-serif font-black text-lg text-emerald-950 flex items-center gap-1.5">
                  <Play className="w-4 h-4 text-emerald-600" />
                  Local 2-Player Hotseat Mode
                </h3>
                <p className="font-serif text-xs text-emerald-800/80 mt-0.5">
                  Play the entire 12-round game on this single screen. No server or second device required!
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onStartLocalHotseat}
              className="mt-3 w-full py-3 rounded-xl font-serif font-black text-sm uppercase tracking-wider bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white shadow-md hover:shadow-emerald-600/30 transform active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Start Local Hotseat Game</span>
            </button>
          </div>

          {/* 1.5. Play vs AI Bot */}
          {onStartBotGame && (
            <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-500/80 shadow-md">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase bg-amber-600 text-white mb-1 shadow-sm">
                    Solo Practice
                  </span>
                  <h3 className="font-serif font-black text-lg text-amber-950 flex items-center gap-1.5">
                    <Bot className="w-4 h-4 text-amber-600" />
                    Play vs AI Bot
                  </h3>
                  <p className="font-serif text-xs text-amber-900/80 mt-0.5">
                    Test your woodland strategy against a smart automated Bearfolk explorer!
                  </p>
                </div>
              </div>

              <div className="mt-3 flex items-center gap-2">
                <span className="text-xs font-serif font-bold text-amber-950">Difficulty:</span>
                {(['easy', 'medium', 'hard'] as const).map((diff) => (
                  <button
                    key={diff}
                    type="button"
                    onClick={() => setBotDifficulty(diff)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-serif font-bold capitalize transition ${
                      botDifficulty === diff
                        ? 'bg-amber-600 text-white shadow-sm'
                        : 'bg-white/80 text-amber-900 border border-amber-300 hover:bg-amber-100'
                    }`}
                  >
                    {diff}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={() => onStartBotGame(botDifficulty)}
                className="mt-3 w-full py-3 rounded-xl font-serif font-black text-sm uppercase tracking-wider bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white shadow-md hover:shadow-amber-600/30 transform active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <Bot className="w-4 h-4 text-amber-200" />
                <span>Play vs Bot ({botDifficulty})</span>
              </button>
            </div>
          )}

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-[#6b4a2c]/30"></div>
            <span className="flex-shrink mx-4 text-xs font-serif text-stone-500 uppercase tracking-widest font-bold">
              Or Online Multiplayer
            </span>
            <div className="flex-grow border-t border-[#6b4a2c]/30"></div>
          </div>

          {/* 2. Online Multiplayer Section */}
          <div className="p-4 rounded-2xl bg-white/80 border border-[#6b4a2c]/30 shadow-sm space-y-4">
            {/* Create Room */}
            <div>
              <button
                type="button"
                disabled={isConnecting}
                onClick={onCreateRoom}
                className="w-full py-3 rounded-xl font-serif font-black text-sm uppercase tracking-wider bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-white shadow-md hover:shadow-amber-500/30 transform active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <Globe className="w-4 h-4" />
                <span>Create Private Online Room</span>
              </button>
            </div>

            {/* Room Created Shareable link */}
            {currentRoomId && (
              <div className="p-3 bg-amber-50 rounded-xl border border-amber-300">
                <div className="flex items-center justify-between text-xs font-serif text-stone-700 mb-1">
                  <span>Room Code:</span>
                  <span className="font-mono font-black text-base text-amber-900 tracking-wider">
                    {currentRoomId}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleCopyLink}
                  className="w-full py-2 px-3 rounded-lg bg-amber-200 hover:bg-amber-300 text-amber-950 font-serif font-bold text-xs flex items-center justify-center gap-2 transition"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-700" /> : <Copy className="w-4 h-4" />}
                  <span>{copied ? 'Link Copied to Clipboard!' : 'Copy Shareable Invite Link'}</span>
                </button>
              </div>
            )}

            {/* Join Room by Code */}
            <div className="pt-2 border-t border-stone-200">
              <label className="block text-xs font-serif font-bold text-stone-700 mb-1.5">
                Join with 6-Character Room Code:
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="e.g. BEAR01"
                  maxLength={6}
                  className="w-full px-3 py-2 rounded-xl bg-white border border-[#6b4a2c]/40 font-mono text-center font-bold tracking-widest text-[#4e3218] focus:border-amber-600 focus:outline-none"
                />
                <button
                  type="button"
                  disabled={joinCode.trim().length < 3 || isConnecting}
                  onClick={() => onJoinRoom(joinCode.trim())}
                  className="px-5 py-2 rounded-xl bg-[#6b4a2c] hover:bg-[#573a1e] text-white font-serif font-bold text-sm disabled:opacity-50 transition shadow"
                >
                  Join
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="mt-8 text-center text-[11px] text-stone-500 font-serif">
          Designed with love for Mojito Studios' Bear Necessities.
        </div>
      </div>
    </div>
  );
};

export default Lobby;
