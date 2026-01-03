export class Router {
    constructor() {
        this.routes = [];
        this.currentView = null;
        this.appContainer = document.getElementById('app');
    }

    register(pathPattern, viewModule) {
        // pathPattern example: 'lobby/:campaignId/:mode'
        // Convert to regex
        const regexStr = '^' + pathPattern.replace(/:[a-zA-Z0-9_]+/g, '([^/]+)') + '$';
        const paramNames = (pathPattern.match(/:[a-zA-Z0-9_]+/g) || []).map(s => s.slice(1));

        this.routes.push({
            pattern: new RegExp(regexStr),
            paramNames: paramNames,
            viewClass: viewModule
        });
    }

    async navigate(path) {
        // Find matching route
        let match = null;
        let route = null;
        let params = {};

        for (const r of this.routes) {
            match = path.match(r.pattern);
            if (match) {
                route = r;
                break;
            }
        }

        if (!route) {
            console.warn(`No route found for ${path}`);
            // Fallback or 404
            return;
        }

        // Extract params
        route.paramNames.forEach((name, index) => {
            params[name] = decodeURIComponent(match[index + 1]);
        });

        // Cleanup current view if needed
        if (this.currentView && typeof this.currentView.destroy === 'function') {
            this.currentView.destroy();
        }

        // Render new view
        this.appContainer.innerHTML = '';
        const ViewClass = route.viewClass;
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
