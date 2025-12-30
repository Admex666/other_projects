import React, { useState, useRef, useEffect } from 'react';
import { useGame } from '../context/GameContext';
import { Send, Image, X, MessageSquare, Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '../lib/utils';

export const ChatDrawer = ({ isOpen, onClose }) => {
    const { gameState, role, sendChat } = useGame();
    const [message, setMessage] = useState('');
    const [isExpanded, setIsExpanded] = useState(false);
    const endRef = useRef(null);
    const fileInputRef = useRef(null);

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            const imageUrl = URL.createObjectURL(file);
            sendChat("Sent an image", imageUrl);
        }
    };

    const handleSend = (e) => {
        e.preventDefault();
        if (!message.trim()) return;
        sendChat(message);
        setMessage('');
    };

    // Auto-scroll
    useEffect(() => {
        if (isOpen) {
            endRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [gameState.feed, isOpen]);

    if (!isOpen) return null;

    const renderFeedItem = (item) => {
        if (item.type === 'chat') {
            const isMe = item.sender === (role || "Spectator");
            return (
                <div key={item.id} className={cn("flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300", isMe ? "items-end" : "items-start")}>
                    <div className="flex items-baseline gap-2 mb-1">
                        <span className={cn(
                            "text-[10px] font-bold uppercase tracking-widest",
                            item.sender === 'hider' ? "text-jetlag" : "text-blue-400"
                        )}>
                            {item.sender}
                        </span>
                        <span className="text-[10px] text-gray-600">
                            {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                    <div className={cn(
                        "max-w-[85%] rounded-2xl px-4 py-2 text-sm shadow-sm",
                        isMe ? "bg-jetlag text-black rounded-tr-none font-medium" : "bg-gray-800 text-gray-200 rounded-tl-none"
                    )}>
                        {item.text}
                        {item.image && (
                            <div className="mt-2 rounded-lg overflow-hidden border border-black/10">
                                <img src={item.image} alt="attachment" className="w-full h-auto" />
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        if (item.type === 'question') {
            return (
                <div key={item.id} className="flex flex-col items-center py-2 animate-in fade-in zoom-in-95 duration-500">
                    <div className="bg-gray-900 border border-jetlag/30 rounded-xl px-4 py-3 w-full shadow-lg relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-jetlag" />
                        <div className="flex justify-between items-start mb-1">
                            <span className="text-[9px] font-black text-jetlag uppercase tracking-[0.2em]">Investigation Log</span>
                            <span className="text-[9px] text-gray-600 font-mono italic">
                                {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                        <p className="text-xs text-gray-300 leading-tight mb-2 font-medium">{item.text}</p>
                        <div className="bg-black/40 rounded-lg p-2 flex items-center justify-between border border-white/5">
                            <span className="text-[10px] uppercase font-bold text-gray-500 tracking-wider">Response</span>
                            <span className="text-[11px] font-black text-white italic">{item.answer}</span>
                        </div>
                    </div>
                </div>
            );
        }

        // Event / System messages
        return (
            <div key={item.id} className="flex flex-col items-center py-4 opacity-70">
                <div className="flex items-center gap-3 w-full">
                    <div className="h-px flex-1 bg-gradient-to-r from-transparent via-gray-700 to-transparent" />
                    <span className="text-[9px] font-black text-gray-500 uppercase tracking-[0.3em] whitespace-nowrap">
                        {item.text}
                    </span>
                    <div className="h-px flex-1 bg-gradient-to-r from-gray-700 via-gray-700 to-transparent" />
                </div>
            </div>
        );
    };

    return (
        <div className={cn(
            "fixed z-50 bg-gray-900 border-l border-gray-800 shadow-2xl transition-all duration-300 flex flex-col",
            isExpanded ? "inset-0 w-full" : "top-0 right-0 bottom-0 w-96"
        )}>
            {/* Header */}
            <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-jetlag/10 flex items-center justify-center">
                        <MessageSquare size={18} className="text-jetlag" />
                    </div>
                    <div>
                        <h2 className="font-black text-white uppercase tracking-wider text-sm">Mission Feed</h2>
                        <p className="text-[9px] text-gray-500 uppercase font-bold tracking-tighter">Live Updates & Comms</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={() => setIsExpanded(!isExpanded)} className="text-gray-400 hover:text-white p-2 hover:bg-gray-800 rounded-lg transition-colors">
                        {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                    </button>
                    <button onClick={onClose} className="text-gray-400 hover:text-white p-2 hover:bg-gray-800 rounded-lg transition-colors">
                        <X size={20} />
                    </button>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-950/80 scrollbar-hide">
                {gameState.feed.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center px-10">
                        <div className="w-16 h-16 rounded-3xl bg-gray-900 flex items-center justify-center mb-4 border border-gray-800">
                            <Shield size={32} className="text-gray-700" />
                        </div>
                        <p className="text-sm font-bold text-gray-500 uppercase tracking-widest">Feed Initialized</p>
                        <p className="text-xs text-gray-600 mt-1 italic">Awaiting first contact...</p>
                    </div>
                )}

                {[...gameState.feed].reverse().map((item) => renderFeedItem(item))}
                <div ref={endRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="p-4 border-t border-gray-800 bg-gray-900">
                <div className="flex gap-2">
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept="image/*"
                        onChange={handleFileSelect}
                    />
                    <button
                        type="button"
                        title="Attach Photo"
                        onClick={() => fileInputRef.current?.click()}
                        className="p-3 bg-gray-800 text-gray-400 rounded-xl hover:bg-gray-700 hover:text-white transition-colors"
                    >
                        <Image size={20} />
                    </button>
                    <input
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Type a message..."
                        className="flex-1 bg-gray-800 text-white placeholder-gray-500 rounded-xl px-4 focus:outline-none focus:ring-2 focus:ring-jetlag"
                    />
                    <button
                        type="submit"
                        className="p-3 bg-jetlag text-black rounded-xl font-bold hover:bg-jetlag-light transition-transform active:scale-95"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </form>
        </div>
    );
};
