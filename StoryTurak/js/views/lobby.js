import { router } from '../router.js';
import { sessionManager } from '../session-manager.js';
import { userManager } from '../user-manager.js';

export default class LobbyView {
    constructor(params) {
        this.campaignId = params.campaignId;
        this.mode = params.mode || 'choice'; // solo, team, choice
        this.isHost = false;
    }

    async render(container) {
        this.container = container;

        if (this.mode === 'solo') {
            await this.startSoloSession();
        } else if (this.mode === 'team') {
            this.renderTeamChoice();
        } else {
            // Fallback if no params provided (e.g. direct nav)
            this.renderInitialChoice();
        }
    }

    async startSoloSession() {
        this.container.innerHTML = `<div class="loading-screen"><p>Kaland előkészítése...</p></div>`;
        try {
            await sessionManager.createSession(this.campaignId, 'solo');
            sessionManager.startSession();
            // Short delay for effect
            setTimeout(() => {
                router.navigate(`game/${this.campaignId}/solo`);
            }, 1000);
        } catch (e) {
            console.error(e);
            this.container.innerHTML = `<div class="error-screen"><p>Hiba: ${e.message}</p><button id="btn-retry">Újra</button></div>`;
            this.container.querySelector('#btn-retry').onclick = () => location.reload();
        }
    }

    renderTeamChoice() {
        this.container.innerHTML = `
            <div class="view-lobby text-center fade-in">
                <h2 class="noir-title">Csapat Összeállítás</h2>
                <div class="lobby-choices mt-lg">
                    <button class="btn btn-block mb-md" id="btn-create">
                        👥 Csapat Indítása (Host)
                    </button>
                    <button class="btn btn-secondary btn-block" id="btn-join">
                        🔗 Csatlakozás Kóddal
                    </button>
                </div>
                <button class="btn-secondary btn-sm mt-lg" id="btn-back">Vissza</button>
            </div>
        `;

        this.container.querySelector('#btn-create').onclick = () => this.createLobby();
        this.container.querySelector('#btn-join').onclick = () => this.showJoinInput();
        this.container.querySelector('#btn-back').onclick = () => router.navigate('campaigns');
    }

    // Legacy/Fallback choice (if someone navigates to /lobby directly)
    renderInitialChoice() {
        // ... (Simplified for this file, redirect to campaigns usually)
        router.navigate('campaigns');
    }

    async createLobby() {
        this.container.innerHTML = `<div class="loading-screen"><p>Szoba létrehozása...</p></div>`;
        try {
            const session = await sessionManager.createSession(this.campaignId, 'team-sync');
            this.isHost = true;
            this.renderLobbyUI(session);
        } catch (e) {
            console.error(e);
            alert('Hiba történt: ' + e.message);
            this.renderTeamChoice();
        }
    }

    showJoinInput() {
        this.container.innerHTML = `
            <div class="view-lobby text-center fade-in">
                <h2 class="noir-title">Csatlakozás</h2>
                <input type="text" id="join-code" class="lobby-input" placeholder="4 jegyű kód" maxlength="4" />
                <button class="btn mt-lg" id="btn-submit-join">Belépés</button>
                <button class="btn-secondary mt-md" id="btn-cancel">Mégse</button>
            </div>
        `;

        this.container.querySelector('#btn-submit-join').onclick = async () => {
            const code = this.container.querySelector('#join-code').value.toUpperCase();
            if (code.length < 4) return alert('Kérlek add meg a 4 jegyű kódot!');

            this.container.innerHTML = `<div class="loading-screen"><p>Csatlakozás...</p></div>`;
            try {
                const session = await sessionManager.joinSession(code);
                this.isHost = false;
                this.renderLobbyUI(session);
            } catch (e) {
                alert(e.message);
                this.showJoinInput();
            }
        };

        this.container.querySelector('#btn-cancel').onclick = () => this.renderTeamChoice();
    }

    renderLobbyUI(session) {
        const updateUI = () => {
            // Re-fetch clean state
            const currentSession = sessionManager.currentSession;
            if (!currentSession) return;

            // FIX: Access user via userManager
            const me = userManager.getCurrentUser();
            const currentUser = currentSession.players.find(p => p.id === me?.id);
            const myReadyState = currentUser ? currentUser.isReady : false;
            const allReady = currentSession.players.every(p => p.isReady);

            const playersList = currentSession.players.map(p => `
                <div class="player-item ${p.isReady ? 'ready' : ''}">
                    <div class="avatar">${p.name[0]}</div>
                    <span style="flex:1">${p.name} ${p.id === currentSession.hostId ? '👑' : ''}</span>
                    <span class="status-icon">${p.isReady ? '✅' : '⏳'}</span>
                </div>
            `).join('');

            this.container.innerHTML = `
                <div class="view-lobby fade-in">
                    <div class="lobby-header">
                        <h3>csapat kód: <span class="lobby-code">${currentSession.id}</span></h3>
                        <p class="mt-sm">Várd meg a többieket!</p>
                    </div>

                    <div class="player-list mt-lg">
                        <h4>Jelenlévők (${currentSession.players.length})</h4>
                        ${playersList}
                    </div>

                    <div class="lobby-footer mt-xl" style="display:flex; flex-direction:column; gap:10px;">
                        <button class="btn ${myReadyState ? 'btn-secondary' : 'btn'}" id="btn-toggle-ready">
                            ${myReadyState ? 'Mégsem' : 'KÉSZ VAGYOK!'}
                        </button>
                        
                        ${this.isHost ?
                    `<button class="btn pulse" id="btn-start-game" ${!allReady ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''}>
                                KÜLDETÉS INDÍTÁSA
                            </button>` :
                    `<p class="blink text-center">Várakozás az indításra...</p>`
                }
                    </div>
                </div>
            `;

            // Re-attach listeners is inefficient here but robust
            this.container.querySelector('#btn-toggle-ready').onclick = () => {
                sessionManager.toggleReady();
            };

            if (this.isHost) {
                const startBtn = this.container.querySelector('#btn-start-game');
                if (startBtn) {
                    startBtn.onclick = () => {
                        sessionManager.startSession();
                        router.navigate(`game/${this.campaignId}/team`);
                    };
                }
            }
        };

        // Initial render
        updateUI();

        // Listen for updates
        sessionManager.onSessionUpdate = (updatedSession) => {
            if (updatedSession.status === 'active') {
                router.navigate(`game/${updatedSession.campaignId}/team`);
            } else {
                updateUI();
            }
        };
    }

    destroy() {
        sessionManager.onSessionUpdate = null;
    }
}
