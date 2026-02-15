"use client";

import { motion } from "framer-motion";
import { Users } from "lucide-react";

const SocialProof = () => {
    return (
        <section className="py-20 px-4">
            <div className="max-w-4xl mx-auto text-center">
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    viewport={{ once: true }}
                    className="bg-primary/10 border border-primary/20 p-12 rounded-[3rem] relative overflow-hidden"
                >
                    <div className="absolute top-0 right-0 p-8 opacity-10">
                        <Users className="w-32 h-32" />
                    </div>

                    <h2 className="text-3xl md:text-5xl font-bold mb-6">
                        Csak 50 <span className="text-primary italic">Alapító Tag</span>
                    </h2>
                    <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
                        Korai hozzáférés, örök kedvezmény és exkluzív játékbeli jutalmak várnak az első csatlakozókra.
                    </p>
                    <div className="flex items-center justify-center gap-2 text-primary font-bold text-lg">
                        <span className="w-3 h-3 bg-primary rounded-full animate-ping"></span>
                        Az elérhető helyek száma korlátozott, ne késlekedj
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

export default SocialProof;
