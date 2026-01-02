import { router } from './router.js';
import OnboardingView from './views/onboarding.js';
import BrowserView from './views/browser.js';
import GameView from './views/game.js';
import LobbyView from './views/lobby.js';

document.addEventListener('DOMContentLoaded', () => {
    // Register Routes
    router.register('onboarding', OnboardingView);
    router.register('browser', BrowserView);
    router.register('lobby', LobbyView);
    router.register('game', GameView);

    // Check if user has seen onboarding (mocked for now, default to false)
    const hasSeenOnboarding = localStorage.getItem('storyturak_intro_seen');

    if (hasSeenOnboarding) {
        router.navigate('browser');
    } else {
        router.navigate('onboarding');
    }

    // Register Service Worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('./sw.js')
                .then(registration => {
                    console.log('SW registered: ', registration);
                })
                .catch(registrationError => {
                    console.log('SW registration failed: ', registrationError);
                });
        });
    }
});
