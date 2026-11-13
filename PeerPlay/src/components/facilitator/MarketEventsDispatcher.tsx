'use client'

import { useState } from 'react'
import {
  triggerMarketEvent,
  clearMarketEvents,
} from '@/modules/bank/actions'
import toast from 'react-hot-toast'

interface ActiveMarketEvent {
  id: string
  code: string
  title: string
  description: string
  priceMultipliers: string
  isActive: boolean
  triggeredAt: string | Date
}

interface MarketEventsDispatcherProps {
  sessionId: string
  activeEvent?: ActiveMarketEvent | null
}

interface PresetEvent {
  code: string
  title: string
  description: string
  multipliers: Record<string, number>
  badge: string
}

const PRESET_EVENTS: PresetEvent[] = [

  {
    code: 'SQUARE_BOOM',
    title: 'Négyzet Boom (Építőipari Kereslet)',
    description: 'Megnövekedett infrastruktúra-fejlesztések miatt a Bank 50%-os felárral, darabonként $450-ért vásárolja fel a szabályos négyzeteket!',
    multipliers: { SQUARE: 1.5 },
    badge: 'Árváltozás (+50%)',
  },
  {
    code: 'PAPER_EMBARGO',
    title: 'Nyersanyag-embargó (Papírválság)',
    description: 'A központi papírellátás ideiglenesen lezárult. Új A4-es papírlapok csak a piacon meglévő készletekből szerezhetők be!',
    multipliers: {},
    badge: 'Kínálati Sokk',
  },
  {
    code: 'TECH_STANDARDS',
    title: 'Technológiai Szabvány Szigorítás',
    description: 'A Bank szigorítja a minőségi követelményeket: a szabályos sablonos körök ára $350-ra emelkedik (+40%), de a szabadkézi íveket azonnal selejtezik.',
    multipliers: { CIRCLE: 1.4 },
    badge: 'Minőségi Árfolyam (+40%)',
  },
  {
    code: 'TRIANGLE_EXPORT',
    title: 'Sürgősségi Exportmegrendelés',
    description: 'Azonnali külpiaci megrendelés érkezett háromszögekre! A Bank a háromszögeket $200-ért veszi át az alap $150 helyett.',
    multipliers: { TRIANGLE: 1.33 },
    badge: 'Export Prémium (+33%)',
  },
]

