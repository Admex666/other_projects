'use client'

import { useState, useEffect } from 'react'

interface MobileCompanionHUDProps {
  teamName: string
  profileCode: string
  currentPhase: string
  phaseStartedAt: string | Date
  phaseDurationSeconds: number
  isTimerPaused: boolean
  timerRemainingSeconds: number
  activeEventTitle?: string | null
  activeEventDescription?: string | null
}

export default function MobileCompanionHUD({
  teamName,
  profileCode,
  currentPhase,
  phaseStartedAt,
  phaseDurationSeconds,
  isTimerPaused,
  timerRemainingSeconds,
  activeEventTitle,
  activeEventDescription,
}: MobileCompanionHUDProps) {
  const [remainingSec, setRemainingSec] = useState<number>(timerRemainingSeconds)

  useEffect(() => {
    if (isTimerPaused) {
      setRemainingSec(timerRemainingSeconds)
      return
    }

    const calcRemaining = () => {
      const started = new Date(phaseStartedAt).getTime()
      const now = Date.now()
      const elapsed = Math.floor((now - started) / 1000)
      return Math.max(0, phaseDurationSeconds - elapsed)
    }

    setRemainingSec(calcRemaining())
    const interval = setInterval(() => setRemainingSec(calcRemaining()), 1000)
    return () => clearInterval(interval)
  }, [phaseStartedAt, phaseDurationSeconds, isTimerPaused, timerRemainingSeconds])

  const minutes = Math.floor(remainingSec / 60)
  const seconds = remainingSec % 60
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`

  return (
    <div className="space-y-4">
      {/* Team Header */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-1">
        <span className="text-[10px] font-mono uppercase font-bold text-slate-400 block">
          Csapatod & Asztalod
        </span>
        <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
          {teamName}
        </h2>
        <span className="text-xs font-mono text-blue-600 font-semibold block">
          Archetípus: {profileCode}
        </span>
      </div>

      {/* Central Synced Timer */}
      <div className="p-6 rounded-xl bg-slate-100 border border-slate-200 text-center space-y-1">
        <span className="text-[10px] font-mono uppercase font-bold text-slate-500 tracking-wider block">
          Aktuális Fázis: {currentPhase}
        </span>
        <div className="text-4xl font-mono font-black text-slate-900 tabular-nums">
          {formattedTime}
        </div>
      </div>

      {/* Active Market Breaking Shock Alert */}
      {activeEventTitle && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-950 space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-600 animate-pulse"></span>
            <span className="text-[10px] font-mono uppercase font-bold bg-amber-200 text-amber-900 px-1.5 py-0.2 rounded">
              Piaci Rendkívüli Hír
            </span>
          </div>
          <h4 className="text-xs font-bold text-amber-950 mt-1">{activeEventTitle}</h4>
          <p className="text-xs text-amber-900 leading-normal">{activeEventDescription}</p>
        </div>
      )}

      {/* Physical Room Ergonomic Guidance Card */}
      <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-600"></span>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Helyszíni Ergonómiai Tipp
          </h3>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          A telefonodra most nincs közvetlen szükség. A csereajánlatokat és a banki elszámolást a csapat közös asztali tabletjén kezelitek.
        </p>
        <p className="text-xs text-slate-600 leading-relaxed font-semibold">
          Menj át tárgyalni a többi csapathoz, vagy segíts a precíz papírformák vonalzóval és ollóval való kivágásában!
        </p>
      </div>
    </div>
  )
}
