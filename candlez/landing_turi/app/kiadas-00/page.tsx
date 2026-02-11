"use client";

import { useState } from "react";
import CollectorHero from "./components/CollectorHero";
import ObjectPhilosophy from "./components/ObjectPhilosophy";
import AccessSection from "./components/AccessSection";
import MinimalFooter from "./components/MinimalFooter";
import CollectorModal from "./components/CollectorModal";

export default function CollectorPage() {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <main className="min-h-screen relative bg-[#f5f5f5] text-neutral-900 selection:bg-neutral-900 selection:text-white font-sans">
            <CollectorHero onUnlockClick={openModal} />
            <ObjectPhilosophy />
            <AccessSection onUnlockClick={openModal} />
            <MinimalFooter />

            <CollectorModal isOpen={isModalOpen} onClose={closeModal} />
        </main>
    );
}
