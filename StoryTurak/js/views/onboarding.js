import { userManager } from '../user-manager.js';
import { router } from '../router.js';

export default class OnboardingView {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'view onboarding-view fade-in';
    }

    async render(container) {
        container.innerHTML = '';
        container.appendChild(this.container);

        this.container.innerHTML = `
            <div class="onboarding-content">
                <div class="logo">🕵️‍♂️</div>
                <h1>Üdvözöllek, Nyomozó.</h1>
                <p>Mielőtt nekilátunk a munkának, szükségünk van a fedőnevedre.</p>
                
                <div class="input-group">
                    <input type="text" id="username-input" placeholder="Írd be a neved..." autofocus />
                </div>

                <button id="btn-start" class="primary-btn">Beszállok</button>
                <button id="btn-guest" class="text-btn">Csak nézelődöm (Vendég)</button>
            </div>
        `;

        this.container.querySelector('#btn-start').addEventListener('click', () => this.finishOnboarding(false));
        this.container.querySelector('#btn-guest').addEventListener('click', () => this.finishOnboarding(true));

        // Enter key support
        this.container.querySelector('#username-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.finishOnboarding(false);
        });
    }

    finishOnboarding(isGuest) {
        const input = this.container.querySelector('#username-input');
        const name = input.value.trim();

        if (!isGuest && !name) {
            input.classList.add('shake');
            setTimeout(() => input.classList.remove('shake'), 500);
            return;
        }

        if (isGuest) {
            userManager.loginAsGuest();
        } else {
            userManager.login(name);
        }

        // Save flag that we've seen onboarding
        localStorage.setItem('storyturak_intro_seen', 'true');

        router.navigate('campaigns');
    }
}
