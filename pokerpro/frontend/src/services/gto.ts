
import api from './api';

export interface SolverResult {
    solver?: string;
    strategy: Record<string, number>;
    evs?: Record<string, number>;
    equity: number;
    recommended_action: string;
    explanation?: string;
    details?: {
        equity_histogram: number[];
        iterations?: number;
    };
}

export interface SolverParams {
    hero_hand: string;
    board?: string;
    villains?: number;
}

export interface DrillScenario {
    hero_hand: string;
    board: string;
    villains: number;
    pot: number;
    stack: number;
    facing_bet: number;
    description: string;
}

export const gtoService = {
    // Solve a GTO spot
    solveSpot: async (data: {
        hero_hand: string;
        board: string;
        villains: number;
        pot?: number;
        stack?: number;
        facing_bet?: number;
    }) => {
        const response = await api.post('/gto/solve', data);
        return response.data;
    },

    // Get a drill scenario
    getDrill: async (drillType: string = 'random'): Promise<DrillScenario> => {
        const response = await api.get(`/gto/drill?type=${drillType}`);
        return response.data;
    }
};
