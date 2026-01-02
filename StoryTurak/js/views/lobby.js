import { router } from '../router.js';
import { sessionManager } from '../session-manager.js';

export default class LobbyView {
    constructor(params) {
        this.campaignId = params.campaignId;
        this.isHost = false;
        this.updateInterval = null;
    }

    async render(container) {
        this.container = container;
        this.renderInitialChoice();
    }

    renderInitialChoice() {
        this.container.innerHTML = `
            <div class="view-lobby text-center fade-in">
                <h2 class="noir-title">Hogyan vágsz bele?</h2>
                <div class="lobby-choices mt-lg">
                    <button class="btn btn-block mb-md" id="btn-solo">
                        🕵️‍♂️ Egyedül (Szóló)
                    </button>
                    <button class="btn btn-secondary btn-block mb-md" id="btn-create">
                        👥 Csapat Indítása
                    </button>
                    <button class="btn btn-secondary btn-block" id="btn-join">
                        🔗 Csatlakozás Csapathoz
                    </button>
                </div>
                <button class="btn-secondary btn-sm mt-lg" id="btn-back">Vissza</button>
            </div>
        `;

        this.container.querySelector('#btn-solo').onclick = () => {
            router.navigate('game', { storyId: this.campaignId, mode: 'solo' });
        };

        this.container.querySelector('#btn-create').onclick = () => this.createLobby();
        this.container.querySelector('#btn-join').onclick = () => this.showJoinInput();
        this.container.querySelector('#btn-back').onclick = () => router.navigate('browser');
    }

    async createLobby() {
        this.container.innerHTML = `<div class="loading-screen"><p>Csapat létrehozása...</p></div>`;
        try {
            const session = await sessionManager.createSession(this.campaignId);
            this.isHost = true;
            this.renderLobby(session);
        } catch (e) {
            console.error(e);
            alert('Hiba történt.');
            this.renderInitialChoice();
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
                this.renderLobby(session);
            } catch (e) {
                alert(e.message);
                this.showJoinInput();
            }
        };

        this.container.querySelector('#btn-cancel').onclick = () => this.renderInitialChoice();
    }

    renderLobby(session) {
        const currentUser = session.players.find(p => p.id === sessionManager.currentUser.id);
        const myReadyState = currentUser ? currentUser.isReady : false;

        const allReady = session.players.every(p => p.isReady);

        const playersList = session.players.map(p => `
            <div class="player-item ${p.isReady ? 'ready' : ''}">
                <div class="avatar">${p.name[0]}</div>
                <span style="flex:1">${p.name} ${p.id === session.hostId ? '👑' : ''}</span>
                <span class="status-icon">${p.isReady ? '✅' : '⏳'}</span>
            </div>
        `).join('');

        this.container.innerHTML = `
            <div class="view-lobby fade-in">
                <div class="lobby-header">
                    <h3>CSAPAT KÓD</h3>
                    <div class="lobby-code">${session.id}</div>
                    <p class="mt-sm">Oszt meg ezt a kódot a társaiddal!</p>
                </div>

                <div class="player-list mt-lg">
                    <h4>Jelenlévők (${session.players.length})</h4>
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

        this.container.querySelector('#btn-toggle-ready').onclick = () => {
            sessionManager.toggleReady();
        };

        if (this.isHost) {
            const startBtn = this.container.querySelector('#btn-start-game');
            if (startBtn) {
                startBtn.onclick = () => {
                    try {
                        sessionManager.startSession();
                        router.navigate('game', { storyId: session.campaignId, mode: 'multi', sessionId: session.id });
                    } catch (e) {
                        alert(e.message);
                    }
                };
            }
        }

        // Auto-navigate if game started
        sessionManager.onSessionUpdate = (updatedSession) => {
            if (updatedSession.status === 'active') {
                router.navigate('game', { storyId: updatedSession.campaignId, mode: 'multi', sessionId: updatedSession.id });
            } else {
                this.renderLobby(updatedSession);
            }
        };
    }

    destroy() {
        // Cleanup if needed
        sessionManager.onSessionUpdate = null;
    }
}
