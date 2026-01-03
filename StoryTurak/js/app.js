import { router } from './router.js';
import { userManager } from './user-manager.js';
import OnboardingView from './views/onboarding.js';
import { CampaignBrowser } from './views/campaign-browser.js';
import { ProfileView } from './views/profile-view.js';
import LobbyView from './views/lobby.js';
import GameView from './views/game.js';

document.addEventListener('DOMContentLoaded', () => {
    // Register Routes
    router.register('onboarding', OnboardingView);
    router.register('campaigns', CampaignBrowser);
    router.register('profile', ProfileView);

    // Support parameterized routes
    router.register('lobby/:campaignId/:mode', LobbyView);
    router.register('lobby', LobbyView); // Fallback
    router.register('game/:campaignId/:mode', GameView);
    router.register('game', GameView); // Fallback

    // Check user state
    const user = userManager.getCurrentUser();

    if (user) {
        router.navigate('campaigns');
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
