"use client";

import { motion } from "framer-motion";
import TallyButton from "./TallyButton";

const AppPreview = () => {
    return (
        <section className="py-24 px-4 relative overflow-hidden">
            <div className="max-w-6xl mx-auto flex flex-col items-center">
                <h2 className="text-4xl md:text-5xl font-bold mb-16 text-center">
                    Fejleszd a karaktered, <span className="text-secondary">miközben mozogsz</span>
                </h2>

                <div className="relative w-full max-w-[800px]">
                    {/* Main central mock-up area */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.7 }}
                        viewport={{ once: true }}
                        className="aspect-[16/9] glass rounded-[2.5rem] p-8 md:p-12 relative flex flex-col justify-end overflow-hidden"
                    >
                        {/* Simulated App Background Gradient */}
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/30 via-transparent to-secondary/30 pointer-events-none"></div>

                        {/* XP BAR OVERLAY */}
                        <div className="relative z-10 w-full mb-8">
                            <div className="flex justify-between items-end mb-3">
                                <div>
                                    <h4 className="text-primary font-bold text-lg uppercase tracking-widest">Level 14 Path-Finder</h4>
                                    <p className="text-white text-3xl font-black">12,450 XP</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-slate-400 text-sm">Next Reward</p>
                                    <p className="text-white font-bold">In 550 steps</p>
                                </div>
                            </div>

                            <div className="w-full h-4 bg-slate-800 rounded-full overflow-hidden border border-white/10 p-0.5">
                                <motion.div
                                    initial={{ width: "0%" }}
                                    whileInView={{ width: "75%" }}
                                    transition={{ duration: 1.5, ease: "easeOut" }}
                                    viewport={{ once: true }}
                                    className="h-full bg-gradient-to-right from-primary to-secondary rounded-full relative shadow-[0_0_15px_rgba(139,92,246,0.5)]"
                                ></motion.div>
                            </div>
                        </div>

                        {/* Stats Overlay */}
                        <div className="grid grid-cols-2 gap-4 relative z-10">
                            <div className="glass bg-white/5 p-6 rounded-2xl border border-white/10">
                                <p className="text-slate-400 text-sm mb-1 uppercase tracking-tighter">Calories Burned</p>
                                <p className="text-2xl md:text-3xl font-bold">1,240 <span className="text-sm font-normal text-slate-500">kcal</span></p>
                            </div>
                            <div className="glass bg-white/5 p-6 rounded-2xl border border-white/10">
                                <p className="text-slate-400 text-sm mb-1 uppercase tracking-tighter">Daily Target</p>
                                <p className="text-2xl md:text-3xl font-bold text-secondary">82% <span className="text-sm font-normal text-slate-500">done</span></p>
                            </div>
                        </div>

                        {/* Floating items/icons simulation */}
                        <div className="absolute top-1/4 right-1/4 animate-float opacity-40">
                            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-yellow-400 to-orange-500 rotate-12 flex items-center justify-center shadow-lg">
                                <span className="text-2xl">⚔️</span>
                            </div>
                        </div>
                        <div className="absolute top-1/3 left-1/4 animate-float opacity-30 delay-700">
                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-400 to-indigo-500 -rotate-12 flex items-center justify-center shadow-lg">
                                <span className="text-xl">🛡️</span>
                            </div>
                        </div>
                    </motion.div>

                    {/* Blurred Background decoration */}
                    <div className="absolute -inset-10 bg-primary/20 blur-3xl -z-10 rounded-full"></div>
                </div>

                <div className="mt-20 text-center">
                    <TallyButton className="px-12 py-5 text-xl">
                        Csatlakozz mielőtt elfogynak a helyek
                    </TallyButton>
                </div>
            </div>
        </section>
    );
};

export default AppPreview;
