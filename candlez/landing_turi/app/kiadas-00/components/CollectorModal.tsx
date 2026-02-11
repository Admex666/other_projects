"use client";

import { useEffect, useRef } from "react";
// import { trackEvent } from "@/lib/analytics"; // Assuming analytics trackEvent exists, otherwise remove or mock

interface CollectorModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function CollectorModal({ isOpen, onClose }: CollectorModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden";
            // trackEvent("collector_tally_opened"); // Optional tracking

            // Load Tally script if not already present
            const scriptSrc = "https://tally.so/widgets/embed.js";
            if (!document.querySelector(`script[src="${scriptSrc}"]`)) {
                const script = document.createElement("script");
                script.src = scriptSrc;
                script.async = true;
                document.body.appendChild(script);
            } else {
                // If script is already there, trigger a reload of embeds
                // @ts-expect-error Tally is global
                if (typeof Tally !== "undefined") {
                    // @ts-expect-error Tally is global
                    Tally.loadEmbeds();
                }
            }
        } else {
            document.body.style.overflow = "unset";
        }

        return () => {
            document.body.style.overflow = "unset";
        };
    }, [isOpen]);

    // Handle click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
        }

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-neutral-900/60 backdrop-blur-md animate-in fade-in duration-300">
            <div
                ref={modalRef}
                className="relative w-full max-w-xl bg-white text-neutral-900 rounded-none shadow-2xl max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-300 border border-neutral-200"
            >
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-10 p-2 text-neutral-400 hover:text-neutral-900 transition-colors"
                    aria-label="Close modal"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>

                <div className="p-8 md:p-12 pb-4">
                    <div className="mb-8 text-center space-y-2">
                        <h3 className="text-2xl font-serif font-light text-neutral-900">
                            Gyűjtői Hozzáférés <br />
                            <span className="text-neutral-400 text-lg sans-serif">Edition 00</span>
                        </h3>
                        <p className="text-neutral-600 font-light text-sm max-w-xs mx-auto">
                            Véglegesítjük az első sorszámozott kiadás árát. Hogy tiéd lehessen egy darab, mindössze 4 kérdésre kell válaszolnod.
                        </p>
                    </div>

                    <div className="w-full">
                        <iframe
                            data-tally-src="https://tally.so/embed/eqevYE?alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1"
                            loading="lazy"
                            width="100%"
                            height="200"
                            frameBorder="0"
                            marginHeight={0}
                            marginWidth={0}
                            title="Unlock early access"
                            className="w-full bg-transparent"
                        >
                        </iframe>
                    </div>
                </div>
            </div>
        </div>
    );
}
