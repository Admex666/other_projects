import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap, ZoomControl, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useGeolocation } from '../hooks/useGeolocation';
import { useGame } from '../context/GameContext';
import { Crosshair, MapPin, Navigation, Info, Shield, Search } from 'lucide-react';
import L from 'leaflet';
import stationsData from '../data/stations.json';
import boundariesData from '../data/boundaries.json';
import { cn } from '../lib/utils';
import { InvestigationPanel } from '../components/InvestigationPanel';

// Fix Leaflet legacy marker icon issue in React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const RecenterMap = ({ location }) => {
    const map = useMap();
    useEffect(() => {
        if (location) {
            map.flyTo([location.lat, location.lng], map.getZoom());
        }
    }, [location, map]);
    return null;
};

export const TheGrid = () => {
    const { location, error } = useGeolocation();
    const { role, claimHidingSpot, hiderState, gameState } = useGame();
    const [selectedStation, setSelectedStation] = useState(null);
    const [recenterActive, setRecenterActive] = useState(false);
    const [isIntelOpen, setIsIntelOpen] = useState(false);

    // Default to Zurich if no location
    const center = location ? [location.lat, location.lng] : [47.3769, 8.5417];

    const getCircleColor = (st) => {
        if (hiderState?.hidingSpot?.id === st.id) return '#ef4444';
        if (selectedStation?.id === st.id) return '#e6b91e';
        return '#444';
    };

    const getFillColor = (st) => {
        if (hiderState?.hidingSpot?.id === st.id) return '#ef4444';
        if (selectedStation?.id === st.id) return '#e6b91e';
        return '#000';
    };

    const boundaryStyle = {
        color: "#e6b91e",
        weight: 3,
        opacity: 0.6,
        fillColor: "#e6b91e",
        fillOpacity: 0.05,
        dashArray: "10, 10"
    };

    return (
        <div className="relative h-full w-full bg-gray-950 font-sans">
            <InvestigationPanel isOpen={isIntelOpen} onClose={() => setIsIntelOpen(false)} />

            <MapContainer
                center={center}
                zoom={13}
                scrollWheelZoom={true}
                className="h-full w-full grayscale-[0.2] contrast-[1.1]"
                zoomControl={false}
            >
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                />

                <ZoomControl position="bottomright" />

                {recenterActive && <RecenterMap location={location} />}

                {/* Game Boundaries */}
                <GeoJSON
                    data={boundariesData}
                    style={boundaryStyle}
                />

                {/* User Location Marker */}
                {location && (
                    <>
                        <Circle
                            center={[location.lat, location.lng]}
                            radius={location.accuracy || 20}
                            pathOptions={{ color: '#2563eb', fillColor: '#2563eb', fillOpacity: 0.1, weight: 1 }}
                        />
                        <Marker position={[location.lat, location.lng]}>
                            <Popup className="custom-popup">
                                <div className="p-1">
                                    <p className="font-black text-blue-600 text-xs uppercase tracking-widest mb-1">Live Position</p>
                                    <p className="text-[10px] text-gray-500">{location.lat.toFixed(5)}, {location.lng.toFixed(5)}</p>
                                </div>
                            </Popup>
                        </Marker>
                    </>
                )}

                {/* Station Markers */}
                {stationsData.map(st => (
                    <Circle
                        key={st.id}
                        center={[st.lat, st.lng]}
                        radius={400}
                        pathOptions={{
                            color: getCircleColor(st),
                            fillColor: getFillColor(st),
                            fillOpacity: 0.7,
                            weight: selectedStation?.id === st.id ? 4 : 2
                        }}
                        eventHandlers={{
                            click: () => setSelectedStation(st)
                        }}
                    >
                        <Popup className="station-popup">
                            <div className="font-sans min-w-[150px]">
                                <h3 className="font-black text-base italic uppercase tracking-tight leading-none mb-1">{st.name}</h3>
                                <p className="text-[10px] uppercase font-bold text-gray-400 mb-3">{st.type} STATION</p>

                                {role === 'hider' && gameState.status === 'lobby' && (
                                    <button
                                        onClick={() => claimHidingSpot(st)}
                                        className={cn(
                                            "w-full text-[10px] font-black py-2 px-3 rounded-lg transition-all border-2",
                                            hiderState?.hidingSpot?.id === st.id
                                                ? "bg-red-600 border-red-600 text-white"
                                                : "bg-jetlag border-jetlag text-black hover:scale-[1.03]"
                                        )}
                                    >
                                        {hiderState?.hidingSpot?.id === st.id ? "CURRENT HIDING SPOT" : "SET AS HIDING SPOT"}
                                    </button>
                                )}

                                {hiderState?.hidingSpot?.id === st.id && role === 'hider' && (
                                    <div className="mt-2 bg-red-100 text-red-600 p-2 rounded-md border border-red-200 text-center">
                                        <p className="text-[8px] font-black uppercase">Active Hiding Spot</p>
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Circle>
                ))}

                {/* Range Previews (Radar, Thermometer, Matching) */}
                {gameState.previewData && (
                    <>
                        {Array.isArray(gameState.previewData.radius) ? (
                            gameState.previewData.radius.map((r, i) => (
                                <Circle
                                    key={i}
                                    center={[gameState.previewData.center.lat, gameState.previewData.center.lng]}
                                    radius={r}
                                    pathOptions={{
                                        color: '#e6b91e',
                                        fillColor: '#e6b91e',
                                        fillOpacity: 0.05,
                                        weight: 2,
                                        dashArray: "5, 10"
                                    }}
                                />
                            ))
                        ) : (
                            <Circle
                                center={[gameState.previewData.center.lat, gameState.previewData.center.lng]}
                                radius={gameState.previewData.radius}
                                pathOptions={{
                                    color: '#e6b91e',
                                    fillColor: '#e6b91e',
                                    fillOpacity: 0.1,
                                    weight: 3,
                                    dashArray: "10, 10"
                                }}
                            />
                        )}
                    </>
                )}

                {/* Hider Choice footprint preview */}
                {role === 'hider' && selectedStation && gameState.status === 'lobby' && (
                    <Circle
                        center={[selectedStation.lat, selectedStation.lng]}
                        radius={1000}
                        pathOptions={{
                            color: '#ef4444',
                            fillColor: '#ef4444',
                            fillOpacity: 0.05,
                            weight: 1,
                            dashArray: "2, 4"
                        }}
                    />
                )}

            </MapContainer>

            {/* Overlay UI Controls */}
            <div className="absolute top-6 left-6 z-[1000] flex flex-col gap-3">
                <div className="bg-gray-900/90 backdrop-blur-md p-4 rounded-2xl border border-gray-800 shadow-2xl flex items-center gap-4">
                    <div className={cn(
                        "w-2 h-2 rounded-full animate-pulse",
                        gameState.status === 'playing' ? "bg-green-500" : "bg-yellow-500"
                    )}></div>
                    <div>
                        <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest leading-none mb-1">Grid Status</p>
                        <p className="text-xs font-black text-white uppercase italic">{gameState.status}</p>
                    </div>
                </div>

                {role === 'hider' && hiderState.hidingSpot && (
                    <div className="bg-red-900/90 backdrop-blur-md p-4 rounded-2xl border border-red-700 shadow-2xl flex items-center gap-4 animate-in slide-in-from-left duration-500">
                        <div className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-white ring-4 ring-red-600/20">
                            <Shield size={20} />
                        </div>
                        <div>
                            <p className="text-[10px] font-black text-red-400 uppercase tracking-widest leading-none mb-1">Hiding Spot</p>
                            <p className="text-sm font-black text-white uppercase italic">{hiderState.hidingSpot.name}</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom Controls */}
            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 z-[1000] flex gap-4">
                <button
                    onClick={() => setRecenterActive(!recenterActive)}
                    className={cn(
                        "p-5 rounded-2xl backdrop-blur-md shadow-2xl border-2 transition-all flex items-center gap-3",
                        recenterActive
                            ? "bg-blue-600 border-blue-400 text-white scale-110"
                            : "bg-gray-900/90 border-gray-800 text-gray-400 hover:text-white"
                    )}
                >
                    <Navigation size={24} className={recenterActive ? "animate-bounce" : ""} />
                    <span className="text-xs font-black uppercase tracking-widest hidden md:inline">Lock to Me</span>
                </button>

                {role === 'seeker' && (
                    <button
                        onClick={() => setIsIntelOpen(!isIntelOpen)}
                        className={cn(
                            "p-5 backdrop-blur-md rounded-2xl shadow-2xl border-2 transition-all flex items-center gap-3 group",
                            isIntelOpen
                                ? "bg-jetlag border-jetlag text-black scale-110"
                                : "bg-gray-900/90 border-gray-800 text-gray-400 hover:text-white hover:border-jetlag"
                        )}
                    >
                        <Search size={24} className="group-hover:scale-110 transition-transform" />
                        <span className="text-xs font-black uppercase tracking-widest hidden md:inline">Intelligence Tools</span>
                    </button>
                )}
            </div>

            {/* Info Legend */}
            <div className="absolute top-6 right-6 z-[1000]">
                <div className="bg-gray-900/90 backdrop-blur-md p-3 rounded-2xl border border-gray-800 shadow-2xl">
                    <Info size={18} className="text-gray-500" />
                </div>
            </div>

            {error && (
                <div className="absolute top-24 left-1/2 -translate-x-1/2 z-[2000] bg-red-600/90 backdrop-blur-md text-white px-6 py-3 rounded-full font-bold shadow-2xl border border-red-400/50">
                    GPS Link Offline: {error}
                </div>
            )}
        </div>
    );
};

