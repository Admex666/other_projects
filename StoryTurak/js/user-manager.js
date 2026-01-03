export class UserManager {
    constructor() {
        this.currentUser = this.loadUser() || null;
    }

    loadUser() {
        const stored = localStorage.getItem('storyturak_user');
        return stored ? JSON.parse(stored) : null;
    }

    saveUser() {
        if (this.currentUser) {
            localStorage.setItem('storyturak_user', JSON.stringify(this.currentUser));
        }
    }

    loginAsGuest(name) {
        this.currentUser = {
            id: 'guest-' + Date.now().toString(36),
            name: name || 'Vándor',
            isGuest: true,
            stats: {
                storiesCompleted: 0,
                distanceTraveled: 0,
                badges: []
            }
        };
        this.saveUser();
        return this.currentUser;
    }

    // Mock registration/login
    login(username) {
        // In a real app, this would verify credentials
        this.currentUser = {
            id: 'user-' + username.toLowerCase().replace(/[^a-z0-9]/g, ''),
            name: username,
            isGuest: false,
            stats: {
                storiesCompleted: 0,
                distanceTraveled: 0,
                badges: []
            }
        };
        this.saveUser();
        return this.currentUser;
    }

    updateStats(distanceInc, storyCompletedId = null) {
        if (!this.currentUser) return;

        if (distanceInc) {
            this.currentUser.stats.distanceTraveled += distanceInc;
        }

        if (storyCompletedId) {
            this.currentUser.stats.storiesCompleted++;
            if (!this.currentUser.stats.badges.includes(storyCompletedId)) {
                // Determine badge based on story ID (mock logic)
                // In real app, we'd lookup badge from campaign data
                this.currentUser.stats.badges.push({
                    id: `badge-${storyCompletedId}`,
                    date: new Date().toISOString()
                });
            }
        }
        this.saveUser();
    }

    getCurrentUser() {
        return this.currentUser;
    }

    isLoggedIn() {
        return !!this.currentUser;
    }
}

export const userManager = new UserManager();
