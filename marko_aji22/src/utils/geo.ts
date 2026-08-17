import { Coordinates, ProximityState } from '../types/quest';

/**
 * Calculates distance between two GPS coordinates in meters using the Haversine formula
 */
export function calculateDistanceMeters(coord1: Coordinates, coord2: Coordinates): number {
  const R = 6371e3; // Earth radius in meters
  const phi1 = (coord1.lat * Math.PI) / 180;
  const phi2 = (coord2.lat * Math.PI) / 180;
  const deltaPhi = ((coord2.lat - coord1.lat) * Math.PI) / 180;
  const deltaLambda = ((coord2.lng - coord1.lng) * Math.PI) / 180;

  const a =
    Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return Math.round(R * c);
}

/**
 * Calculates bearing from coord1 to coord2 in degrees (0 - 360)
 */
export function calculateBearing(coord1: Coordinates, coord2: Coordinates): number {
  const phi1 = (coord1.lat * Math.PI) / 180;
  const phi2 = (coord2.lat * Math.PI) / 180;
  const deltaLambda = ((coord2.lng - coord1.lng) * Math.PI) / 180;

  const y = Math.sin(deltaLambda) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);

  const theta = Math.atan2(y, x);
  const bearing = ((theta * 180) / Math.PI + 360) % 360;

  return Math.round(bearing);
}

/**
 * Maps distance in meters to Hot / Cold proximity state
 */
export function getProximityState(
  distanceMeters: number,
  thresholds = { burning: 30, hot: 100, warm: 250, cold: 500 }
): ProximityState {
  if (distanceMeters <= thresholds.burning) return 'burning';
  if (distanceMeters <= thresholds.hot) return 'hot';
  if (distanceMeters <= thresholds.warm) return 'warm';
  if (distanceMeters <= thresholds.cold) return 'cold';
  return 'freezing';
}

export function getProximityInfo(state: ProximityState) {
  switch (state) {
    case 'burning':
      return {
        label: 'LÁNGOLSZ! MEGÉRKEZTÉL!',
        description: '30 méteren belül vagy a célhoz! A titkos helyszín feltárult!',
        color: 'text-rose-400',
        bgGlow: 'bg-rose-500/20 border-rose-500/80 shadow-[0_0_35px_rgba(244,63,94,0.4)]',
        badgeBg: 'bg-rose-500 text-white',
        icon: '🔥',
        radarColor: '#f43f5e'
      };
    case 'hot':
      return {
        label: 'FORRÓ! NAGYON KÖZEL VAGY!',
        description: 'Már szinte látod a bejáratot! Még pár lépés...',
        color: 'text-amber-400',
        bgGlow: 'bg-amber-500/20 border-amber-500/80 shadow-[0_0_25px_rgba(245,158,11,0.35)]',
        badgeBg: 'bg-amber-500 text-black',
        icon: '♨️',
        radarColor: '#f59e0b'
      };
    case 'warm':
      return {
        label: 'MELEGEDIK...',
        description: 'Jó irányba tartasz, közeledsz a célhoz!',
        color: 'text-yellow-300',
        bgGlow: 'bg-yellow-500/15 border-yellow-500/60 shadow-[0_0_20px_rgba(234,179,8,0.25)]',
        badgeBg: 'bg-yellow-500 text-black',
        icon: '🌤️',
        radarColor: '#eab308'
      };
    case 'cold':
      return {
        label: 'HIDEG...',
        description: 'Még távol vagy, de a radar már észleli a jelet.',
        color: 'text-cyan-400',
        bgGlow: 'bg-cyan-500/10 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]',
        badgeBg: 'bg-cyan-600 text-white',
        icon: '🧊',
        radarColor: '#06b6d4'
      };
    case 'freezing':
    default:
      return {
        label: 'JEGESEN HIDEG...',
        description: 'Még messze jársz a titkos helyszíntől. Indulj a megadott irányba!',
        color: 'text-blue-400',
        bgGlow: 'bg-blue-500/10 border-blue-500/40',
        badgeBg: 'bg-blue-600 text-white',
        icon: '❄️',
        radarColor: '#3b82f6'
      };
  }
}
