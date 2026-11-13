'use client'

import { BASE_PRICES, ShapeType } from '@/modules/bank/constants'


interface ActiveMarketEvent {
  title: string
  description: string
  priceMultipliers: string
}

interface BankCommodityBoardProps {
  activeEvent?: ActiveMarketEvent | null
}

const COMMODITIES: {
  type: ShapeType
  name: string
  spec: string
  dimensions: string
}[] = [
  {
    type: 'SQUARE',
    name: 'Szabályos Négyzet',
    spec: 'Pontos 90°-os derékszögek, vonalzóval ellenőrizve',
    dimensions: '10 × 10 cm',
  },
  {
    type: 'TRIANGLE',
    name: 'Egyenlő oldalú Háromszög',
    spec: 'Minden oldala 10 cm, 60°-os hegyesszögekkel',
    dimensions: '10 × 10 × 10 cm',
  },
  {
    type: 'CIRCLE',
    name: 'Szabályos Kör',
    spec: 'Kizárólag sablon segítségével rajzolható és vágható!',
    dimensions: 'Ø 10 cm átmérő',
  },
  {
    type: 'RECTANGLE',
    name: 'Téglalap',
    spec: 'Párhuzamos oldalak, precíz sarkok',
    dimensions: '5 × 15 cm',
  },
  {
    type: 'PREMIUM_PACK',
    name: 'Prémium Csomag',
    spec: '2 db hibátlan Háromszög + 1 db Négyzet köteg',
    dimensions: 'Kombinált tétel',
  },
]

export default function BankCommodityBoard({ activeEvent }: BankCommodityBoardProps) {
  let multipliers: Record<string, number> = {}
  if (activeEvent?.priceMultipliers) {
    try {
      multipliers = JSON.parse(activeEvent.priceMultipliers)
    } catch {
      multipliers = {}
    }
  }

  return (
    <div className="space-y-6">
      {/* Active Market Breaking Shock Banner */}
      {activeEvent && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-950 space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-600 animate-pulse"></span>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider bg-amber-200 text-amber-900 px-2 py-0.5 rounded">
              Piaci Értesítés / Rendkívüli Hír
            </span>
            <span className="text-xs font-bold">{activeEvent.title}</span>
          </div>
          <p className="text-xs text-amber-900">{activeEvent.description}</p>
        </div>
      )}

      {/* Official Price Index */}
      <div className="theme-card p-6 space-y-4">
        <div className="pb-3 border-b border-slate-100 flex justify-between items-center">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Hivatalos Banki Árfolyamtábla (S-TEAM-03)
            </h3>
            <p className="text-xs text-slate-500">
              A Központi Bank felvásárlási egységárai a jelenlegi fázisban
            </p>
          </div>
          <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">
            Garantált kifizetés
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {COMMODITIES.map((c) => {
            const base = BASE_PRICES[c.type]
            const mult = multipliers[c.type] ?? 1.0
            const finalPrice = Math.round(base * mult)
            const hasMultiplier = mult !== 1.0

            return (
              <div key={c.type} className="py-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{c.name}</span>
                    <span className="text-xs font-mono text-slate-400">({c.dimensions})</span>
                    {hasMultiplier && (
                      <span className="text-[10px] font-mono font-bold bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded">
                        {mult > 1.0 ? `+${Math.round((mult - 1) * 100)}% Boom` : 'Árcsökkenés'}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{c.spec}</p>
                </div>

                <div className="text-right">
                  <div className="text-lg font-mono font-extrabold text-slate-900 tabular-nums">
                    ${finalPrice}
                  </div>
                  {hasMultiplier && (
                    <span className="text-[10px] font-mono text-slate-400 line-through">
                      ${base}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Quality Inspection & Defect Prevention Standard Card */}
      <div className="theme-card p-6 space-y-3 bg-slate-50/50">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
          Minőségi Standardok & Selejt Elkerülése
        </h4>
        <ul className="space-y-2 text-xs text-slate-600">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Hullámos vágás tilalma:</strong> A Bank a vonalzótól eltérő, szabadkézi vágású éleket azonnal selejtnek nyilvánítja.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Sablon monopólium:</strong> A szabályos kör kizárólag a hivatalos sablonnal rajzolható és vágható.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Méretellenőrzés:</strong> A leadás előtt ellenőrizzétek a méreteket, mert a Bank átvételi pultjánál nincs utólagos korrekció!
            </span>
          </li>
        </ul>
      </div>
    </div>
  )
}
