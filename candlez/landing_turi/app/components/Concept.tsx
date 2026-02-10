export default function Concept() {
    return (
        <section className="py-24 px-6 md:px-12 border-t border-neutral-900 mx-auto max-w-4xl">
            <div className="grid md:grid-cols-2 gap-12 items-start">
                <div className="space-y-6">
                    <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
                        Not a souvenir.
                        <br />
                        <span className="text-neutral-500">A memory you take home.</span>
                    </h2>

                    <div className="space-y-4 text-lg text-neutral-300 font-light leading-relaxed">
                        <p>
                            Odor Finium is a place captured through scent.
                        </p>
                        <p>
                            Each object is designed to evoke the atmosphere of a city — not its landmarks, but its feeling.
                        </p>
                    </div>
                </div>

                <ul className="space-y-4 pt-2 md:pt-0">
                    {[
                        "Limited Budapest edition",
                        "Designed to travel easily",
                        "Created for people who want more than a postcard"
                    ].map((item, i) => (
                        <li key={i} className="flex items-center gap-3 text-neutral-400">
                            <span className="h-px w-4 bg-neutral-600 inline-block" />
                            {item}
                        </li>
                    ))}
                </ul>
            </div>
        </section>
    );
}
