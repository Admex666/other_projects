'use client';

import { Target, Users } from 'lucide-react';

export default function VirtualPockets({ pockets }: { pockets: any[] }) {
  if (!pockets || pockets.length === 0) return null;

  return (
    <section className="space-y-4">
      <div className="flex justify-between items-center px-1">
        <h3 className="font-bold text-lg text-on-surface">Virtuális Zsebek</h3>
        <button className="text-primary text-xs font-bold hover:underline">+ Új zseb</button>
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
              {pocket.owners?.length > 1 && (
                <div className="flex items-center gap-1.5 text-[10px] text-primary bg-primary/10 px-2.5 py-1 rounded-full font-bold border border-primary/20">
                  <Users size={12} /> KÖZÖS
                </div>
              )}
            </div>

            {pocket.targetAmount ? (
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-bold">
                  <span className="text-on-surface-variant uppercase tracking-widest">Cél: {pocket.targetAmount.toLocaleString()} Ft</span>
                  <span className="text-primary">65%</span>
                </div>
                <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden p-[1px]">
                  <div 
                    className="h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(0,0,0,0.5)]" 
                    style={{ width: '65%', backgroundColor: pocket.color }}
                  ></div>
                </div>
              </div>
            ) : (
              <div className="flex justify-between items-end">
                 <p className="text-xs text-on-surface-variant">Jelenlegi egyenleg</p>
                 <p className="text-xl font-bold">45,000 Ft</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
