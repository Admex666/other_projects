'use client'

import { useState } from 'react'
import { submitPostGameFeedback } from '@/modules/survey/actions'
import toast from 'react-hot-toast'

interface ParticipantInfo {
  id: string
  name: string
  teamId: string
  teamName: string
}

interface PostGamePeerFeedbackFormProps {
  sessionId: string
  userId: string
  myTeamId: string
  allParticipants: ParticipantInfo[]
  onSubmitted?: () => void
}

export default function PostGamePeerFeedbackForm({
  sessionId,
  userId,
  myTeamId,
  allParticipants,
  onSubmitted,
}: PostGamePeerFeedbackFormProps) {
  const [selectedBrokers, setSelectedBrokers] = useState<string[]>([])
  const [selectedEnablers, setSelectedEnablers] = useState<string[]>([])
  const [finalEnergy, setFinalEnergy] = useState<number>(8)
  const [reflectionText, setReflectionText] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)

  // External participants (other teams)
  const externalCandidates = allParticipants.filter(
    (p) => p.teamId !== myTeamId && p.id !== userId
  )

  // Internal participants (own team)
  const internalCandidates = allParticipants.filter(
    (p) => p.teamId === myTeamId && p.id !== userId
  )

  const toggleBroker = (candidateId: string) => {
    setSelectedBrokers((prev) => {
      if (prev.includes(candidateId)) {
        return prev.filter((id) => id !== candidateId)
      }
      if (prev.length >= 2) {
        toast('Legfeljebb 2 koordinátort jelölhetsz meg.')
        return prev
      }
      return [...prev, candidateId]
    })
  }

  const toggleEnabler = (candidateId: string) => {
    setSelectedEnablers((prev) => {
      if (prev.includes(candidateId)) {
        return []
      }
      return [candidateId]
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await submitPostGameFeedback(
        sessionId,
        userId,
        selectedBrokers,
        selectedEnablers,
        finalEnergy,
        reflectionText
      )
      toast.success('Köszönjük értékes visszajelzésedet!')
      if (onSubmitted) onSubmitted()
    } catch (err: any) {
      toast.error(err.message || 'Hiba a visszajelzés mentésekor')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Top Banner */}
      <div className="pb-2 border-b border-slate-100">
        <span className="text-[10px] font-mono uppercase font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
          10. Fázis: Peer Reflexió · S-MOB-04
        </span>
        <h2 className="text-xl font-extrabold text-slate-900 tracking-tight mt-1">
          Post-Game Együttműködési Értékelés
        </h2>
        <p className="text-xs text-slate-500">
          A szimuláció zárásaként értékeld a társak közötti együttműködést és saját tapasztalataidat.
        </p>
      </div>

      {/* Step 1: Cross-Team Broker Nominations */}
      <div className="space-y-2.5">
        <div>
          <label className="text-xs font-bold text-slate-900 block">
            1. Keresztfunkcionális Koordinátor (Broker Nomináció)
          </label>
          <p className="text-xs text-slate-500">
            Ki segítette leginkább a többi vállalat közül az információáramlást és a megállapodások létrejöttét? (Max. 2 fő)
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-1">
          {externalCandidates.length === 0 ? (
            <div className="text-xs text-slate-400 italic py-2">
              Nincs más csapatban elérhető játékos.
            </div>
          ) : (
            externalCandidates.map((candidate) => {
              const isSelected = selectedBrokers.includes(candidate.id)
              return (
                <button
                  type="button"
                  key={candidate.id}
                  onClick={() => toggleBroker(candidate.id)}
                  className={`p-2.5 rounded-lg border text-left text-xs transition cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-blue-50 border-blue-500 text-blue-900 font-bold'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <div className="truncate">
                    <span className="block truncate">{candidate.name}</span>
                    <span className="text-[10px] font-mono text-slate-400 font-normal">
                      {candidate.teamName}
                    </span>
                  </div>
                  {isSelected && (
                    <span className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0">
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    </span>
                  )}
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Step 2: Internal Team Anchor (Enabler Nominations) */}
      <div className="space-y-2.5 pt-2 border-t border-slate-100">
        <div>
          <label className="text-xs font-bold text-slate-900 block">
            2. Belső Csapattámasz (Internal Enabler)
          </label>
          <p className="text-xs text-slate-500">
            A saját csapatodon belül ki volt a legfőbb operatív motor vagy támasz? (1 fő)
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-1">
          {internalCandidates.length === 0 ? (
            <div className="text-xs text-slate-400 italic py-2">
              Nincs más csapattag a vállalatodban.
            </div>
          ) : (
            internalCandidates.map((candidate) => {
              const isSelected = selectedEnablers.includes(candidate.id)
              return (
                <button
                  type="button"
                  key={candidate.id}
                  onClick={() => toggleEnabler(candidate.id)}
                  className={`p-2.5 rounded-lg border text-left text-xs transition cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-900 font-bold'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <span className="truncate">{candidate.name}</span>
                  {isSelected && (
                    <span className="w-4 h-4 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
                      <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    </span>
                  )}
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Step 3: Final Energy Slider */}
      <div className="space-y-2 pt-2 border-t border-slate-100">
        <div className="flex justify-between items-center">
          <label className="text-xs font-semibold text-slate-800">
            3. Milyen az energiaszinted a játék zárásakor?
          </label>
          <span className="font-mono text-xl font-extrabold text-blue-600 tabular-nums">
            {finalEnergy} <span className="text-xs text-slate-400">/ 10</span>
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="10"
          value={finalEnergy}
          onChange={(e) => setFinalEnergy(parseInt(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex justify-between text-[10px] font-medium text-slate-400">
          <span>1 - Lemerültem</span>
          <span>10 - Feltöltődve, energikusan</span>
        </div>
      </div>

      {/* Step 4: Reflection Textarea */}
      <div className="space-y-1.5 pt-2 border-t border-slate-100">
        <label className="text-xs font-semibold text-slate-800 block">
          4. Legfontosabb felismerésed (Opcionális)
        </label>
        <textarea
          rows={2}
          maxLength={300}
          placeholder="Mi lepett meg leginkább a csapatok közötti tárgyalások során?"
          value={reflectionText}
          onChange={(e) => setReflectionText(e.target.value)}
          className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        />
      </div>

      {/* Footnote on Anonymity */}
      <p className="text-[11px] text-slate-400 italic">
        A válaszok anonimizálva, kizárólag aggregált hálózati mutatókként kerülnek feldolgozásra a záró debrief és ONA riport során.
      </p>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full min-h-[48px] py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-lg shadow-sm transition flex items-center justify-center gap-2 cursor-pointer"
      >
        <span>{loading ? 'Mentés...' : 'Értékelés Véglegesítése →'}</span>
      </button>
    </form>
  )
}
