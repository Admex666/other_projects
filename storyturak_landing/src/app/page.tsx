import Hero from "@/components/Hero";
import Features from "@/components/Features";
import SocialProof from "@/components/SocialProof";
import AppPreview from "@/components/AppPreview";

export default function Home() {
  return (
    <main className="min-h-screen relative">
      <Hero />
      <Features />
      <SocialProof />
      <AppPreview />

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 text-center px-4">
        <p className="text-slate-500 text-sm">
          © {new Date().getFullYear()} Keldor. Minden jog fenntartva.
        </p>
      </footer>
    </main>
  );
}
