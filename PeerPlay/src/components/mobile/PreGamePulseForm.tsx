'use client'

import { useState } from 'react'
import { submitPreGameSurvey } from '@/modules/survey/actions'
import toast from 'react-hot-toast'

interface PreGamePulseFormProps {
  sessionId: string
  userId: string
  onSubmitted?: () => void
}

export default function PreGamePulseForm({
  sessionId,
  userId,
  onSubmitted,
}: PreGamePulseFormProps) {
  const [energy, setEnergy] = useState<number>(7)
  const [engagement, setEngagement] = useState<number>(8)
  const [loading, setLoading] = useState<boolean>(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await submitPreGameSurvey(sessionId, userId, energy, engagement)
      toast.success('Köszönjük! A kezdő energiaszintedet rögzítettük.')
      if (onSubmitted) onSubmitted()
    } catch (err: any) {
      toast.error(err.message || 'Hiba a válaszok elküldésekor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Top Banner */}
      <div className="pb-2 border-b border-slate-100">
        <span className="text-[10px] font-mono uppercase font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
          1. Fázis: Hangolódás · S-MOB-02
        </span>
        <h2 className="text-xl font-extrabold text-slate-900 tracking-tight mt-1">
          Pre-Game Pulse Felmérés
        </h2>
        <p className="text-xs text-slate-500">
          Két gyors csúszka az érkezési állapotodról a szimuláció kezdete előtt.
        </p>
      </div>

      {/* Slider 1: Energy */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-xs font-semibold text-slate-800">
            1. Milyen a fizikai & mentális energiaszinted most?
          </label>
          <span className="font-mono text-xl font-extrabold text-blue-600 tabular-nums">
            {energy} <span className="text-xs text-slate-400">/ 10</span>
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="10"
          value={energy}
          onChange={(e) => setEnergy(parseInt(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-[10px] font-medium text-slate-400">
          <span>1 - Kimerült, tompa</span>
          <span>10 - Tettre kész, energikus</span>
        </div>
      </div>

      {/* Slider 2: Engagement */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-xs font-semibold text-slate-800">
            2. Mekkora kíváncsisággal és nyitottsággal érkeztél?
          </label>
          <span className="font-mono text-xl font-extrabold text-blue-600 tabular-nums">
            {engagement} <span className="text-xs text-slate-400">/ 10</span>
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="10"
          value={engagement}
          onChange={(e) => setEngagement(parseInt(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-[10px] font-medium text-slate-400">
          <span>1 - Inkább kihagynám</span>
          <span>10 - Kíváncsi és motivált vagyok</span>
        </div>
      </div>

      {/* 48px Touch Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full min-h-[48px] py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-lg shadow-sm transition flex items-center justify-center gap-2 cursor-pointer mt-6"
      >
        <span>{loading ? 'Rögzítés...' : 'Válaszok Rögzítése →'}</span>
      </button>
    </form>
  )
}
