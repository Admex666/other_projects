'use client'

import { useState, useEffect } from 'react'
import {
  advanceSessionPhase,
  adjustPhaseTimer,
} from '@/modules/session/actions'
import {
  WORKSHOP_PHASES,
  WorkshopPhase,
} from '@/modules/session/constants'

import toast from 'react-hot-toast'

interface PhaseControlHeroTimerProps {
  sessionId: string
  currentPhase: string
  phaseStartedAt: string | Date
  phaseDurationSeconds: number
  isTimerPaused: boolean
  timerRemainingSeconds: number
}

const PHASE_METADATA: Record<
  string,
  { name: string; durationMin: number; script: string; instructions: string[] }
> = {
  PHASE_0_SETUP: {
    name: '0. Munkamenet Előkészítés',
    durationMin: 5,
    script: 'Köszöntsd a résztvevőket, és ellenőrizd, hogy minden asztalon megvan-e a kiinduló boríték és a belépési kód.',
    instructions: [
      'Vetítsd ki a 6 karakteres belépési PIN kódot.',
      'Biztosítsd, hogy minden csapat asztalán legyen 1 db közös tablet vagy laptop.',
      'A játékosok a mobiljukkal csatlakozzanak a teremhez.',
    ],
  },
  PHASE_1_PRE_SURVEY: {
    name: '1. Pre-Game Pulse Felmérés',
    durationMin: 5,
    script: 'Kérd meg a résztvevőket, hogy a mobiljukon állítsák be a 2 csúszkát az érkezési energiaszintjükről és nyitottságukról.',
    instructions: [
      'A mobil felületen a Pre-Game Pulse kérdőív automatikusan megjelenik.',
      'A kitöltés mindössze 60 másodpercet vesz igénybe.',
      'Ne menj tovább, amíg a többség nem végzett.',
    ],
  },
  PHASE_2_RULES: {
    name: '2. Szabályismertetés & Eligazítás',
    durationMin: 8,
    script: 'Magyarázd el a 4 terméket, a minőségi elvárásokat és a Központi Bank működését. Tilos a szabadkézi vágás!',
    instructions: [
      'Mutasd be a vonalzó és sablon kötelező használatát.',
      'Hangsúlyozd: a Bank szigorúan selejtnek nyilvánítja a pontatlan méreteket.',
      'A vállalatok aszimmetrikus erőforrásokkal indulnak.',
    ],
  },
  PHASE_3_PLANNING: {
    name: '3. Csapatstratégia & Tervezés',
    durationMin: 5,
    script: 'A csapatok áttekintik a készleteiket és belső szerepeket osztanak ki (tárgyaló, mérnök, vágó).',
    instructions: [
      'A csapatok még NEM kezdhetnek el papírt vágni.',
      'Tárgyalási stratégia kialakítása a hiányzó eszközök megszerzésére.',
    ],
  },
  PHASE_4_ROUND_1: {
    name: '4. 1. Termelési & Kereskedelmi Kör',
    durationMin: 15,
    script: 'A piac megnyílt! Indulhat a cserekereskedelem és a formák gyártása.',
    instructions: [
      'A Bank átvételi pultja nyitva áll a kész formák leadására.',
      'P2P ajánlatok a tableten futnak, azonnali letéti zárolással.',
      'Figyeld a teremben kialakuló információs közvetítőket.',
    ],
  },
  PHASE_5_EVENT_1: {
    name: '5. 1. Piaci Esemény & Sokk',
    durationMin: 3,
    script: 'Rendkívüli gazdasági hírek érkeztek! Hirdesd ki az új felvásárlási árakat vagy korlátozásokat.',
    instructions: [
      'Aktiváld a kívánt piaci eseményt a jobb oldali modulban.',
      'A csapatoknak azonnal alkalmazkodniuk kell az új árakhoz.',
    ],
  },
  PHASE_6_ROUND_2: {
    name: '6. 2. Termelési & Kereskedelmi Kör',
    durationMin: 15,
    script: 'Második kereskedelmi kör megnövekedett tempóban. A szövetségek megszilárdulnak vagy felbomlanak.',
    instructions: [
      'Kövesd figyelemmel a nyersanyaghiányos csapatok tárgyalási pozícióit.',
      'A Bank folyamatosan ellenőrzi a geometriai méreteket.',
    ],
  },
  PHASE_7_EVENT_2: {
    name: '7. 2. Piaci Esemény & Szabályozói Váltás',
    durationMin: 3,
    script: 'Második piaci sokk! Változnak a prémium csomagok vagy technológiai követelmények.',
    instructions: [
      'Hirdesd ki a szabálymódosítást a teremben.',
      'Ellenőrizd a csapatok likviditását és alapanyagkészletét.',
    ],
  },
  PHASE_8_ROUND_3: {
    name: '8. 3. Záró Termelési Hajrá',
    durationMin: 12,
    script: 'Utolsó esély a formák eladására és a megmaradt javak monetizálására.',
    instructions: [
      'Figyelmeztesd a csapatokat: a fel nem használt papírlap nem hoz bevételt!',
      'Az utolsó 2 percben a Bank előtt torlódás alakulhat ki.',
    ],
  },
  PHASE_9_BANK_SETTLEMENT: {
    name: '9. Banki Zárás & Végelszámolás',
    durationMin: 7,
    script: 'A Bank ablaka bezárult! Nincs több termékátvétel. Minden csapat rögzíti a végső egyenlegét.',
    instructions: [
      'A Bank leállítja a kifizetéseket.',
      'Az összes nyitott P2P ajánlat automatikusan visszatérítésre került.',
    ],
  },
  PHASE_10_POST_SURVEY: {
    name: '10. Post-Game Peer Feedback',
    durationMin: 10,
    script: 'Kérd meg a résztvevőket, hogy a mobiljukon jelöljék a kulcsfontosságú koordinátorokat és belső támaszokat.',
    instructions: [
      'Mobil felületen: Broker (külső) és Enabler (belső) nominációk.',
      'Záró energiaszint és kvalitatív felismerések rögzítése.',
    ],
  },
  PHASE_11_DEBRIEF: {
    name: '11. Közös Teremi Debrief & Reflexió',
    durationMin: 7,
    script: 'Kapcsold be a kivetítői nézetet! Elemezzétek a hálózati szociogramot és a viselkedési tanulságokat.',
    instructions: [
      'Kattints a "Debrief Kivetítő Megnyitása" gombra a teljes képernyős hatáshoz.',
      'Vitassátok meg a facilitátori beszélgetésindító kérdéseket.',
    ],
  },
}

