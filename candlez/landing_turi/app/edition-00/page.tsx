"use client";

import { useState } from "react";
import Hero from "../components/Hero";
import Concept from "../components/Concept";
import DropLogic from "../components/DropLogic";
import AccessModal from "../components/AccessModal";
import Trust from "../components/Trust";
import Footer from "../components/Footer";

export default function Home() {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => setIsModalOpen(false);

    return (
        <main className="min-h-screen relative selection:bg-white selection:text-black">
            <Hero onUnlockClick={openModal} />
            <Concept />
            <DropLogic onUnlockClick={openModal} />
            <Trust />
            <Footer />

            <AccessModal isOpen={isModalOpen} onClose={closeModal} />
        </main>
    );
}
