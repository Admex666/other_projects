"use client";

import { motion } from "framer-motion";
import TallyButton from "./TallyButton";

const Hero = () => {
    return (
        <section className="relative min-h-[90vh] flex flex-col items-center justify-center text-center px-4 overflow-hidden bg-gradient-hero">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="z-10 max-w-4xl"
            >
                <span className="inline-block px-4 py-1.5 mb-6 text-sm font-semibold tracking-wider text-secondary uppercase bg-secondary/10 rounded-full border border-secondary/20">
                    Változtasd a sétát kalanddá
                </span>
                <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
                    Mozogj <span className="text-gradient">észrevétlenül</span>, játssz közben, és formálódj – szenvedés nélkül
                </h1>
                <p className="text-xl md:text-2xl text-slate-300 mb-10 max-w-2xl mx-auto leading-relaxed">
                    Napi 30 perc sétával akár havi <span className="text-secondary font-bold">4 000 kalóriát</span> is elégethetsz – és közben a karaktered fejlődik a játékban.
                </p>
                <TallyButton>
                    Szeretnék játszva formálódni
                </TallyButton>
                <div className="mt-4 flex items-center justify-center gap-2 text-slate-400 text-sm md:text-base font-medium">
                    <span className="flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-accent opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
                    </span>
                    Siess! Már <span className="text-white font-bold">38 / 50</span> hely betelt.
                </div>
            </motion.div>

            {/* Decorative elements */}
            <div className="absolute top-1/4 -left-20 w-64 h-64 bg-primary/20 rounded-full blur-[120px] animate-pulse-slow"></div>
            <div className="absolute bottom-1/4 -right-20 w-64 h-64 bg-secondary/20 rounded-full blur-[120px] animate-pulse-slow"></div>
        </section>
    );
};

export default Hero;
