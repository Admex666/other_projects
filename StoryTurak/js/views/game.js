import { router } from '../router.js';
import { storyEngine } from '../story-engine.js';
import { gpsManager } from '../gps-manager.js';
import { sessionManager } from '../session-manager.js';

export default class GameView {
    constructor(params) {
        console.log("GameView params:", params);
        this.storyId = params.campaignId || params.storyId; // Support both for safety
        this.mode = params.mode || 'solo'; // solo, multi
        this.sessionId = params.sessionId;

        this.container = null;
        this.map = null;
        this.userMarker = null;
        this.targetMarker = null;
        this.gpsListener = null;
    }

    async render(container) {
        this.container = container;
        container.innerHTML = `
            <div class="view-game">
                <div class="loading-screen">
                    <p>Akták betöltése...</p>
                </div>
            </div>
        `;


        try {
            // Safety check for ID
            if (!this.storyId || this.storyId === 'undefined') {
                if (this.mode === 'multi' || this.mode === 'team') {
                    const session = sessionManager.currentSession;
                    if (session && session.campaignId) {
                        this.storyId = session.campaignId;
                    } else {
                        throw new Error("Hiányzó Story ID!");
                    }
                } else {
                    throw new Error("Hiányzó Story ID!");
                }
            }

            // Fetch story data
            const response = await fetch(`data/${this.storyId}.json`);
            if (!response.ok) throw new Error('Story not found');
            const storyData = await response.json();

            // Initialize Engine
            storyEngine.loadStory(storyData);
            storyEngine.onStoryUpdate = (node) => this.renderNode(node);

            // Sync Outbound
            if (this.mode === 'multi') {
                storyEngine.onStateChange = (nodeId) => {
                    import('../session-manager.js').then(({ sessionManager }) => {
                        sessionManager.updateStoryState(nodeId);
                    });
                };
            }

            // Start GPS and Engine
            storyEngine.start();

            // Sync with Session if Multi
            if (this.mode === 'multi') {
                sessionManager.onSessionUpdate = (session) => {
                    // Update UI (players count)
                    this.updateTeamUI(session);

                    // Sync Story Node if changed remotely
                    if (session.state.currentNode !== storyEngine.currentNodeId) {
                        storyEngine.advance(session.state.currentNode, true); // true = silent/remote
                    }
                };

                // Handle Input Status
                sessionManager.onInputStatus = (user, isTyping) => {
                    // Ignore self
                    import('../user-manager.js').then(({ userManager }) => {
                        const me = userManager.getCurrentUser();
                        if (user.id === me.id) return;

                        const inputEl = this.container.querySelector('#story-input');
                        const feedbackEl = this.container.querySelector('#input-feedback');

                        if (inputEl) {
                            if (isTyping) {
                                inputEl.disabled = true;
                                inputEl.placeholder = `${user.name} épp ír...`;
                                if (feedbackEl) feedbackEl.textContent = "🔒 Egyszerre csak egy ügynök írhat.";
                            } else {
                                inputEl.disabled = false;
                                inputEl.placeholder = "Válasz...";
                                if (feedbackEl) feedbackEl.textContent = "";
                            }
                        }
                    });
                };
            }

            // Subscribe to GPS for UI updates (Map)
            this.gpsListener = (pos) => this.updateMapPosition(pos);
            gpsManager.subscribe(this.gpsListener);

        } catch (error) {
            console.error(error);
            container.innerHTML = `<div class="error">Hiba: Az akta nem elérhető.</div>`;
        }
    }

    updateTeamUI(session) {
        const statusEl = this.container.querySelector('.team-status');
        if (statusEl) {
            statusEl.innerHTML = `👥 Csapat kód: <strong>${session.id}</strong> | Online: ${session.players.length}`;
        }
    }

