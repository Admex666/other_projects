"use client";

import { useEffect, useRef } from "react";
import { trackEvent } from "@/lib/analytics";

interface AccessModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AccessModal({ isOpen, onClose }: AccessModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = "hidden";
            trackEvent("tally_opened");

            // Load Tally script if not already present
            const scriptSrc = "https://tally.so/widgets/embed.js";
            if (!document.querySelector(`script[src="${scriptSrc}"]`)) {
                const script = document.createElement("script");
                script.src = scriptSrc;
                script.async = true;
                document.body.appendChild(script);
            } else {
                // If script is already there, trigger a reload of embeds in case
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div
                ref={modalRef}
                className="relative w-full max-w-2xl bg-[#111] border border-neutral-800 rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-200"
            >
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-10 p-2 text-neutral-400 hover:text-white transition-colors"
                    aria-label="Close modal"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>

                <div className="p-1">
                    <iframe
                        data-tally-src="https://tally.so/embed/rjAd8p?alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1"
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
    );
}
