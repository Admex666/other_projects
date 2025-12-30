import React, { useState } from 'react';
import { useGame } from '../context/GameContext';
import { cn } from '../lib/utils';
import { Search, ChevronRight, Send, Clock, Banknote, MapPin, X } from 'lucide-react';
import stationsData from '../data/stations.json';
import { useGeolocation } from '../hooks/useGeolocation';

export const InvestigationPanel = ({ isOpen, onClose }) => {
    const { questions, submitQuestion, setPreview } = useGame();
    const { location: seekerLocation } = useGeolocation();
    const [selectedType, setSelectedType] = useState(null);
    const [selectedOption, setSelectedOption] = useState(null);
    const [selectedStation, setSelectedStation] = useState(null);
    const [customValue, setCustomValue] = useState("");

    const activeQuestion = selectedType ? questions.find(q => q.type === selectedType) : null;

    // Handle Map Preview
    React.useEffect(() => {
        if (!selectedType || !seekerLocation || !isOpen) {
            setPreview(null);
            return;
        }

        if (selectedType === 'Radar' && selectedOption) {
            let radius = 1000;
            if (selectedOption.includes('0.25mi')) radius = 402;
            else if (selectedOption.includes('0.50mi')) radius = 805;
            else if (selectedOption.includes('1mi')) radius = 1609;
            else if (selectedOption.includes('3mi')) radius = 4828;
            else if (selectedOption.includes('5mi')) radius = 8046;
            else if (selectedOption.includes('10mi')) radius = 16093;

            setPreview({
                type: 'Radar',
                center: seekerLocation,
                radius: radius
            });
        } else if (selectedType === 'Thermometer') {
            setPreview({
                type: 'Thermometer',
                center: seekerLocation,
                radius: [500, 2000, 5000]
            });
        } else if (selectedType === 'Matching' && selectedStation) {
            setPreview({
                type: 'Matching',
                center: { lat: selectedStation.lat, lng: selectedStation.lng },
                radius: 1000
            });
        } else {
            setPreview(null);
        }

        return () => setPreview(null);
    }, [selectedType, selectedOption, selectedStation, seekerLocation, setPreview, isOpen]);

    const handleAsk = () => {
        if (!activeQuestion) return;

        const params = {
            option: selectedOption,
            station: selectedStation,
            custom: customValue
        };

        submitQuestion(activeQuestion, params, seekerLocation);

        // Reset
        setSelectedType(null);
        setSelectedOption(null);
        setSelectedStation(null);
        setCustomValue("");
        onClose(); // Close panel after asking
    };

    if (!isOpen) return null;

    return (
        <div className={cn(
            "absolute inset-y-0 left-0 z-[2000] w-full md:w-[450px] bg-gray-950/95 backdrop-blur-xl border-r border-gray-800 shadow-2xl flex flex-col transition-all duration-500",
            isOpen ? "translate-x-0" : "-translate-x-full"
        )}>
            {/* Header */}
            <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter italic flex items-center gap-2">
                        <Search className="text-jetlag" />
                        Investigation
                    </h2>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-widest mt-1">Satellite Tracking & Local Intel</p>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg text-gray-500 hover:text-white transition-colors">
                    <X size={24} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
                {selectedType && activeQuestion ? (
                    <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                        <button
                            onClick={() => { setSelectedType(null); setSelectedOption(null); setSelectedStation(null); }}
                            className="text-jetlag hover:text-jetlag-light mb-6 flex items-center gap-2 text-xs font-black uppercase tracking-widest transition-colors"
                        >
                            &larr; Back to Tools
                        </button>

                        <div className="bg-gray-900/50 rounded-2xl p-6 border border-gray-800 mb-6">
                            <h3 className="text-3xl font-black text-white uppercase tracking-tighter mb-4">{activeQuestion.type}</h3>
                            <div className="flex gap-4 mb-6">
                                <div className="flex items-center gap-2 text-jetlag font-bold text-xs bg-jetlag/10 px-3 py-1 rounded-full border border-jetlag/20">
                                    <Banknote size={12} />
                                    <span>{activeQuestion.cost || "Free"}</span>
                                </div>
                                <div className="flex items-center gap-2 text-gray-400 text-xs bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                                    <Clock size={12} />
                                    <span>{activeQuestion.time || "Instant"}</span>
                                </div>
                            </div>
                            <p className="text-lg font-medium text-gray-300 italic leading-snug">
                                "{activeQuestion.template}"
                            </p>
                        </div>

                        <div className="space-y-8">
                            {activeQuestion.options && activeQuestion.options.length > 0 && (
                                <div>
                                    <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-4">Select Range</h4>
                                    <div className="grid grid-cols-2 gap-2">
                                        {activeQuestion.options.map((opt, i) => (
                                            <button
                                                key={i}
                                                onClick={() => setSelectedOption(opt)}
                                                className={cn(
                                                    "p-3 rounded-xl text-xs font-black transition-all border-2",
                                                    selectedOption === opt
                                                        ? "bg-jetlag border-jetlag text-black"
                                                        : "bg-gray-900 border-gray-800 text-gray-400 hover:border-gray-700 hover:text-white"
                                                )}
                                            >
                                                {opt}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {(activeQuestion.type === 'Matching' || activeQuestion.type === 'Measuring') && (
                                <div>
                                    <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-4">Select Station</h4>
                                    <select
                                        className="w-full bg-gray-900 border-2 border-gray-800 text-white rounded-xl py-3 px-4 focus:outline-none focus:border-jetlag transition-all text-sm font-bold"
                                        onChange={(e) => {
                                            const st = stationsData.find(s => s.id === e.target.value);
                                            setSelectedStation(st);
                                        }}
                                        value={selectedStation?.id || ""}
                                    >
                                        <option value="" disabled>Choose station...</option>
                                        {stationsData.map(st => (
                                            <option key={st.id} value={st.id}>{st.name}</option>
                                        ))}
                                    </select>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 gap-4">
                        <p className="text-xs font-black text-gray-600 uppercase tracking-widest mb-2">Available Intelligence Tools</p>
                        {questions.map((q, i) => (
                            <button
                                key={i}
                                onClick={() => setSelectedType(q.type)}
                                className="group bg-gray-900/50 border border-gray-800 hover:border-jetlag p-5 rounded-2xl transition-all hover:bg-gray-800/80 text-left flex items-center justify-between"
                            >
                                <div>
                                    <h3 className="text-lg font-black text-white uppercase group-hover:text-jetlag transition-colors">{q.type}</h3>
                                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{q.cost || "Free"}</p>
                                </div>
                                <ChevronRight className="text-gray-700 group-hover:text-jetlag group-hover:translate-x-1 transition-all" size={20} />
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="p-6 bg-gray-900/80 border-t border-gray-800 backdrop-blur-md">
                <button
                    disabled={!selectedType || (!selectedOption && !selectedStation)}
                    onClick={handleAsk}
                    className="w-full bg-jetlag hover:bg-jetlag-light disabled:opacity-50 disabled:cursor-not-allowed text-black font-black py-4 rounded-xl shadow-xl flex items-center justify-center gap-3 transition-all active:scale-[0.98]"
                >
                    <Send size={20} />
                    DEPLOY TRACKER
                </button>
                {!seekerLocation && (
                    <p className="text-[9px] text-red-500 font-black uppercase tracking-tighter text-center mt-3 animate-pulse">
                        Satellite Link unstable: GPS REQUIRED for auto-intel
                    </p>
                )}
            </div>
        </div>
    );
};
