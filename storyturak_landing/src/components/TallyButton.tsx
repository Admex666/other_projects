"use client";

import { cn } from "@/lib/utils";
import React from "react";

interface TallyButtonProps {
    className?: string;
    children: React.ReactNode;
}

const TallyButton = ({ className, children }: TallyButtonProps) => {
    return (
        <button
            data-tally-open="Pd5Vrb"
            data-tally-layout="modal"
            data-tally-emoji-text="👋"
            data-tally-emoji-animation="wave"
            className={cn(
                "bg-accent hover:bg-accent/90 text-white font-bold py-4 px-8 rounded-full text-lg md:text-xl transition-all duration-300 cta-glow",
                className
            )}
        >
            {children}
        </button>
    );
};

export default TallyButton;
