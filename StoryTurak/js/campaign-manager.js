import { userManager } from './user-manager.js';

export class CampaignManager {
    constructor() {
        this.campaigns = [];
        this.loadCampaigns(); // In real app, fetch from server
    }

    async loadCampaigns() {
        // Mock data matching the product brief requirements
        this.campaigns = [
            {
                id: 'intro-01',
                title: 'A Vigadó Árnyéka',
                description: 'Rövid bevezető kaland Budapest szívében.',
                difficulty: 'Könnyű',
                distance: '1.5 km',
                duration: '30 perc',
                location: 'Budapest, V. kerület',
                image: 'assets/vigado_noir.png',
                tags: ['Tutorial', 'Misztikus']
            },
            {
                id: 'city-secrets-01',
                title: 'A Néma Harangok',
                description: 'Hosszú nyomozás a budai oldalon. Készülj fel egy kiadós sétára.',
                difficulty: 'Közepes',
                distance: '5.0 km',
                duration: '2-3 óra',
                location: 'Budapest, I. kerület',
                image: 'assets/buda_castle.png', // Placeholder
                tags: ['Nyomozás', 'Történelmi']
            },
            {
                id: 'marathon-01',
                title: 'A Duna Menti Futár',
                description: 'Egész napos kihívás a legkitartóbbaknak.',
                difficulty: 'Nehéz',
                distance: '12 km',
                duration: '5+ óra',
                location: 'Budapest, Duna-part',
                image: 'assets/danube.png', // Placeholder
                tags: ['Kihívás', 'Sportos']
            }
        ];
    }

    getAllCampaigns() {
        return this.campaigns;
    }

    getCampaign(id) {
        return this.campaigns.find(c => c.id === id);
    }

    async startCampaign(campaignId, mode = 'solo') {
        const campaign = this.getCampaign(campaignId);
        if (!campaign) throw new Error('Campaign not found');

        // Logic to initialize tracking for this specific playthrough
        // Usually handled by SessionManager, but CampaignManager might track "Active Campaigns"
        console.log(`Starting campaign ${campaignId} in ${mode} mode`);

        return campaign;
    }
}

export const campaignManager = new CampaignManager();
