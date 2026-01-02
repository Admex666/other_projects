export class SessionManager {
    constructor() {
        this.channel = new BroadcastChannel('storyturak_game_sync');
        this.currentSession = null;
        this.currentUser = {
            id: 'user-' + Math.floor(Math.random() * 10000),
            name: 'Játékos ' + Math.floor(Math.random() * 100)
        };
        this.onSessionUpdate = null;

        this.channel.onmessage = (event) => this.handleMessage(event.data);
    }

    async createSession(campaignId) {
        // Simulate network
        await this._delay(300);

        const sessionId = Math.random().toString(36).substring(2, 6).toUpperCase();

        // Add ready state to user
        this.currentUser.isReady = false;

        this.currentSession = {
            id: sessionId,
            hostId: this.currentUser.id,
            campaignId: campaignId,
            players: [this.currentUser],
            state: {
                currentNode: 'node-1', // Default start
                inventory: []
            },
            status: 'waiting'
        };

        this.broadcastState();
        return this.currentSession;
    }

    async joinSession(sessionId) {
        await this._delay(500);
        this.currentUser.isReady = false; // Reset ready state

        // Request session info from network (Broadcast)
        this.sendMessage({ type: 'JOIN_REQUEST', sessionId, user: this.currentUser });

        // Wait for response (timeout 2s)
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                // Determine if we found it (handled by onmessage)
                if (this.currentSession && this.currentSession.id === sessionId) {
                    resolve(this.currentSession);
                } else {
                    reject(new Error("Nem található a szoba (vagy a Host nem elérhető)"));
                }
            }, 2000);

            // Temporary listener for immediate response
            const responseHandler = (event) => {
                if (event.data.type === 'SESSION_STATE' && event.data.session.id === sessionId) {
                    // We got in! (Logic handled in handleMessage, just resolve here)
                    clearTimeout(timeout);
                    resolve(event.data.session);
                    this.channel.removeEventListener('message', responseHandler);
                }
            };
            this.channel.addEventListener('message', responseHandler);
        });
    }

    toggleReady() {
        if (!this.currentSession) return;
        this.sendMessage({ type: 'TOGGLE_READY', sessionId: this.currentSession.id, userId: this.currentUser.id });
    }

    startSession() {
        if (!this.currentSession) return;

        // Check if all players are ready
        const allReady = this.currentSession.players.every(p => p.isReady);
        if (!allReady) {
            throw new Error("Minden játékosnak készen kell állnia az indításhoz!");
        }

        this.currentSession.status = 'active';
        this.broadcastState();
    }

    updateStoryState(nodeId) {
        if (!this.currentSession) return;
        this.currentSession.state.currentNode = nodeId;
        this.broadcastState();
    }

    sendInputStatus(isTyping) {
        if (!this.currentSession) return;
        this.sendMessage({
            type: 'INPUT_STATUS',
            sessionId: this.currentSession.id,
            user: this.currentUser,
            isTyping: isTyping
        });
    }

    handleMessage(msg) {
        // console.log('Received:', msg.type);

        if (msg.type === 'JOIN_REQUEST') {
            // IF I am the host of this session
            if (this.currentSession &&
                this.currentSession.hostId === this.currentUser.id &&
                this.currentSession.id === msg.sessionId) {

                // Add player if not exists
                if (!this.currentSession.players.find(p => p.id === msg.user.id)) {
                    this.currentSession.players.push(msg.user);
                    this.broadcastState();
                } else {
                    // Just rebroadcast state so they get it
                    this.broadcastState();
                }
            }
        }
        else if (msg.type === 'TOGGLE_READY') {
            // The logic: if I am the Host, I update the authoritative state and broadcast it back.
            // If I am NOT the host, I do nothing here (unless I trust the peer fully, but better to wait for Host's auth update).
            // Actually for true P2P, users update themselves. But lets stick to Host-Authority to avoid race conditions easily.

            if (this.currentSession && this.currentSession.hostId === this.currentUser.id && this.currentSession.id === msg.sessionId) {
                const p = this.currentSession.players.find(pl => pl.id === msg.userId);
                if (p) {
                    p.isReady = !p.isReady;
                    this.broadcastState();
                }
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
            // Update local state if it matches our session content
            if (this.currentSession && this.currentSession.id === msg.session.id) {
                this.currentSession = msg.session;
                this._notify();
            }
            // Or if we are trying to join
            else if (!this.currentSession && msg.session.players.find(p => p.id === this.currentUser.id)) {
                this.currentSession = msg.session;
                this._notify();
            }
        }
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
