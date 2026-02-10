"use client";

import { trackEvent } from "@/lib/analytics";

interface HeroProps {
    onUnlockClick: () => void;
}

export default function Hero({ onUnlockClick }: HeroProps) {
    const handleUnlock = () => {
        trackEvent("unlock_access_click");
        onUnlockClick();
    };

    return (
        <section className="min-h-[85vh] flex flex-col justify-center px-6 md:px-12 max-w-4xl mx-auto pt-20">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tighter mb-8 text-balance">
                What does Budapest smell like?
            </h1>

            <div className="space-y-6 max-w-xl">
                <h2 className="text-xl md:text-2xl font-light text-neutral-400 italic">
                    Odor Finium creates limited scent objects inspired by places.
                    <br />
                    Budapest is the first.
                </h2>

                <p className="text-neutral-500 font-mono text-sm uppercase tracking-widest">
                    Designed for travelers. Produced in small batches.
                </p>

                <button
                    onClick={handleUnlock}
                    className="mt-8 bg-foreground text-background px-8 py-4 text-lg font-medium hover:bg-neutral-200 transition-colors duration-200 cursor-pointer"
                >
                    Unlock early access
                </button>
            </div>
        </section>
    );
}
