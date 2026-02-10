import { track } from '@vercel/analytics/react';

type PlausibleEvents = {
    unlock_access_click: never;
    tally_opened: never;
    early_access_unlocked: never;
    [key: string]: never;
};

export const trackEvent = (
    eventName: keyof PlausibleEvents | string,
    props?: Record<string, string | number | boolean>
) => {
    // Vercel Analytics track function can be called directly
    // It handles checking for window/environment internally usually, 
    // but good to keep it wrapped for consistency.
    track(eventName as string, props);

    if (process.env.NODE_ENV === 'development') {
        console.log(`[Vercel Analytics] Event tracked: ${eventName}`, props);
    }
};
