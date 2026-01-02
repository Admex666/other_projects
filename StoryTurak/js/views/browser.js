import { router } from '../router.js';

export default class BrowserView {
    constructor() {
        // Mock data for now
        this.campaigns = [
            {
                id: 'intro-01',
                title: 'A Vigadó Árnyéka',
                type: 'Noir Krimi',
                location: 'Budapest, Belváros',
                distance: '3 km',
                time: '45-60 perc',
                intensity: 'Vezetett',
                image: 'assets/story-bg-1.jpg' // Placeholder
            },
            {
                id: 'forest-01',
                title: 'Az Elfeledett Ösvény',
                type: 'Misztikus',
                location: 'Budai-hegység',
                distance: '8 km',
                time: '2-3 óra',
                intensity: 'Felfedezős',
                image: 'assets/story-bg-2.jpg'
            }
        ];
    }

    async render(container) {
        let cardsHtml = this.campaigns.map(c => `
            <div class="campaign-card" data-id="${c.id}">
                <div class="card-header">
                    <span class="badge badge-type">${c.type}</span>
                    <span class="badge badge-dist">${c.distance}</span>
                </div>
                <div class="card-body">
                    <h3>${c.title}</h3>
                    <p class="location"><i class="icon-map"></i> ${c.location}</p>
                    <div class="meta">
                        <span>⏱ ${c.time}</span>
                        <span>🔥 ${c.intensity}</span>
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-sm">Kiválaszt</button>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="view-browser">
                <header class="app-header">
                    <h2>Aktuális Ügyek</h2>
                    <p>Válassz történetet a kezdéshez</p>
                </header>
                <div class="campaign-list">
                    ${cardsHtml}
                </div>
            </div>
        `;

        // Add event listeners
        container.querySelectorAll('.campaign-card').forEach(card => {
            card.onclick = () => {
                const id = card.dataset.id;
                console.log(`Selected campaign: ${id}`);
                // Go to Lobby first
                router.navigate('lobby', { campaignId: id });
            };
        });
    }
}
