import { router } from '../router.js';

export default class OnboardingView {
    constructor() {
        this.step = 0;
        this.content = [
            {
                text: "Ez nem csupán séta...",
                sub: "Hanem egy történet, aminek te vagy a főszereplője."
            },
            {
                text: "Ez nem egy edzés app...",
                sub: "Bár meg fogsz izzadni a feszültségtől."
            },
            {
                text: "Ez nem szabadulószoba...",
                sub: "Mert az egész város a rendelkezésedre áll."
            },
            {
                text: "Készen állsz a nyomozásra?",
                sub: "Válassz egy ügyet, és indulj el.",
                action: "Kezdés"
            }
        ];
    }

    async render(container) {
        this.container = container;
        this.renderStep();
    }

    renderStep() {
        const data = this.content[this.step];
        const isLast = this.step === this.content.length - 1;

        this.container.innerHTML = `
            <div class="view-onboarding fade-in">
                <div class="onboarding-content">
                    <h1 class="noir-title">${data.text}</h1>
                    <p class="noir-subtitle">${data.sub}</p>
                </div>
                <div class="onboarding-controls">
                    <button id="next-btn" class="btn">${data.action || 'Tovább'}</button>
                </div>
            </div>
        `;

        this.container.querySelector('#next-btn').onclick = () => {
            if (isLast) {
                this.finish();
            } else {
                this.step++;
                this.renderStep();
            }
        };
    }

    finish() {
        localStorage.setItem('storyturak_intro_seen', 'true');
        router.navigate('browser');
    }
}
