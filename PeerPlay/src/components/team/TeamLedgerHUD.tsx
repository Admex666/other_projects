'use client'

import { useState, useEffect } from 'react'

interface TeamLedgerHUDProps {
  teamName: string
  profileCode: string
  cashBalance: number
  paperSheets: number
  scissorsCount: number
  rulersCount: number
  templatesCount: number
  currentPhase: string
  phaseStartedAt: string | Date
  phaseDurationSeconds: number
  isTimerPaused: boolean
  timerRemainingSeconds: number
}

const ARCHETYPE_LABELS: Record<string, { label: string; badgeClass: string }> = {
  CAPITAL: { label: 'Tőkeerős Vállalat (Capital Rich)', badgeClass: 'bg-blue-50 text-blue-700 border-blue-200' },
  RESOURCE: { label: 'Nyersanyag-óriás (Resource Giant)', badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  TECH: { label: 'Technológiai Bajnok (Tech Leader)', badgeClass: 'bg-purple-50 text-purple-700 border-purple-200' },
  EMERGING: { label: 'Feltörekvő Start-up (Emerging Team)', badgeClass: 'bg-amber-50 text-amber-700 border-amber-200' },
}

export default function TeamLedgerHUD({
  teamName,
  profileCode,
  cashBalance,
  paperSheets,
  scissorsCount,
  rulersCount,
  templatesCount,
  currentPhase,
  phaseStartedAt,
  phaseDurationSeconds,
  isTimerPaused,
  timerRemainingSeconds,
}: TeamLedgerHUDProps) {
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

  const isCritical = remainingSec <= 30 && !isTimerPaused && remainingSec > 0
  const isWarning = remainingSec <= 120 && !isTimerPaused && remainingSec > 30

  const archetypeInfo = ARCHETYPE_LABELS[profileCode] || {
    label: profileCode,
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-200',
  }

  return (
    <div className="space-y-4">
      {/* Topbar: Company Identity + Big Balances */}
      <div className="theme-card p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${archetypeInfo.badgeClass}`}
            >
              {archetypeInfo.label}
            </span>
            <span className="text-xs font-mono text-slate-500">
              Fázis: {currentPhase}
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            {teamName}
          </h1>
        </div>

        <div className="flex items-center gap-6">
          {/* Phase Timer */}
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
              Kör Hátralévő Ideje
            </span>
            <div
              className={`text-2xl font-mono font-bold tabular-nums ${
                isCritical
                  ? 'text-red-600 animate-pulse'
                  : isWarning
                  ? 'text-amber-600'
                  : isTimerPaused
                  ? 'text-slate-400'
                  : 'text-slate-900'
              }`}
            >
              {formattedTime}
            </div>
          </div>

          <div className="h-8 w-px bg-slate-200 hidden sm:block"></div>

          {/* Cash Balance */}
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
              Virtuális Készpénz
            </span>
            <div className="text-2xl lg:text-3xl font-mono font-extrabold text-blue-600 tabular-nums">
              ${cashBalance}
            </div>
          </div>
        </div>
      </div>

      {/* 4-Column Inventory HUD */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: A4 Paper */}
        <div className="theme-card p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-semibold">Nyersanyag (A4 Lap)</span>
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900 tabular-nums">
            {paperSheets} <span className="text-xs font-normal text-slate-500">lap</span>
          </div>
          <div className="text-[10px] font-medium pt-1">
            {paperSheets <= 1 ? (
              <span className="text-amber-600 font-bold">Kritikus alapanyaghiány!</span>
            ) : (
              <span className="text-slate-500">Gyártásra kész</span>
            )}
          </div>
        </div>

        {/* Card 2: Scissors */}
        <div className="theme-card p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-semibold">Vágóeszköz (Olló)</span>
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M7.864 4.243A7.5 7.5 0 0119.5 10.5c0 2.92-.556 5.709-1.568 8.268M5.742 6.364A7.465 7.465 0 004.5 10.5a7.464 7.464 0 01-1.15 3.993m1.989 3.559A11.209 11.209 0 008.25 10.5a3.75 3.75 0 117.5 0c0 .527-.021 1.049-.064 1.565m-9.761 4.01l7.39-7.39" />
            </svg>
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900 tabular-nums">
            {scissorsCount} <span className="text-xs font-normal text-slate-500">db</span>
          </div>
          <div className="text-[10px] font-medium pt-1">
            {scissorsCount > 1 ? (
              <span className="text-blue-600 font-bold">Bérbeadható kapacitás</span>
            ) : scissorsCount === 1 ? (
              <span className="text-slate-500">Csapat használatban</span>
            ) : (
              <span className="text-red-600 font-bold">Eszközhiány (bérlés szükséges)</span>
            )}
          </div>
        </div>

        {/* Card 3: Rulers */}
        <div className="theme-card p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-semibold">Mérőeszköz (Vonalzó)</span>
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900 tabular-nums">
            {rulersCount} <span className="text-xs font-normal text-slate-500">db</span>
          </div>
          <div className="text-[10px] font-medium pt-1">
            {rulersCount > 0 ? (
              <span className="text-slate-500">Pontos mérés biztosított</span>
            ) : (
              <span className="text-amber-600 font-bold">Selejtveszély (nincs vonalzó)</span>
            )}
          </div>
        </div>

        {/* Card 4: Templates */}
        <div className="theme-card p-4 space-y-1">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-semibold">Geometriai Sablon</span>
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
            </svg>
          </div>
          <div className="text-2xl font-mono font-extrabold text-slate-900 tabular-nums">
            {templatesCount} <span className="text-xs font-normal text-slate-500">db</span>
          </div>
          <div className="text-[10px] font-medium pt-1">
            {templatesCount > 0 ? (
              <span className="text-emerald-700 font-bold">Körgyártási monopólium</span>
            ) : (
              <span className="text-slate-500">Körök nem vághatók</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
