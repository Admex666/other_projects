"use client";

interface AccessSectionProps {
    onUnlockClick: () => void;
}

export default function AccessSection({ onUnlockClick }: AccessSectionProps) {
    return (
        <section className="py-24 md:py-32 px-6 md:px-12 max-w-7xl mx-auto border-t border-neutral-200">
            <div className="flex flex-col items-center text-center space-y-8 max-w-2xl mx-auto">
                <span className="text-xs uppercase tracking-widest text-neutral-400 font-semibold mb-2">Korai Hozzáférés</span>

                <h2 className="text-4xl md:text-6xl font-serif font-light text-neutral-900 leading-[1.1]">
                    A gyűjtői hozzáférés <br />
                    <span>hamarosan megnyílik.</span>
                </h2>

                <div className="space-y-4 text-lg text-neutral-600 font-light max-w-lg">
                    <p>Véglegesítjük az Edition 00 árát.</p>
                    <p>Hogy tiéd lehessen egy darab, mindössze 4 kérdésre kell válaszolnod.</p>
                </div>

                <div className="pt-8 flex flex-col items-center gap-3">
                    <button
                        onClick={onUnlockClick}
                        className="group inline-flex items-center gap-3 bg-neutral-900 text-white px-8 py-4 rounded-full hover:bg-neutral-800 transition-all duration-300 shadow-lg hover:shadow-xl"
                    >
                        <span className="text-lg font-medium tracking-wide">Lefoglalom a helyem</span>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="group-hover:translate-x-1 transition-transform"
                        >
                            <path d="M5 12h14" />
                            <path d="m12 5 7 7-7 7" />
                        </svg>
                    </button>
                    <p className="text-sm text-neutral-500 font-medium tracking-wide">
                        (23/30 hely betelt)
                    </p>
                </div>
            </div>
        </section>
    );
}
