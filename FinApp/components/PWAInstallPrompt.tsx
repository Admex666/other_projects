'use client';

import { useState, useEffect } from 'react';
import { Download, X } from 'lucide-react';

export default function PWAInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState<any>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handler = (e: any) => {
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();
      // Stash the event so it can be triggered later.
      setInstallPrompt(e);
      
      // Check if we should show it (e.g. haven't dismissed it recently)
      const dismissed = localStorage.getItem('pwa-prompt-dismissed');
      const now = Date.now();
      
      if (!dismissed || now - parseInt(dismissed) > 1000 * 60 * 60 * 24 * 7) { // 7 days
         setIsVisible(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Check if already in standalone mode
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsVisible(false);
    }

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;
    
    installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setIsVisible(false);
    }
    setInstallPrompt(null);
  };

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-24 left-4 right-4 z-[100] animate-in slide-in-from-bottom-10 duration-500">
      <div className="custom-glass p-5 rounded-3xl flex items-center justify-between gap-4 border border-primary/20 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary rounded-2xl flex items-center justify-center text-background shadow-lg">
            <Download size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">FinApp Telepítése</h3>
            <p className="text-[10px] text-on-surface-variant font-medium">Add a kezdőképernyőhöz a gyors eléréshez!</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={handleInstall}
            className="bg-primary text-background text-xs font-bold px-4 py-2.5 rounded-xl hover:opacity-90 active:scale-95 transition-all"
          >
            Telepítés
          </button>
          <button 
            onClick={handleDismiss}
            className="p-2 text-on-surface-variant hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
