import { userManager } from '../user-manager.js';
import { router } from '../router.js';

export class ProfileView {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'view profile-view';
    }

    async render(container) {
        const user = userManager.getCurrentUser();
        if (!user) {
            router.navigate('onboarding');
            return;
        }

        this.container.innerHTML = `
            <header>
                <button id="back-btn" class="icon-btn">⬅</button>
                <h1>Profil</h1>
            </header>
            <div class="profile-content">
                <div class="profile-header">
                    <div class="avatar">${user.name.charAt(0).toUpperCase()}</div>
                    <h2>${user.name}</h2>
                    <span class="status">${user.isGuest ? 'Vendég' : 'Ügynök'}</span>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <label>Megtett táv</label>
                        <value>${(user.stats.distanceTraveled / 1000).toFixed(1)} km</value>
                    </div>
                    <div class="stat-card">
                        <label>Történetek</label>
                        <value>${user.stats.storiesCompleted}</value>
                    </div>
                </div>

                <h3>Jelvények</h3>
                <div class="badges-grid">
                    ${user.stats.badges.length ? user.stats.badges.map(b => `
                        <div class="badge">
                            <span>🏆</span>
                            <small>${b.id}</small>
                        </div>
                    `).join('') : '<p class="empty-state">Még nincsenek jelvényeid.</p>'}
                </div>

                <div class="actions">
                    <button id="logout-btn" class="secondary-btn">Kijelentkezés</button>
                </div>
            </div>
        `;

        this.container.querySelector('#back-btn').addEventListener('click', () => router.navigate('campaigns'));
        this.container.querySelector('#logout-btn').addEventListener('click', () => {
            // For guest, clear data. For real auth, logout.
            // Since we use localStorage key 'storyturak_user'
            localStorage.removeItem('storyturak_user');
            location.reload();
        });

        container.innerHTML = '';
        container.appendChild(this.container);
    }
}
