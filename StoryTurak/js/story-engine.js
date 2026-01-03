import { gpsManager } from './gps-manager.js';

export class StoryEngine {
    constructor() {
        this.storyData = null;
        this.currentNodeId = null;
        this.state = {}; // Game state variables (inventory, flags)
        this.onStoryUpdate = null; // Callback for UI
        this.onStateChange = null; // Callback for sync
        this.history = []; // Track visited nodes
    }

    loadStory(storyJson) {
        this.storyData = storyJson;
        this.currentNodeId = this.storyData.startNode;
        this.state = { ...this.storyData.initialState };
        this.history = [];
        console.log('Story loaded:', this.storyData.title);
    }

    start() {
        if (!this.storyData) return;

        // Start GPS tracking
        gpsManager.start();
        gpsManager.subscribe((pos) => this.checkLocationTriggers(pos));

        // Initial update
        this.triggerUpdate();
    }

    checkLocationTriggers(pos) {
        const currentNode = this.getCurrentNode();
        if (!currentNode || !currentNode.triggers) return;

        // Location Wait Logic
        if (currentNode.type === 'location_wait' && currentNode.targetLocation) {
            const dist = gpsManager.getDistance(
                pos.lat, pos.lng,
                currentNode.targetLocation.lat, currentNode.targetLocation.lng
            );

            // If closer than 20 meters (configurable)
            const threshold = currentNode.targetLocation.radius || 20;
            if (dist < threshold) {
                this.advance(currentNode.next);
            }
        }
    }

    getCurrentNode() {
        if (!this.storyData) return null;
        return this.storyData.nodes[this.currentNodeId];
    }

    // Logic: Variable getters/setters
    getVar(key) {
        return this.state[key];
    }

    setVar(key, value) {
        this.state[key] = value;
    }

    // Check conditions for a choice or node entry
    checkCondition(condition) {
        if (!condition) return true; // No condition = always true
        // format: "hasKey", "!hasKey", "score > 10" (simple parser)

        let shouldBeTrue = true;
        let varName = condition;

        if (condition.startsWith('!')) {
            shouldBeTrue = false;
            varName = condition.substring(1);
        }

        // Support simple boolean flags for now
        const val = !!this.state[varName];
        return val === shouldBeTrue;
    }

    advance(nextNodeId, remote = false) {
        if (this.storyData.nodes[nextNodeId]) {
            this.history.push(this.currentNodeId);
            this.currentNodeId = nextNodeId;

            // Execute any actions on entry (e.g., set flags)
            const node = this.getCurrentNode();
            if (node.onEnter) {
                // e.g., "set:hasKey"
                const parts = node.onEnter.split(':');
                if (parts[0] === 'set') {
                    this.setVar(parts[1], true);
                }
            }

            this.triggerUpdate();

            // If local action, sync to session
            if (!remote) {
                if (this.onStateChange) this.onStateChange(nextNodeId);
            }
        } else {
            console.error('Node not found:', nextNodeId);
        }
    }

    processInput(input) {
        const node = this.getCurrentNode();
        if (node.type !== 'input') return { success: false, message: "Nem várok választ." };

        const cleanInput = input.trim().toLowerCase();

        // Flexible matching
        const isValid = node.validAnswers.some(ans => cleanInput.includes(ans.toLowerCase()));

        if (isValid) {
            this.advance(node.successNext);
            return { success: true };
        } else {
            // Adaptive Logic: If failureNext is defined, go there instead of just message
            if (node.failureNext) {
                this.advance(node.failureNext);
                return { success: false, message: "Helytelen... De a történet folytatódik." };
            }

            return { success: false, message: node.failureMessage || "Ez nem tűnik jónak." };
        }
    }

    // New Hint System
    getHint() {
        const node = this.getCurrentNode();
        if (!node || !node.hint) return null;

        // Could track hint usage here in stats
        return node.hint;
    }

    triggerUpdate() {
        if (this.onStoryUpdate) {
            this.onStoryUpdate(this.getCurrentNode());
        }
    }
}

export const storyEngine = new StoryEngine();
