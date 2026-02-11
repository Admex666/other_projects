import Image from "next/image";

interface CollectorHeroProps {
    onUnlockClick: () => void;
}

export default function CollectorHero({ onUnlockClick }: CollectorHeroProps) {
    return (
        <section className="relative min-h-[90vh] flex items-center justify-center px-6 md:px-12 py-12 md:py-0 overflow-hidden">
            <div className="w-full max-w-7xl mx-auto grid md:grid-cols-2 gap-12 md:gap-24 items-center">
                {/* Text Content - Left Side */}
                <div className="order-2 md:order-1 space-y-8 md:space-y-12">
                    <div className="space-y-4">
                        <h1 className="text-4xl md:text-6xl font-serif font-light tracking-tight text-neutral-900 leading-[1.1]">
                            Odor Finium <br />
                            <span className="text-neutral-400 font-sans text-2xl md:text-3xl tracking-normal block mt-2">Edition 00</span>
                        </h1>
                        <p className="text-lg md:text-xl text-neutral-600 font-light max-w-md">
                            Kézműves illatszobor kollekció.
                        </p>
                    </div>

                    <div className="space-y-2 text-sm uppercase tracking-widest text-neutral-400 font-medium">
                        <p>Kézműves.</p>
                        <p>Limitált.</p>
                        <p>Magyar.</p>
                    </div>

                    <div className="flex flex-col items-start gap-2">
                        <button
                            onClick={onUnlockClick}
                            className="group inline-flex items-center gap-3 text-neutral-900 border-b border-neutral-900 pb-1 hover:text-neutral-600 hover:border-neutral-600 transition-all duration-300"
                        >
                            <span className="text-lg">Lefoglalom a helyem</span>
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                width="20"
                                height="20"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                className="group-hover:translate-x-1 transition-transform"
                            >
                                <path d="M5 12h14" />
                                <path d="m12 5 7 7-7 7" />
                            </svg>
                        </button>
                        <p className="text-xs text-neutral-500 font-medium tracking-wide">
                            (23/30 hely betelt)
                        </p>
                    </div>
                </div>

                {/* Hero Image - Right Side */}
                <div className="order-1 md:order-2 relative w-full aspect-[4/5] bg-[#f0f0f0] shadow-sm">
                    <Image
                        src="/gemini_parlament_matrica_light.png"
                        alt="Budapest Parliament sticker light"
                        fill
                        priority
                        className="object-contain object-center p-8"
                        sizes="(max-width: 768px) 100vw, 50vw"
                    />

                    {/* Subtle Overlay for Texture Feel */}
                    <div className="absolute inset-0 bg-neutral-900/[0.02] pointer-events-none" />
                </div>
            </div>
        </section>
    );
}
