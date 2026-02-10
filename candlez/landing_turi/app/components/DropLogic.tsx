"use client";

import { trackEvent } from "@/lib/analytics";

interface DropLogicProps {
    onUnlockClick: () => void;
}

export default function DropLogic({ onUnlockClick }: DropLogicProps) {
    const handleUnlock = () => {
        trackEvent("unlock_access_click");
        onUnlockClick();
    };

    return (
        <section className="py-24 px-6 md:px-12 max-w-4xl mx-auto text-center">
            <div className="max-w-2xl mx-auto space-y-8">
                <h2 className="text-3xl font-bold tracking-tight">
                    First drop. Limited access.
                </h2>

                <div className="space-y-6 text-lg text-neutral-400 font-light">
                    <p>
                        We’re preparing a small first batch inspired by Budapest.
                    </p>
                    <p>
                        Before opening access, we’re finalizing one key detail: <strong className="text-white font-medium">price</strong>.
                    </p>
                    <p className="border-t border-neutral-800 pt-6 mt-6">
                        To unlock early access, we ask you to answer 4 short questions.
                    </p>
                </div>

                <button
                    onClick={handleUnlock}
                    className="bg-white text-black px-8 py-4 text-lg font-medium hover:bg-neutral-200 transition-colors duration-200 cursor-pointer mt-4"
                >
                    Unlock early access
                </button>
            </div>
        </section>
    );
}