    renderNode(node) {
        if (!node) {
            alert('Gratulálunk! Az ügy lezárva.');
            router.navigate('browser');
            return;
        }

        let content = '';

        // Map Container
        content += `<div id="map"></div>`;

        // Team Status (Multiplayer)
        if (this.mode === 'multi') {
            content += `
                <div class="team-status" style="margin-bottom: 10px; font-size: 0.8rem; color: var(--color-accent); text-align: center;">
                    👥 Csapat kód: <strong>${this.sessionId}</strong> | Online: 2
                </div>
            `;
        }

        // Text
        content += `<div class="story-text"><p>${node.text}</p></div>`;

        // Interaction
        if (node.type === 'narrative') {
            content += `<button class="btn mt-lg actions-btn" data-action="next">${node.buttonText || 'Tovább'}</button>`;
        }
        else if (node.type === 'location_wait') {
            content += `
                <div class="location-status mt-lg">
                    <p class="blink">Célkövetés aktív...</p>
                    <button class="btn-secondary btn-sm mt-lg actions-btn" data-action="skip">${node.fallbackButton || 'Skip'}</button>
                </div>
            `;
        }
        else if (node.type === 'input') {
            content += `
                <div class="input-group mt-lg">
                    <input type="text" id="story-input" placeholder="Válasz..." />
                    <button class="btn actions-btn" data-action="submit">Ellenőrzés</button>
                    ${node.hint ? `<button class="btn-secondary btn-sm ml-sm actions-btn" data-action="hint">💡 Súgó</button>` : ''}
                    <p id="input-feedback" class="error-text"></p>
                </div>
            `;
        }
        else if (node.type === 'choice') {
            content += `<div class="choices-container mt-lg" style="display:flex; flex-direction:column; gap:10px;">`;
            node.choices.forEach(choice => {
                // Check if choice has condition
                const isVisible = choice.condition ? storyEngine.checkCondition(choice.condition) : true;
                if (isVisible) {
                    content += `<button class="btn btn-block actions-btn" data-action="choose" data-target="${choice.next}">${choice.text}</button>`;
                }
            });
            content += `</div>`;
        }

        this.container.innerHTML = `
            <div class="view-game active-story">
                ${content}
            </div>
        `;

        // Init Map after DOM insertion
        this.initMap(node);

        // Event Listeners
        this.container.querySelectorAll('.actions-btn').forEach(btn => {
            btn.onclick = () => {
                const action = btn.dataset.action;
                if (action === 'next' || action === 'skip') {
                    if (node.next) {
                        storyEngine.advance(node.next);
                    } else {
                        // End of story
                        alert('Gratulálunk! Az ügy lezárva.');
                        router.navigate('browser');
                    }
                } else if (action === 'submit') {
                    const inputVal = this.container.querySelector('#story-input').value;
                    const result = storyEngine.processInput(inputVal);
                    if (result.success) {
                        // Clear lock if we submitted
                        if (this.mode === 'multi') sessionManager.sendInputStatus(false);
                    } else {
                        const fb = this.container.querySelector('#input-feedback');
                        fb.textContent = result.message;
                        fb.classList.add('shake');
                        setTimeout(() => fb.classList.remove('shake'), 500);
                    }
                } else if (action === 'hint') {
                    const hint = storyEngine.getHint();
                    if (hint) {
                        const fb = this.container.querySelector('#input-feedback');
                        fb.textContent = "Súgó: " + hint;
                        fb.style.color = 'var(--color-accent)';
                    }
                } else if (action === 'choose') {
                    const targetNode = btn.dataset.target;
                    storyEngine.advance(targetNode);
                }
            };
        });

        // Input Focus Listeners for Multi
        const inputField = this.container.querySelector('#story-input');
        if (inputField && this.mode === 'multi') {
            inputField.addEventListener('focus', () => sessionManager.sendInputStatus(true));
            inputField.addEventListener('blur', () => {
                // Only clear if empty? Or always?
                // Simple lockout: unlock on blur
                sessionManager.sendInputStatus(false);
            });
        }
    }

    initMap(node) {
        if (!window.L) return; // Leaflet not loaded

        // Default to Budapest center if no GPS yet
        const startPos = gpsManager.currentPosition
            ? [gpsManager.currentPosition.lat, gpsManager.currentPosition.lng]
            : [47.4979, 19.0402];

        if (!this.map) {
            this.map = L.map('map', {
                zoomControl: false,
                attributionControl: false
            }).setView([center.lat, center.lng], 15);

            // Dark Themed Map via CartoDB
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                maxZoom: 19
            }).addTo(this.map);

            // Custom User Marker
            const userIcon = L.divIcon({
                className: 'map-user-marker',
                html: '<div class="pulse-ring"></div><div class="user-dot"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            this.userMarker = L.marker([center.lat, center.lng], { icon: userIcon }).addTo(this.map);
        } else {
            this.map.setView([center.lat, center.lng], 15);
        }

        // Target Marker if location_wait
        if (node.type === 'location_wait' && node.targetLocation) {
            const targetIcon = L.divIcon({
                className: 'map-target-marker',
                html: '🎯',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });

            L.marker([node.targetLocation.lat, node.targetLocation.lng], { icon: targetIcon })
                .addTo(this.map)
                .bindPopup("Célterület")
                .openPopup();
        }
    }

    updateMapPosition(pos) {
        if (!this.map || !this.userMarker) return;

        const newLatLng = [pos.lat, pos.lng];
        this.userMarker.setLatLng(newLatLng);
    }

    destroy() {
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
    }
}