export default function PhaseControlHeroTimer({
  sessionId,
  currentPhase,
  phaseStartedAt,
  phaseDurationSeconds,
  isTimerPaused,
  timerRemainingSeconds,
}: PhaseControlHeroTimerProps) {
  const [remainingSec, setRemainingSec] = useState<number>(timerRemainingSeconds)
  const [loadingAction, setLoadingAction] = useState<boolean>(false)

  // Local live tick every 1000ms
  useEffect(() => {
    if (isTimerPaused) {
      setRemainingSec(timerRemainingSeconds)
      return
    }

    const calcRemaining = () => {
      const started = new Date(phaseStartedAt).getTime()
      const now = Date.now()
      const elapsed = Math.floor((now - started) / 1000)
      const rem = Math.max(0, phaseDurationSeconds - elapsed)
      return rem
    }

    setRemainingSec(calcRemaining())

    const interval = setInterval(() => {
      setRemainingSec(calcRemaining())
    }, 1000)

    return () => clearInterval(interval)
  }, [phaseStartedAt, phaseDurationSeconds, isTimerPaused, timerRemainingSeconds])

  const currentIndex = WORKSHOP_PHASES.indexOf(currentPhase as any)
  const prevPhase = currentIndex > 0 ? WORKSHOP_PHASES[currentIndex - 1] : null
  const nextPhase =
    currentIndex >= 0 && currentIndex < WORKSHOP_PHASES.length - 1
      ? WORKSHOP_PHASES[currentIndex + 1]
      : null

  const meta = PHASE_METADATA[currentPhase] || {
    name: currentPhase,
    durationMin: Math.round(phaseDurationSeconds / 60),
    script: 'Facilitátori teendők folyamatban.',
    instructions: ['Kövesd az ütemtervet.'],
  }

  // Format mm:ss
  const minutes = Math.floor(remainingSec / 60)
  const seconds = remainingSec % 60
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`

  // Timer alert styling
  const isCritical = remainingSec <= 30 && !isTimerPaused && remainingSec > 0
  const isWarning = remainingSec <= 120 && !isTimerPaused && remainingSec > 30

  const handleAdvance = async (phaseToGo: string) => {
    if (remainingSec > 60 && !confirm(`Még ${minutes} perc van hátra a fázisból. Biztosan léptetni szeretnéd?`)) {
      return
    }
    setLoadingAction(true)
    try {
      await advanceSessionPhase(sessionId, phaseToGo)
      toast.success(`Fázis váltva: ${PHASE_METADATA[phaseToGo]?.name || phaseToGo}`)
    } catch (e: any) {
      toast.error(e.message || 'Hiba a fázis léptetésekor')
    } finally {
      setLoadingAction(false)
    }
  }

  const handleTimerAdjust = async (addSec: number, pauseToggle?: boolean) => {
    setLoadingAction(true)
    try {
      const nextPaused = typeof pauseToggle === 'boolean' ? pauseToggle : undefined
      await adjustPhaseTimer(sessionId, addSec, nextPaused)
      if (addSec > 0) toast.success(`+${addSec / 60} perc hozzáadva az időzítőhöz.`)
      if (pauseToggle !== undefined) {
        toast(pauseToggle ? 'Időzítő szüneteltetve' : 'Időzítő folytatva')
      }
    } catch (e: any) {
      toast.error(e.message || 'Hiba az időzítő módosításakor')
    } finally {
      setLoadingAction(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 1. Horizontal Stepped Progress Bar (11 Phases) */}
      <div className="theme-card p-4 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[760px] gap-2">
          {WORKSHOP_PHASES.map((p, idx) => {
            const isCompleted = idx < currentIndex
            const isCurrent = idx === currentIndex
            return (
              <button
                key={p}
                onClick={() => handleAdvance(p)}
                disabled={loadingAction}
                title={PHASE_METADATA[p]?.name}
                className={`flex-1 flex flex-col items-center p-2 rounded-lg text-center transition cursor-pointer ${
                  isCurrent
                    ? 'bg-blue-50 border border-blue-400 text-blue-900 shadow-xs'
                    : isCompleted
                    ? 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200'
                    : 'text-slate-400 hover:bg-slate-50 border border-transparent'
                }`}
              >
                <div className="flex items-center justify-center w-6 h-6 rounded-full text-xs font-mono font-bold mb-1">
                  {isCompleted ? (
                    <span className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    </span>
                  ) : isCurrent ? (
                    <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center">
                      {idx}
                    </span>
                  ) : (
                    <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center">
                      {idx}
                    </span>
                  )}
                </div>
                <span className="text-[11px] font-bold tracking-tight truncate max-w-[85px] leading-tight">
                  {PHASE_METADATA[p]?.name.split('.')[1] || p}
                </span>
                <span className="text-[10px] font-mono text-slate-400 mt-0.5">
                  {PHASE_METADATA[p]?.durationMin}p
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* 2. Hero Timer Box & Controls */}
      <div className="theme-card p-6 flex flex-col lg:flex-row items-center justify-between gap-6">
        {/* Left: Active Phase Info */}
        <div className="space-y-1 text-center lg:text-left">
          <div className="flex items-center justify-center lg:justify-start gap-2">
            <span className="text-xs font-mono uppercase tracking-wider font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
              Aktív Fázis · {currentIndex + 1} / {WORKSHOP_PHASES.length}
            </span>
            {isTimerPaused && (
              <span className="text-xs font-mono uppercase tracking-wider font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-300">
                Szüneteltetve
              </span>
            )}
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">{meta.name}</h2>
          <p className="text-xs text-slate-500 font-medium max-w-sm">
            {meta.script}
          </p>
        </div>

        {/* Center: 3-Meter Hero Timer Box */}
        <div
          className={`flex flex-col items-center justify-center px-8 py-4 rounded-xl border transition-all ${
            isCritical
              ? 'bg-red-50 border-red-300 text-red-600 animate-pulse'
              : isWarning
              ? 'bg-amber-50 border-amber-300 text-amber-600'
              : isTimerPaused
              ? 'bg-slate-100 border-slate-300 text-slate-600'
              : 'bg-slate-100 border-slate-200 text-slate-900'
          }`}
        >
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 mb-1">
            Hátralévő Idő
          </span>
          <div className="text-5xl lg:text-6xl font-mono font-bold tracking-tight tabular-nums">
            {formattedTime}
          </div>

          {/* Quick Timer Steppers */}
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={() => handleTimerAdjust(0, !isTimerPaused)}
              disabled={loadingAction}
              className="px-3 py-1 bg-white hover:bg-slate-50 border border-slate-300 rounded text-xs font-semibold text-slate-700 shadow-2xs cursor-pointer"
            >
              {isTimerPaused ? 'Folytatás' : 'Szünet'}
            </button>
            <button
              onClick={() => handleTimerAdjust(60)}
              disabled={loadingAction}
              className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-300 rounded text-xs font-mono font-semibold text-slate-700 shadow-2xs cursor-pointer"
            >
              +1 perc
            </button>
            <button
              onClick={() => handleTimerAdjust(120)}
              disabled={loadingAction}
              className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-300 rounded text-xs font-mono font-semibold text-slate-700 shadow-2xs cursor-pointer"
            >
              +2 perc
            </button>
          </div>
        </div>

        {/* Right: Phase Steppers Next / Prev */}
        <div className="flex flex-col sm:flex-row lg:flex-col gap-2 w-full lg:w-auto">
          {nextPhase && (
            <button
              onClick={() => handleAdvance(nextPhase)}
              disabled={loadingAction}
              className="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Következő: {PHASE_METADATA[nextPhase]?.name.split('.')[1] || nextPhase}</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </button>
          )}
          {prevPhase && (
            <button
              onClick={() => handleAdvance(prevPhase)}
              disabled={loadingAction}
              className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1 cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              <span>Előző Fázis</span>
            </button>
          )}
        </div>
      </div>

      {/* 3. Facilitator Speaking Script & Instructions */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-7 theme-card p-5 space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Mit mondj a teremben most? (Facilitátori Forgatókönyv)
            </h3>
          </div>
          <blockquote className="border-l-2 border-blue-600 pl-4 py-1 text-sm font-medium text-slate-800 italic bg-slate-50/70 rounded-r">
            &ldquo;{meta.script}&rdquo;
          </blockquote>
        </div>

        <div className="md:col-span-5 theme-card p-5 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Teremfelügyeleti Ellenőrzőpontok
          </h3>
          <ul className="space-y-1.5 text-xs text-slate-600">
            {meta.instructions.map((ins, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="font-mono text-slate-400 font-bold">{i + 1}.</span>
                <span>{ins}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
