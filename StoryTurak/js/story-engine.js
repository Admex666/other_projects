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
        if (!currentNode || !currentNode.targetLocation) return;

        // Location Wait Logic
        if (currentNode.type === 'location_wait') {
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
        const node = { ...this.storyData.nodes[this.currentNodeId] };

        // Handle conditional text (Alternative narratives)
        if (node.alternatives) {
            for (const alt of node.alternatives) {
                if (this.checkCondition(alt.condition)) {
                    node.text = alt.text;
                    break;
                }
            }
        }

        return node;
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
        if (!condition) return true;

        // Support: "key", "!key", "key == value", "key != value"
        if (condition.includes(' == ')) {
            const [key, val] = condition.split(' == ');
            return this.state[key] == val.replace(/['"]/g, '');
        }
        if (condition.includes(' != ')) {
            const [key, val] = condition.split(' != ');
            return this.state[key] != val.replace(/['"]/g, '');
        }

        let shouldBeTrue = true;
        let varName = condition;

        if (condition.startsWith('!')) {
            shouldBeTrue = false;
            varName = condition.substring(1);
        }

        const val = !!this.state[varName];
        return val === shouldBeTrue;
    }

    advance(nextNodeId, remote = false) {
        let node = this.storyData.nodes[nextNodeId];
        if (node) {
            // Handle Auto-redirection (Condition nodes)
            if (node.type === 'condition') {
                const result = this.checkCondition(node.condition);
                const nextId = result ? node.successNext : node.failureNext;
                return this.advance(nextId, remote);
            }

            this.history.push(this.currentNodeId);
            this.currentNodeId = nextNodeId;

            // Execute actions on entry
            if (node.onEnter) {
                this.executeActions(node.onEnter);
            }

            this.triggerUpdate();

            // Sync to session if local
            if (!remote && this.onStateChange) {
                this.onStateChange(nextNodeId, this.state);
            }
        } else {
            console.error('Node not found:', nextNodeId);
        }
    }

    choose(choice) {
        if (choice.onSelect) {
            this.executeActions(choice.onSelect);
        }
        this.advance(choice.next);
    }

    executeActions(actions) {
        // Support array of actions or single string
        const actionList = Array.isArray(actions) ? actions : [actions];

        actionList.forEach(action => {
            const parts = action.split(':');
            if (parts[0] === 'set') {
                // Support "key=value" or just "key" (sets true)
                const kv = parts[1].split('=');
                if (kv.length === 2) {
                    let val = kv[1];
                    if (val === 'true') val = true;
                    else if (val === 'false') val = false;
                    this.setVar(kv[0], val);
                } else {
                    this.setVar(parts[1], true);
                }
            }
        });
    }

    processInput(input) {
        const node = this.getCurrentNode();
        if (node.type !== 'input') return { success: false, message: "Nem várok választ." };

        const cleanInput = input.trim().toLowerCase();

        // 1. Exact or include matching (default)
        let isValid = false;
        if (node.validAnswers) {
            isValid = node.validAnswers.some(ans => cleanInput.includes(ans.toLowerCase()));
        }

        // 2. Numeric matching
        if (node.numericAnswer !== undefined) {
            isValid = parseInt(cleanInput) === node.numericAnswer;
        }

        // 3. Optional Ordering matching (simplified: comma separated)
        if (node.orderAnswer) {
            const userOrder = cleanInput.split(',').map(s => s.trim());
            isValid = JSON.stringify(userOrder) === JSON.stringify(node.orderAnswer.map(s => s.toLowerCase()));
        }

        if (isValid) {
            if (node.onSuccess) this.executeActions(node.onSuccess);
            this.advance(node.successNext);
            return { success: true };
        } else {
            if (node.onFailure) this.executeActions(node.onFailure);
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
