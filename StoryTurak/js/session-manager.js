import { userManager } from './user-manager.js';

export class SessionManager {
    constructor() {
        this.channel = new BroadcastChannel('storyturak_game_sync');
        this.currentSession = this.loadSession() || null;
        this.onSessionUpdate = null;
        this.onInputStatus = null;

        this.channel.onmessage = (event) => this.handleMessage(event.data);
    }

    loadSession() {
        const stored = localStorage.getItem('storyturak_session');
        return stored ? JSON.parse(stored) : null;
    }

    saveSession() {
        if (this.currentSession) {
            localStorage.setItem('storyturak_session', JSON.stringify(this.currentSession));
        } else {
            localStorage.removeItem('storyturak_session');
        }
    }

    async createSession(campaignId, mode = 'solo') {
        const user = userManager.getCurrentUser();
        if (!user) throw new Error("Jelentkezz be a játék indításához!");

        // Simulate network
        await this._delay(300);

        const sessionId = Math.random().toString(36).substring(2, 6).toUpperCase();

        const hostPlayer = {
            ...user, // Copy user data
            isReady: mode === 'solo' // Auto-ready if solo
        };

        this.currentSession = {
            id: sessionId,
            hostId: hostPlayer.id,
            campaignId: campaignId,
            mode: mode, // 'solo', 'team-sync', 'team-async'
            players: [hostPlayer],
            state: {
                currentNode: null, // Will be set by StoryEngine
                inventory: [],
                startedAt: new Date().toISOString()
            },
            status: 'waiting' // waiting, active, completed
        };

        // If solo, we can even auto-start here or let the view do it. 
        // LobbyView calls startSession() which checks readiness. So isReady=true is key.

        this.saveSession();
        this.broadcastState();
        return this.currentSession;
    }

    async joinSession(sessionId) {
        const user = userManager.getCurrentUser();
        if (!user) throw new Error("Jelentkezz be a játékhoz!");

        await this._delay(500);

        // Prepare player object
        const playerObj = { ...user, isReady: false };

        // Request session info from network (Broadcast)
        this.sendMessage({ type: 'JOIN_REQUEST', sessionId, user: playerObj });

        // Wait for response (timeout 2s)
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                // Check if we managed to join via handleMessage
                if (this.currentSession && this.currentSession.id === sessionId) {
                    resolve(this.currentSession);
                } else {
                    reject(new Error("Nem található a szoba (vagy a Host nem elérhető)"));
                }
            }, 2000);

            // Temporary listener for immediate response
            const responseHandler = (event) => {
                if (event.data.type === 'SESSION_STATE' && event.data.session.id === sessionId) {
                    // Check if we are in the player list
                    const isInList = event.data.session.players.find(p => p.id === playerObj.id);
                    if (isInList) {
                        clearTimeout(timeout);
                        // State will be updated by handleMessage
                        resolve(event.data.session);
                        this.channel.removeEventListener('message', responseHandler);
                    }
                }
            };
            this.channel.addEventListener('message', responseHandler);
        });
    }

    leaveSession() {
        this.currentSession = null;
        this.saveSession();
        this._notify();
    }

    toggleReady() {
        if (!this.currentSession) return;
        const user = userManager.getCurrentUser();
        if (!user) return;

        // If I am the host, I update state directly
        if (this.currentSession.hostId === user.id) {
            this._handleReadyLogic(user.id);
        } else {
            // If I am client, I request it
            this.sendMessage({ type: 'TOGGLE_READY', sessionId: this.currentSession.id, userId: user.id });
        }
    }

    _handleReadyLogic(userId) {
        const p = this.currentSession.players.find(pl => pl.id === userId);
        if (p) {
            p.isReady = !p.isReady;
            this.saveSession();
            this.broadcastState();
        }
    }

    startSession() {
        if (!this.currentSession) return;

        // Check if all players are ready
        const allReady = this.currentSession.players.every(p => p.isReady);
        if (!allReady) {
            throw new Error("Minden játékosnak készen kell állnia az indításhoz!");
        }

        this.currentSession.status = 'active';
        this.saveSession();
        this.broadcastState();
    }

    updateStoryState(nodeId) {
        if (!this.currentSession) return;
        this.currentSession.state.currentNode = nodeId;
        this.saveSession();
        this.broadcastState();
    }

    completeSession() {
        if (!this.currentSession) return;
        this.currentSession.status = 'completed';
        this.currentSession.completedAt = new Date().toISOString();

        // Update user stats
        userManager.updateStats(0, this.currentSession.campaignId); // Distance would be calculated dynamically

        this.saveSession();
        this.broadcastState();
    }

    sendInputStatus(isTyping) {
        if (!this.currentSession) return;
        const user = userManager.getCurrentUser();
        if (!user) return;

        this.sendMessage({
            type: 'INPUT_STATUS',
            sessionId: this.currentSession.id,
            user: user,
            isTyping: isTyping
        });
    }

    handleMessage(msg) {
        // console.log('Received:', msg.type);

        if (msg.type === 'JOIN_REQUEST') {
            // IF I am the host of this session
            const user = userManager.getCurrentUser();
            if (this.currentSession &&
                this.currentSession.hostId === user?.id &&
                this.currentSession.id === msg.sessionId) {

                // Add player if not exists
                if (!this.currentSession.players.find(p => p.id === msg.user.id)) {
                    this.currentSession.players.push(msg.user);
                    this.saveSession();
                    this.broadcastState();
                } else {
                    // Just rebroadcast state so they get it
                    this.broadcastState();
                }
            }
        }
        else if (msg.type === 'TOGGLE_READY') {
            const user = userManager.getCurrentUser();
            // Host Authority Logic
            if (this.currentSession && this.currentSession.hostId === user?.id && this.currentSession.id === msg.sessionId) {
                this._handleReadyLogic(msg.userId);
            }
        }
        else if (msg.type === 'INPUT_STATUS') {
            if (this.currentSession && this.currentSession.id === msg.sessionId) {
                // Notify listeners (UI) about who is typing
                if (this.onInputStatus) {
                    this.onInputStatus(msg.user, msg.isTyping);
                }
            }
        }
        else if (msg.type === 'SESSION_STATE') {
            const user = userManager.getCurrentUser();
            // Update local state if it matches our session content
            if (this.currentSession && this.currentSession.id === msg.session.id) {
                this.currentSession = msg.session;
                this.saveSession();
                this._notify();
            }
            // Or if we are trying to join and we are in the list
            else if (!this.currentSession && msg.session.players.find(p => p.id === user?.id)) {
                this.currentSession = msg.session;
                this.saveSession();
                this._notify();
            }
        }
        // Force refresh on reconnect logic could go here
    }

    broadcastState() {
        if (!this.currentSession) return;
        this.sendMessage({
            type: 'SESSION_STATE',
            session: this.currentSession
        });
        this._notify();
    }

    sendMessage(data) {
        this.channel.postMessage(data);
    }

    _notify() {
        if (this.onSessionUpdate) {
            this.onSessionUpdate(this.currentSession);
        }
    }

    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

export const sessionManager = new SessionManager();
