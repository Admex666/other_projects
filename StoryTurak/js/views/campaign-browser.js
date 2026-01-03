import { campaignManager } from '../campaign-manager.js';
import { userManager } from '../user-manager.js';
import { router } from '../router.js';

export class CampaignBrowser {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'view campaign-browser';
    }

    async render(container) {
        const campaigns = campaignManager.getAllCampaigns();
        const user = userManager.getCurrentUser();

        this.container.innerHTML = `
            <header>
                <h1>Kalandok</h1>
                <div class="user-info">
                    <span>${user ? user.name : 'Vendég'}</span>
                    <button id="btn-profile" class="icon-btn">👤</button>
                </div>
            </header>
            <div class="campaign-list">
                ${campaigns.map(c => this._renderCard(c)).join('')}
            </div>
        `;

        this.container.querySelector('#btn-profile').addEventListener('click', () => {
            router.navigate('profile');
        });

        this.container.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.dataset.id;
                this._selectCampaign(id);
            });
        });

        container.innerHTML = '';
        container.appendChild(this.container);
    }

    _renderCard(campaign) {
        return `
            <div class="campaign-card">
                <div class="card-image" style="background-image: url('${campaign.image}')"></div>
                <div class="card-content">
                    <div class="tags">
                        ${campaign.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                    </div>
                    <h2>${campaign.title}</h2>
                    <p>${campaign.description}</p>
                    <div class="meta">
                        <span>📏 ${campaign.distance}</span>
                        <span>⏱ ${campaign.duration}</span>
                        <span>⭐ ${campaign.difficulty}</span>
                    </div>
                    <button class="play-btn btn primary-btn" data-id="${campaign.id}">NYOMOZÁS ➜</button>
                </div>
            </div>
        `;
    }

    _selectCampaign(id) {
        // Show mode selection modal
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <h2>Hogyan szeretnél játszani?</h2>
                <div class="mode-options">
                    <button class="mode-btn" data-mode="solo">
                        <h3>Egyedül</h3>
                        <p>Nyomozz a saját tempódban.</p>
                    </button>
                    <button class="mode-btn" data-mode="team">
                        <h3>Csapatban</h3>
                        <p>Hívd meg barátaidat és oldjátok meg közösen.</p>
                    </button>
                </div>
                <button class="close-btn">Mégse</button>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.close-btn').addEventListener('click', () => modal.remove());

        modal.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                router.navigate(`lobby/${id}/${mode}`);
                modal.remove();
            });
        });
    }
    _showGlobalJoinModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <h2 class="noir-title">Csatlakozás</h2>
                <p>Add meg a 4 jegyű kódot a belépéshez:</p>
                <input type="text" id="global-join-code" class="lobby-input" placeholder="KÓD" maxlength="4" />
                <button class="btn mt-lg" id="btn-global-submit">Belépés</button>
                <button class="close-btn">Mégse</button>
            </div>
        `;

        document.body.appendChild(modal);
        modal.querySelector('.close-btn').addEventListener('click', () => modal.remove());

        modal.querySelector('#btn-global-submit').onclick = async () => {
            const code = modal.querySelector('#global-join-code').value.toUpperCase();
            if (code.length < 4) return alert('Kérlek add meg a kódot!');

            const btn = modal.querySelector('#btn-global-submit');
            btn.disabled = true;
            btn.textContent = "Keresés...";

            try {
                // Import helper to avoid circular dep if needed, or use global
                const { sessionManager } = await import('../session-manager.js');
                const session = await sessionManager.joinSession(code);

                // Success! Navigate to the correct lobby
                modal.remove();
                router.navigate(`lobby/${session.campaignId}/team`);
            } catch (e) {
                alert(e.message);
                btn.disabled = false;
                btn.textContent = "Belépés";
            }
        };
    }
}
