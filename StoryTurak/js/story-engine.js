import { gpsManager } from './gps-manager.js';

export class StoryEngine {
    constructor() {
        this.storyData = null;
        this.currentNodeId = null;
        this.state = {}; // Game state variables (inventory, flags)
        this.onStoryUpdate = null; // Callback for UI
    }

    loadStory(storyJson) {
        this.storyData = storyJson;
        this.currentNodeId = this.storyData.startNode;
        this.state = { ...this.storyData.initialState };
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

        // Check if we are close enough to any target location
        // This is a simplified logic. In a real app, active triggers might depend on the current objective.

        // Example: if the node waits for location
        if (currentNode.type === 'location_wait' && currentNode.targetLocation) {
            const dist = gpsManager.getDistance(
                pos.lat, pos.lng,
                currentNode.targetLocation.lat, currentNode.targetLocation.lng
            );

            // If closer than 20 meters
            if (dist < 20) {
                this.advance(currentNode.next);
            }
        }
    }

    getCurrentNode() {
        return this.storyData.nodes[this.currentNodeId];
    }

    advance(nextNodeId, remote = false) {
        if (this.storyData.nodes[nextNodeId]) {
            this.currentNodeId = nextNodeId;
            this.triggerUpdate();

            // If local action, sync to session
            if (!remote) {
                // Import sessionManager dynamically or check global to avoid circular dep if needed
                // But better to have an observer pattern.
                // For now, let's assume GameView handles the sync or we attach a listener.
                if (this.onStateChange) this.onStateChange(nextNodeId);
            }
        } else {
            console.error('Node not found:', nextNodeId);
        }
    }

    processInput(input) {
        const node = this.getCurrentNode();
        if (node.type === 'input') {
            // Simple validation
            if (node.validAnswers.includes(input.toLowerCase().trim())) {
                this.advance(node.successNext);
                return { success: true };
            } else {
                return { success: false, message: node.failureMessage || "Ez nem tűnik jónak." };
            }
        }
        return { success: false };
    }

    triggerUpdate() {
        if (this.onStoryUpdate) {
            this.onStoryUpdate(this.getCurrentNode());
        }
    }
}

export const storyEngine = new StoryEngine();
