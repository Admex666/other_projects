import Image from "next/image";

export default function ProductDetail() {
    return (
        <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto border-t border-neutral-200">
            <div className="grid md:grid-cols-2 gap-12 lg:gap-24 items-center">
                {/* Image - Left Side */}
                <div className="relative w-full aspect-[4/5] bg-neutral-100 shadow-sm overflow-hidden">
                    <Image
                        src="/scent_sculpture_texture_detail.png"
                        alt="Macro detail of the scent sculpture texture showing engraved number 01"
                        fill
                        className="object-cover object-center scale-105 hover:scale-100 transition-transform duration-700 ease-out"
                        sizes="(max-width: 768px) 100vw, 50vw"
                    />
                </div>

                {/* Text - Right Side */}
                <div className="space-y-6 md:pl-12">
                    <h2 className="text-3xl md:text-5xl font-serif font-light text-neutral-900 leading-tight">
                        Az anyag <br />
                        <span className="text-neutral-400">számít.</span>
                    </h2>

                    <p className="text-lg text-neutral-600 font-light leading-relaxed max-w-sm">
                        A forma, a felület és az illat egyenrangú alkotóelemek.
                    </p>
                </div>
            </div>
        </section>
    );
}
