import React, { useState } from 'react';
import { GameState, GridPosition } from './game/types';
import { getValidPlacements } from './game/validation';
import { createInitialGameState, resolveHotseatRound, PlayerTurnSelection } from './game/hotseat';
import { chooseBotMove, BotDifficulty } from './game/ai/bot';
import {
  TableauGrid,
  HandView,
  ScoreBoard,
  OpponentBoard,
  GameOverModal,
  Lobby,
} from './components';
import { Info, ArrowRight, X, Copy, Check, Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  // Screen mode: 'lobby' | 'hotseat' | 'multiplayer' | 'bot'
  const [mode, setMode] = useState<'lobby' | 'hotseat' | 'multiplayer' | 'bot'>('lobby');
  const [botDifficulty, setBotDifficulty] = useState<BotDifficulty>('medium');

  // Player Names
  const [playerName, setPlayerName] = useState<string>('Player 1');
  const [player2Name, setPlayer2Name] = useState<string>('Player 2');

  // Hotseat Game State
  const [gameState, setGameState] = useState<GameState | null>(null);

  // In hotseat, which player is currently making their turn? 'p1' | 'p2' | 'resolving'
  const [activeHotseatPlayer, setActiveHotseatPlayer] = useState<'p1' | 'p2'>('p1');
  const [p1Selection, setP1Selection] = useState<PlayerTurnSelection | null>(null);

  // Turn in-progress selections for active player
  const [selectedTableauCardId, setSelectedTableauCardId] = useState<number | null>(null);
  const [selectedReserveCardId, setSelectedReserveCardId] = useState<number | null>(null);
  const [selectedPlacement, setSelectedPlacement] = useState<GridPosition | null>(null);

  // Pass-the-device screen transition in hotseat
  const [showPassScreen, setShowPassScreen] = useState<boolean>(false);

  // Round summary notification
  const [roundNotification, setRoundNotification] = useState<string | null>(null);
  const [lastBeeWinnerName, setLastBeeWinnerName] = useState<string | null>(null);

  // Help / Rules modal
  const [rulesModalOpen, setRulesModalOpen] = useState<boolean>(false);

  // Multiplayer room state
  const [roomId, setRoomId] = useState<string | null>(null);
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [multiplayerPlayerId, setMultiplayerPlayerId] = useState<string | null>(null);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  // Current active player object in hotseat or multiplayer
  const activePid = mode === 'multiplayer' && multiplayerPlayerId ? multiplayerPlayerId : activeHotseatPlayer;
  const currentP = gameState?.players[activePid];
  const opponentPid = gameState ? Object.keys(gameState.players).find((id) => id !== activePid) : undefined;
  const opponentP = opponentPid ? gameState?.players[opponentPid] : (gameState && activeHotseatPlayer === 'p1' ? gameState.players.p2 : gameState?.players.p1);

  // Initialize Hotseat Game
  const handleStartHotseat = () => {
    const initialState = createInitialGameState(playerName || 'Player 1', player2Name || 'Player 2');
    setGameState(initialState);
    setActiveHotseatPlayer('p1');
    setP1Selection(null);
    setSelectedTableauCardId(null);
    setSelectedReserveCardId(null);
    setSelectedPlacement(null);
    setShowPassScreen(false);
    setRoundNotification(null);
    setLastBeeWinnerName(null);
    setMode('hotseat');
  };

  // Initialize Game vs Bot
  const handleStartBotGame = (difficulty: BotDifficulty = 'medium') => {
    const botName = `BearBot (${difficulty.charAt(0).toUpperCase() + difficulty.slice(1)})`;
    const initialState = createInitialGameState(playerName || 'Explorer', botName);
    setGameState(initialState);
    setBotDifficulty(difficulty);
    setActiveHotseatPlayer('p1');
    setP1Selection(null);
    setSelectedTableauCardId(null);
    setSelectedReserveCardId(null);
    setSelectedPlacement(null);
    setShowPassScreen(false);
    setRoundNotification(`Game started against ${botName}!`);
    setLastBeeWinnerName(null);
    setMode('bot');
  };

  // Reset / Rematch
  const handleRematch = () => {
    if (mode === 'hotseat') {
      handleStartHotseat();
    } else if (mode === 'bot') {
      handleStartBotGame(botDifficulty);
    } else if (socket && roomId) {
      socket.send(JSON.stringify({ type: 'REMATCH' }));
    }
  };

  // Handle Online Room Creation
  const handleCreateRoom = () => {
    connectWebSocket('', playerName || 'Player 1', true);
  };

  // Handle Join Online Room
  const handleJoinRoom = (code: string) => {
    const cleanCode = code.trim().toUpperCase();
    setRoomId(cleanCode);
    connectWebSocket(cleanCode, playerName || 'Player 2', false);
  };

  const connectWebSocket = (roomCode: string, name: string, isHost: boolean) => {
    setServerError(null);
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.hostname || 'localhost';
      const wsPort = window.location.port ? window.location.port : '3001';
      const wsUrl = `${wsProtocol}//${wsHost}:${wsPort}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setSocket(ws);
        setMode('multiplayer');
        if (isHost) {
          ws.send(JSON.stringify({ type: 'CREATE_ROOM', playerName: name }));
        } else {
          ws.send(JSON.stringify({ type: 'JOIN_ROOM', playerName: name, roomId: roomCode }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'ROOM_CREATED') {
            setMultiplayerPlayerId(msg.playerId);
            setRoomId(msg.roomId);
            if (msg.inviteUrl) {
              setInviteUrl(msg.inviteUrl);
            }
          } else if (msg.type === 'ROOM_JOINED') {
            setMultiplayerPlayerId(msg.playerId);
            setRoomId(msg.roomId);
            if (msg.gameState) setGameState(msg.gameState);
          } else if (msg.type === 'GAME_STARTED') {
            if (msg.state) setGameState(msg.state);
            setRoundNotification('Game started! Both players connected.');
          } else if (msg.type === 'STATE_UPDATE') {
            setGameState(msg.state);
          } else if (msg.type === 'ROUND_RESOLVED') {
            setGameState(msg.state || msg.nextState);
            setRoundNotification(`Round ${msg.round} complete!`);
          } else if (msg.type === 'ERROR') {
            setServerError(msg.message);
          }
        } catch (e) {
          console.error('Error handling WebSocket message:', e);
        }
      };

      ws.onerror = () => {
        setServerError('Could not connect to online server. Check if server is running on port 3001.');
      };
    } catch {
      handleStartHotseat();
    }
  };

  // Valid placements for current active player
  const validPlacements = currentP ? getValidPlacements(currentP.tableau) : [];

  // Can confirm move?
  const canConfirmMove =
    selectedTableauCardId !== null &&
    selectedReserveCardId !== null &&
    selectedTableauCardId !== selectedReserveCardId &&
    selectedPlacement !== null &&
    validPlacements.some((p) => p.row === selectedPlacement.row && p.col === selectedPlacement.col);

  // Handle Confirm Move (Hotseat or Multiplayer)
  const handleConfirmMove = () => {
    if (!canConfirmMove || !selectedPlacement || !selectedTableauCardId || !selectedReserveCardId) {
      return;
    }

    if (mode === 'multiplayer' && socket && multiplayerPlayerId && roomId) {
      socket.send(
        JSON.stringify({
          type: 'SUBMIT_SELECTION',
          roomId,
          playerId: multiplayerPlayerId,
          tableauCardId: selectedTableauCardId,
          reserveCardId: selectedReserveCardId,
          position: selectedPlacement,
        })
      );
      setSelectedTableauCardId(null);
      setSelectedReserveCardId(null);
      setSelectedPlacement(null);
      setRoundNotification('Move submitted! Waiting for opponent to draft...');
      return;
    }

    const currentSelection: PlayerTurnSelection = {
      tableauCardId: selectedTableauCardId,
      reserveCardId: selectedReserveCardId,
      position: selectedPlacement,
    };

    if (mode === 'bot') {
      if (!gameState) return;
      const botP = gameState.players.p2;
      const humanP = gameState.players.p1;
      const botMove = chooseBotMove(botP, humanP, gameState.round, botDifficulty);

      const botSelection: PlayerTurnSelection = {
        tableauCardId: botMove.tableauCardId,
        reserveCardId: botMove.reserveCardId,
        position: botMove.position,
      };

      const resolution = resolveHotseatRound(gameState, currentSelection, botSelection);
      setGameState(resolution.nextState);
      setSelectedTableauCardId(null);
      setSelectedReserveCardId(null);
      setSelectedPlacement(null);

      // Bee winner names
      if (resolution.beeTokenRecipients.length === 2) {
        setLastBeeWinnerName('Both Players (Tied)');
      } else if (resolution.beeTokenRecipients.includes('p1')) {
        setLastBeeWinnerName(gameState.players.p1.name);
      } else if (resolution.beeTokenRecipients.includes('p2')) {
        setLastBeeWinnerName(gameState.players.p2.name);
      }

      setRoundNotification(resolution.logMessage);
      setTimeout(() => {
        setRoundNotification(null);
      }, 5000);
      return;
    }

    if (activeHotseatPlayer === 'p1') {
      setP1Selection(currentSelection);
      // Reset local selection controls
      setSelectedTableauCardId(null);
      setSelectedReserveCardId(null);
      setSelectedPlacement(null);
      // Prompt pass device to Player 2
      setShowPassScreen(true);
      setActiveHotseatPlayer('p2');
    } else {
      // Player 2 confirms: resolve round!
      if (!p1Selection || !gameState) return;

      const resolution = resolveHotseatRound(gameState, p1Selection, currentSelection);

      setGameState(resolution.nextState);
      setP1Selection(null);
      setSelectedTableauCardId(null);
      setSelectedReserveCardId(null);
      setSelectedPlacement(null);
      setShowPassScreen(false);
      setActiveHotseatPlayer('p1');

      // Bee winner names
      if (resolution.beeTokenRecipients.length === 2) {
        setLastBeeWinnerName('Both Players (Tied)');
      } else if (resolution.beeTokenRecipients.includes('p1')) {
        setLastBeeWinnerName(gameState.players.p1.name);
      } else if (resolution.beeTokenRecipients.includes('p2')) {
        setLastBeeWinnerName(gameState.players.p2.name);
      }

      setRoundNotification(resolution.logMessage);
      setTimeout(() => {
        setRoundNotification(null);
      }, 5000);
    }
  };

  // If in Lobby
  if (mode === 'lobby') {
    return (
      <div className="min-h-screen flex flex-col justify-between py-6">
        <Lobby
          playerName={playerName}
          onPlayerNameChange={setPlayerName}
          player2Name={player2Name}
          onPlayer2NameChange={setPlayer2Name}
          onCreateRoom={handleCreateRoom}
          onJoinRoom={handleJoinRoom}
          onStartLocalHotseat={handleStartHotseat}
          onStartBotGame={handleStartBotGame}
          currentRoomId={roomId}
          error={serverError}
        />
      </div>
    );
  }

  // Pass-Device Screen for Hotseat
  if (showPassScreen && mode === 'hotseat') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
        <div className="wood-panel rounded-3xl p-8 max-w-md w-full text-center shadow-2xl text-[#3c2a18]">
          <div className="w-16 h-16 rounded-full bg-amber-400 text-amber-950 flex items-center justify-center mx-auto mb-4 text-3xl shadow-lg">
            🌲
          </div>
          <h2 className="font-serif font-black text-2xl sm:text-3xl text-[#4e3218]">
            Pass Device to {gameState?.players.p2.name}
          </h2>
          <p className="font-serif text-sm text-stone-600 mt-2">
            Player 1 has secretly locked in their choices. It's now {gameState?.players.p2.name}'s turn to draft!
          </p>

          <button
            type="button"
            onClick={() => setShowPassScreen(false)}
            className="mt-6 w-full py-3.5 rounded-full font-serif font-black text-sm uppercase tracking-wider bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white shadow-xl cursor-pointer flex items-center justify-center gap-2 transform active:scale-95 transition"
          >
            <span>I'm Ready — Start Turn</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // Waiting for opponent screen in multiplayer
  if (mode === 'multiplayer' && (!gameState || !currentP)) {
    const shareableUrl =
      inviteUrl ||
      (roomId
        ? `${window.location.origin}${window.location.pathname}?room=${roomId}`
        : `${window.location.origin}${window.location.pathname}`);

    const handleCopyWaitingLink = () => {
      navigator.clipboard.writeText(shareableUrl).then(() => {
        setCopiedLink(true);
        setTimeout(() => setCopiedLink(false), 2500);
      });
    };

    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="wood-panel rounded-3xl p-8 max-w-md w-full text-center shadow-2xl text-[#3c2a18]">
          <div className="w-16 h-16 rounded-full bg-amber-400 text-amber-950 flex items-center justify-center mx-auto mb-4 text-3xl shadow-lg">
            🌐
          </div>
          <h2 className="font-serif font-black text-2xl sm:text-3xl text-[#4e3218]">
            Room Created!
          </h2>
          <p className="font-serif text-sm text-stone-600 mt-1">
            Waiting for Player 2 to join...
          </p>

          {roomId && (
            <div className="mt-5 p-4 rounded-2xl bg-amber-100/70 border-2 border-amber-300">
              <span className="block text-[11px] font-mono uppercase tracking-wider text-amber-800 font-bold mb-1">
                Room Code
              </span>
              <span className="font-mono font-black text-3xl text-amber-950 tracking-widest">
                {roomId}
              </span>
            </div>
          )}

          <div className="mt-5 flex flex-col gap-3">
            <button
              type="button"
              onClick={handleCopyWaitingLink}
              className="w-full py-3 rounded-xl font-serif font-black text-sm uppercase tracking-wider bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white shadow-md flex items-center justify-center gap-2 cursor-pointer transition active:scale-95"
            >
              {copiedLink ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
              <span>{copiedLink ? 'Link Copied!' : 'Copy Invite Link'}</span>
            </button>

            <button
              type="button"
              onClick={() => {
                if (socket) {
                  try {
                    socket.close();
                  } catch {}
                }
                setSocket(null);
                setMode('lobby');
              }}
              className="w-full py-2.5 rounded-xl font-serif text-xs font-bold text-stone-600 hover:bg-stone-200/60 transition cursor-pointer"
            >
              Cancel & Back to Lobby
            </button>
          </div>

          <div className="mt-6 flex items-center justify-center gap-2 text-stone-500 font-serif text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
            <span>Game will start immediately when the second player joins</span>
          </div>

          {serverError && (
            <div className="mt-4 p-3 rounded-xl bg-red-100/90 border border-red-300 text-red-700 font-serif text-xs">
              {serverError}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!gameState || !currentP) {
    return (
      <div className="min-h-screen flex items-center justify-center font-serif text-amber-900">
        Loading game...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col justify-between pb-8 select-none">
      {/* Top Header & Navigation */}
      <header className="px-4 py-3 bg-[#5c3c20] text-stone-100 shadow-md flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🐻</span>
          <span className="font-serif font-black text-lg sm:text-xl tracking-tight text-amber-200">
            Bear Necessities
          </span>
          <span className="text-[10px] font-mono uppercase bg-amber-400/20 text-amber-300 px-2 py-0.5 rounded border border-amber-400/40 ml-1">
            {mode === 'hotseat' ? 'Hotseat Mode' : mode === 'bot' ? `Vs Bot (${botDifficulty})` : `Room: ${roomId}`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setRulesModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-serif flex items-center gap-1.5 transition text-amber-100"
          >
            <Info className="w-3.5 h-3.5" />
            <span>Rules</span>
          </button>

          <button
            onClick={() => setMode('lobby')}
            className="px-3 py-1.5 rounded-lg bg-black/20 hover:bg-black/30 text-xs font-serif text-stone-300 transition"
          >
            Leave Game
          </button>
        </div>
      </header>

      {/* Round & Score Board */}
      <div className="my-3">
        <ScoreBoard
          round={gameState.round}
          player={currentP}
          opponent={opponentP}
          lastBeeWinnerName={lastBeeWinnerName}
          onExplainClick={() => setRulesModalOpen(true)}
        />
      </div>

      {/* Turn Banner (Hotseat indication) */}
      {mode === 'hotseat' && (
        <div className="max-w-5xl mx-auto px-4 w-full mb-2">
          <div className="flex items-center justify-between bg-gradient-to-r from-amber-600 to-amber-700 text-white px-4 py-2 rounded-xl shadow-md border border-amber-400/60 font-serif text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="font-black tracking-wide">
                Current Explorer: <span className="underline decoration-amber-300">{currentP.name}</span>
              </span>
            </div>
            <span className="text-[11px] text-amber-200 opacity-90 hidden sm:inline">
              Secretly pick your 2 cards, select grid slot, then confirm.
            </span>
          </div>
        </div>
      )}

      {/* Round Notification Toast */}
      {roundNotification && (
        <div className="max-w-xl mx-auto px-4 w-full mb-3 animate-fade-in">
          <div className="p-3 rounded-xl bg-amber-100 border-2 border-amber-500 text-amber-950 font-serif font-bold text-xs sm:text-sm text-center shadow-lg">
            {roundNotification}
          </div>
        </div>
      )}

      {/* Main Game Board Area */}
      <main className="max-w-6xl mx-auto px-2 sm:px-4 w-full flex-1 flex flex-col justify-center gap-6">
        {/* Upper Area: Opponent Tableau (Compact) & Active Tableau Side-by-Side on Desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
          {/* Active Player Tableau (8 cols on lg) */}
          <div className="lg:col-span-8 flex flex-col items-center">
            <div className="flex items-center justify-between w-full max-w-[560px] mb-2 px-1 text-xs font-serif font-bold text-[#4e3218]">
              <span>Your Photographic Journey (4×3 Grid)</span>
              <span className="text-emerald-800">
                {validPlacements.length} valid placement {validPlacements.length === 1 ? 'slot' : 'slots'}
              </span>
            </div>

            <TableauGrid
              tableau={currentP.tableau}
              validPlacements={validPlacements}
              selectedPlacement={selectedPlacement}
              onSelectPosition={(pos) => setSelectedPlacement(pos)}
              size="md"
            />
          </div>

          {/* Opponent Compact Board (4 cols on lg) */}
          {opponentP && (
            <div className="lg:col-span-4 flex flex-col">
              <OpponentBoard opponent={opponentP} />
            </div>
          )}
        </div>

        {/* Hand View (Active Player's 2-5 Cards) */}
        <HandView
          hand={currentP.hand}
          selectedTableauCardId={selectedTableauCardId}
          selectedReserveCardId={selectedReserveCardId}
          onSelectTableauCard={(id) => setSelectedTableauCardId(id === -1 ? null : id)}
          onSelectReserveCard={(id) => setSelectedReserveCardId(id === -1 ? null : id)}
          onConfirmMove={handleConfirmMove}
          canConfirm={canConfirmMove}
          hasPlacementSelected={selectedPlacement !== null}
          currentReserveCard={currentP.reserveCard}
          round={gameState.round}
        />
      </main>

      {/* Game Over Modal */}
      {gameState.phase === 'GAME_OVER' && (
        <GameOverModal
          players={gameState.players}
          activePlayerId={currentP.id}
          winnerIds={gameState.winner}
          onRematch={handleRematch}
        />
      )}

      {/* Rules & Help Modal */}
      {rulesModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
          onClick={() => setRulesModalOpen(false)}
        >
          <div
            className="relative wood-panel rounded-3xl p-6 sm:p-8 max-w-2xl w-full shadow-2xl text-[#3c2a18] max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setRulesModalOpen(false)}
              className="absolute top-4 right-4 p-1.5 rounded-full bg-stone-300 hover:bg-stone-400 text-stone-800 transition"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="font-serif font-black text-2xl text-[#4e3218] mb-4 flex items-center gap-2">
              <span>🐻</span> Bear Necessities Quick Rules
            </h2>

            <div className="space-y-4 font-serif text-xs sm:text-sm leading-relaxed text-stone-800">
              <div className="p-3 bg-white/70 rounded-xl border border-[#6b4a2c]/20">
                <h4 className="font-bold text-[#6b4a2c] mb-1">1. The 12-Round Journey & Tableau</h4>
                <p>
                  You build a 4-column by 3-row grid of photographs over exactly 12 rounds. The first card can be placed anywhere. Every subsequent card must be placed orthogonally adjacent (Up, Down, Left, Right) to at least one already placed card.
                </p>
              </div>

              <div className="p-3 bg-white/70 rounded-xl border border-[#6b4a2c]/20">
                <h4 className="font-bold text-[#6b4a2c] mb-1">2. Drafting Each Turn</h4>
                <p>
                  Each round, secretly choose <strong>1 card to play to your Tableau</strong> and <strong>1 card to store in your Reserve</strong>. After scoring, remaining hand cards are passed to your neighbor, and you add your reserved card to your new hand!
                </p>
              </div>

              <div className="p-3 bg-white/70 rounded-xl border border-[#6b4a2c]/20">
                <h4 className="font-bold text-[#6b4a2c] mb-1">3. Cascading Activations</h4>
                <p>
                  When your card is placed, it activates <strong>FIRST</strong>. Next, every orthogonally adjacent card already in your tableau activates in the order of your choice!
                </p>
              </div>

              <div className="p-3 bg-white/70 rounded-xl border border-[#6b4a2c]/20">
                <h4 className="font-bold text-[#6b4a2c] mb-1">4. Bee Time (Catch-up Mechanism)</h4>
                <p>
                  At the end of each round, the player who earned the <strong>fewest VP this round</strong> takes 1 Bee token. If tied, both players take 1 Bee token!
                </p>
              </div>

              <div className="p-3 bg-white/70 rounded-xl border border-[#6b4a2c]/20">
                <h4 className="font-bold text-[#6b4a2c] mb-1">5. End-Game Bee Hive Multiplier</h4>
                <p>
                  At the end of Round 12, each Bee token multiplies the total number of <strong>Bee Hive symbols</strong> on your tableau cards:
                  <br />
                  <span className="font-bold text-amber-800">Final Score = In-game VP + (Bee Hives × Bee Tokens)</span>.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
