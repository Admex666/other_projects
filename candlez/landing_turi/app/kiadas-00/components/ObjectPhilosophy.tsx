export default function ObjectPhilosophy() {
    return (
        <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto border-t border-neutral-200">
            <div className="grid md:grid-cols-2 gap-12 lg:gap-24 items-start">
                <div className="space-y-6">
                    <h2 className="text-3xl md:text-5xl font-serif font-light text-neutral-900 leading-tight">
                        Nem gyertya. <br />
                        <span className="text-neutral-400">Illatemlék.</span>
                    </h2>

                    <div className="space-y-4 text-lg text-neutral-600 font-light leading-relaxed max-w-md">
                        <p>
                            Az Odor Finium Magyarország szépségeit és emlékeit önti viaszba és illatokba.
                        </p>
                        <p>
                            Minden kiadás kis példányszámban készül, és szobrászati alkotásként áll meg a helyét – akár meggyújtva, akár anélkül.
                        </p>
                    </div>
                </div>

                <ul className="space-y-6 pt-4 md:pt-[10px]">
                    {[
                        "Első magyar gyűjtői kiadás",
                        "Kézzel készített",
                        "Limitált példányszámban gyártva",
                        "Az egyes kiadások formája és illata szerint egyediek"
                    ].map((item, i) => (
                        <li key={i} className="flex items-center gap-4 text-neutral-500 group">
                            <span className="h-px w-6 bg-neutral-300 group-hover:w-10 transition-all duration-500 ease-out" />
                            <span className="font-light tracking-wide">{item}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </section>
    );
}
