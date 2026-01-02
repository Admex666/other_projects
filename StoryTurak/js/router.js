export class Router {
    constructor() {
        this.routes = {};
        this.currentView = null;
        this.appContainer = document.getElementById('app');
    }

    register(path, viewModule) {
        this.routes[path] = viewModule;
    }

    async navigate(path, params = {}) {
        const ViewClass = this.routes[path];
        if (!ViewClass) {
            console.error(`No route found for ${path}`);
            return;
        }

        // Cleanup current view if needed
        if (this.currentView && typeof this.currentView.destroy === 'function') {
            this.currentView.destroy();
        }

        // Render new view
        this.appContainer.innerHTML = '';
        this.currentView = new ViewClass(params);
        
        try {
            await this.currentView.render(this.appContainer);
        } catch (error) {
            console.error('Error rendering view:', error);
            this.appContainer.innerHTML = '<div class="error">Hiba történt a betöltés közben.</div>';
        }
    }
}

export const router = new Router();
