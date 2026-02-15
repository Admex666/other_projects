"use client";

import { motion } from "framer-motion";
import { Sparkles, Activity, Sword } from "lucide-react";

const features = [
    {
        icon: <Sparkles className="w-8 h-8 text-primary" />,
        title: "Szenvedésmentes mozgás",
        description: "Nincs edzés, nincs kondi. Csak a természetes mozgásod válik játékká.",
    },
    {
        icon: <Activity className="w-8 h-8 text-secondary" />,
        title: "Mérhető eredmény",
        description: "Valós idejű kalóriaégetés és folyamatos formajavulás az adataid alapján.",
    },
    {
        icon: <Sword className="w-8 h-8 text-accent" />,
        title: "Játékos motiváció",
        description: "A karaktered veled együtt fejlődik. Minden lépés pontot ér, minden cél új tárgyakat.",
    },
];

const Features = () => {
    return (
        <section className="py-24 px-4 bg-slate-950/50">
            <div className="max-w-6xl mx-auto">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {features.map((feature, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: index * 0.2 }}
                            viewport={{ once: true }}
                            className="glass p-8 rounded-3xl group hover:border-primary/50 transition-colors"
                        >
                            <div className="mb-6 p-4 rounded-2xl bg-white/5 inline-block group-hover:scale-110 transition-transform">
                                {feature.icon}
                            </div>
                            <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
                            <p className="text-slate-400 leading-relaxed">
                                {feature.description}
                            </p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Features;
