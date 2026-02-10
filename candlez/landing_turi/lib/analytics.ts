type PlausibleEvents = {
    unlock_access_click: never;
    tally_opened: never;
    early_access_unlocked: never;
    [key: string]: never; // Allow other events dynamically if needed
};

// Declare window properties for Plausible
declare global {
    interface Window {
        plausible: (
            eventName: keyof PlausibleEvents | string,
            options?: { props?: Record<string, string | number | boolean> }
        ) => void;
    }
}

export const trackEvent = (
    eventName: keyof PlausibleEvents | string,
    props?: Record<string, string | number | boolean>
) => {
    if (typeof window !== "undefined" && window.plausible) {
        window.plausible(eventName, { props });
    } else {
        console.log(`[Analytics] Event tracked: ${eventName}`, props);
    }
};
