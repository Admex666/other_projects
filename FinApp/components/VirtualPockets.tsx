'use client';

import { Target, Users, Share2 } from 'lucide-react';
import ShareModal from './ShareModal';
import { useState } from 'react';

export default function VirtualPockets({ pockets, onCreate, onTransfer }: { pockets: any[], onCreate?: () => void, onTransfer?: () => void }) {
  const [shareData, setShareData] = useState<{ id: string, name: string } | null>(null);

  if (!pockets || pockets.length === 0) {
    return (
      <section className="space-y-4">
        <div className="flex justify-between items-center px-1">
          <h3 className="font-bold text-lg text-on-surface">Virtuális Zsebek</h3>
          <button onClick={onCreate} className="text-primary text-xs font-bold hover:underline">+ Új zseb</button>
        </div>
        <div className="custom-glass p-8 rounded-2xl text-center">
          <p className="text-on-surface-variant text-sm mb-4">Még nincsenek zsebeid.</p>
          <button 
            onClick={onCreate}
            className="px-6 py-2 bg-primary/10 text-primary rounded-xl text-sm font-bold hover:bg-primary/20 transition-colors"
          >
            Első zseb létrehozása
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="flex justify-between items-center px-1">
        <h3 className="font-bold text-lg text-on-surface">Virtuális Zsebek</h3>
        <div className="flex gap-4">
          <button onClick={onTransfer} className="text-secondary text-xs font-bold hover:underline">Pénz mozgatása</button>
          <button onClick={onCreate} className="text-primary text-xs font-bold hover:underline">+ Új zseb</button>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {pockets.map((pocket) => (
          <div key={pocket._id} className="custom-glass p-5 space-y-4 rounded-2xl relative overflow-hidden group hover:bg-white/5 transition-colors">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg" 
                  style={{ backgroundColor: pocket.color + '20', color: pocket.color }}
                >
                  <Target size={20} />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">{pocket.name}</p>
                  <p className="text-[10px] text-on-surface-variant font-medium uppercase tracking-wider">{pocket.linkedAccountId?.name || 'Minden számla'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {pocket.owners?.length > 1 && (
                  <div className="flex items-center gap-1.5 text-[10px] text-primary bg-primary/10 px-2.5 py-1 rounded-full font-bold border border-primary/20">
                    <Users size={12} /> KÖZÖS
                  </div>
                )}
                <button 
                  onClick={() => setShareData({ id: pocket._id, name: pocket.name })}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-on-surface-variant transition-colors"
                >
                  <Share2 size={16} />
                </button>
              </div>
            </div>

            {pocket.targetAmount ? (
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-bold">
                  <span className="text-on-surface-variant uppercase tracking-widest">
                    Cél: {pocket.targetAmount.toLocaleString()} {pocket.currency}
                  </span>
                  <span className="text-primary">{pocket.progress}%</span>
                </div>
                <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden p-[1px]">
                  <div 
                    className="h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(0,0,0,0.5)]" 
                    style={{ width: `${pocket.progress}%`, backgroundColor: pocket.color }}
                  ></div>
                </div>
                <div className="flex justify-between items-center pt-1">
                  <p className="text-xs text-on-surface-variant">Egyenleg</p>
                  <p className="text-lg font-bold">{(pocket.currentAmount || 0).toLocaleString()} <span className="text-xs font-normal opacity-60">{pocket.currency}</span></p>
                </div>
              </div>
            ) : (
              <div className="flex justify-between items-end pt-2">
                 <p className="text-xs text-on-surface-variant">Jelenlegi egyenleg</p>
                 <p className="text-xl font-bold">{(pocket.currentAmount || 0).toLocaleString()} <span className="text-xs font-normal opacity-60">{pocket.currency}</span></p>
              </div>
            )}
          </div>
        ))}
      </div>

      <ShareModal 
        isOpen={!!shareData}
        onClose={() => setShareData(null)}
        pocketId={shareData?.id || ''}
        pocketName={shareData?.name || ''}
      />
    </section>
  );
}