export default function MarketEventsDispatcher({
  sessionId,
  activeEvent,
}: MarketEventsDispatcherProps) {
  const [loading, setLoading] = useState(false)
  const [customTitle, setCustomTitle] = useState('')
  const [customDescription, setCustomDescription] = useState('')
  const [customShape, setCustomShape] = useState<'SQUARE' | 'TRIANGLE' | 'CIRCLE' | 'RECTANGLE'>('SQUARE')
  const [customMultiplier, setCustomMultiplier] = useState<number>(1.5)

  const handleTriggerPreset = async (preset: (typeof PRESET_EVENTS)[number]) => {
    setLoading(true)
    try {
      await triggerMarketEvent(
        sessionId,
        preset.code,
        preset.title,
        preset.description,
        preset.multipliers,
        180
      )
      toast.success(`Piaci esemény kiküldve: ${preset.title}`)
    } catch (e: any) {
      toast.error(e.message || 'Hiba a piaci esemény indításakor')
    } finally {
      setLoading(false)
    }
  }

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!customTitle || !customDescription) {
      toast.error('Kérlek töltsd ki a hír címét és leírását!')
      return
    }

    setLoading(true)
    try {
      await triggerMarketEvent(
        sessionId,
        'CUSTOM_SHOCK',
        customTitle,
        customDescription,
        { [customShape]: customMultiplier },
        180
      )
      toast.success(`Egyedi piaci esemény aktiválva!`)
      setCustomTitle('')
      setCustomDescription('')
    } catch (e: any) {
      toast.error(e.message || 'Hiba a piaci esemény mentésekor')
    } finally {
      setLoading(false)
    }
  }

  const handleClearEvents = async () => {
    setLoading(true)
    try {
      await clearMarketEvents(sessionId)
      toast.success('Piac normalizálva! Minden árfolyam-módosító visszaállt alapszintre.')
    } catch (e: any) {
      toast.error(e.message || 'Hiba a piac visszaállításakor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="theme-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-amber-800 bg-amber-50 px-2.5 py-0.5 rounded border border-amber-300">
                S-FAC-04 Piaci Események Dispatcher
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Piaci Hírek & Gazdasági Sokkok Kezelése
            </h2>
            <p className="text-xs text-slate-500">
              Árváltozások, nyersanyag-embargók és szabályozói hírek azonnali szinkronizált kiküldése a csapatok képernyőjére.
            </p>
          </div>

          <div>
            {activeEvent && activeEvent.isActive ? (
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300">
                <span className="w-2 h-2 rounded-full bg-amber-600 animate-pulse"></span>
                1 Aktív Piaci Módosító Érvényben
              </span>
            ) : (
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-slate-100 text-slate-600 border border-slate-200">
                Alapértelmezett Piaci Állapot
              </span>
            )}
          </div>
        </div>

        {/* Currently Active Event Banner */}
        {activeEvent && activeEvent.isActive && (
          <div className="mt-4 p-4 rounded-xl bg-amber-50/80 border border-amber-300 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase font-bold bg-amber-200 text-amber-900 px-2 py-0.5 rounded">
                  Élő Adásban
                </span>
                <span className="font-bold text-amber-950 text-sm">{activeEvent.title}</span>
              </div>
              <p className="text-xs text-amber-900 mt-1">{activeEvent.description}</p>
              <span className="text-[10px] font-mono text-amber-700 block mt-1">
                Szorzók: {activeEvent.priceMultipliers}
              </span>
            </div>
            <button
              onClick={handleClearEvents}
              disabled={loading}
              className="px-4 py-2 bg-white hover:bg-slate-50 text-amber-900 border border-amber-300 rounded-lg text-xs font-bold transition shadow-2xs shrink-0 cursor-pointer"
            >
              Piac Normalizálása (Törlés)
            </button>
          </div>
        )}
      </div>

      {/* Grid: Presets vs Custom Dispatcher */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Predefined Presets (7 cols) */}
        <div className="lg:col-span-7 theme-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Előre Konfigurált Események (Katalógus)
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {PRESET_EVENTS.map((preset) => (
              <div
                key={preset.code}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-[10px] font-mono font-bold bg-slate-200 text-slate-700 px-2 py-0.5 rounded">
                      {preset.badge}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-900">{preset.title}</h4>
                  <p className="text-[11px] text-slate-600 mt-1 leading-normal line-clamp-3">
                    {preset.description}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => handleTriggerPreset(preset)}
                  disabled={loading}
                  className="mt-4 w-full py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition shadow-2xs flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                  </svg>
                  <span>Aktiválás Most</span>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Custom News Editor (5 cols) */}
        <div className="lg:col-span-5 theme-card p-6 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Egyedi Hír Szerkesztése & Kiküldése
          </h3>

          <form onSubmit={handleCustomSubmit} className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-600 block mb-1">
                Esemény / Hír Címe
              </label>
              <input
                type="text"
                placeholder="pl. Nyersanyagárrobbanás"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-600 block mb-1">
                Részletes Tájékoztató Szöveg
              </label>
              <textarea
                placeholder="pl. A piac bizonytalan, a Bank prémiumot fizet a körökért..."
                value={customDescription}
                onChange={(e) => setCustomDescription(e.target.value)}
                required
                rows={3}
                className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">
                  Érintett Forma
                </label>
                <select
                  value={customShape}
                  onChange={(e) => setCustomShape(e.target.value as any)}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="SQUARE">Négyzet</option>
                  <option value="TRIANGLE">Háromszög</option>
                  <option value="CIRCLE">Kör</option>
                  <option value="RECTANGLE">Téglalap</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">
                  Árszorzó (pl. 1.5 = +50%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.2"
                  max="3.0"
                  value={customMultiplier}
                  onChange={(e) => setCustomMultiplier(parseFloat(e.target.value))}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 font-mono focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-3 w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition shadow-xs flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Azonnali Broadcast Kiküldés</span>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
