'use client'

import { useState, useRef } from 'react'
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

const SCALE_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

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

  const energyInputRef = useRef<HTMLInputElement>(null)

  const externalCandidates = allParticipants.filter(
    (p) => p.teamId !== myTeamId && p.id !== userId
  )

  const internalCandidates = allParticipants.filter(
    (p) => p.teamId === myTeamId && p.id !== userId
  )

  const toggleBroker = (candidateId: string, checked: boolean) => {
    setSelectedBrokers((prev) => {
      if (!checked) {
        return prev.filter((id) => id !== candidateId)
      }
      if (prev.includes(candidateId)) return prev
      if (prev.length >= 2) {
        toast('Legfeljebb 2 főt jelölhetsz meg.')
        return prev
      }
      return [...prev, candidateId]
    })
  }

  const selectFinalEnergy = (val: number) => {
    setFinalEnergy(val)
    if (energyInputRef.current) {
      energyInputRef.current.value = String(val)
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (loading) return
    setLoading(true)

    const form = e.currentTarget
    const formData = new FormData(form)
    const submittedEnergy = Number(formData.get('finalEnergy') || finalEnergy)
    const submittedReflection = String(formData.get('reflectionText') ?? reflectionText).trim()
    const brokersFromDom = formData.getAll('brokerNominations').map(String).filter(Boolean)
    const enablersFromDom = formData.getAll('internalEnablerNominations').map(String).filter(Boolean)

    const finalBrokers = brokersFromDom.length > 0 ? brokersFromDom.slice(0, 2) : selectedBrokers
    const finalEnablers = enablersFromDom.length > 0 ? enablersFromDom.slice(0, 1) : selectedEnablers

    try {
      const res = await fetch('/api/survey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phaseType: 'POST_GAME',
          sessionId,
          userId,
          brokerNominations: finalBrokers,
          internalEnablerNominations: finalEnablers,
          finalEnergy: submittedEnergy,
          reflectionText: submittedReflection,
        }),
      })

      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a visszajelzés mentésekor')
      }

      toast.success('Köszönjük a visszajelzésedet!')
      if (onSubmitted) {
        onSubmitted()
      } else {
        window.location.reload()
      }
    } catch (err: any) {
      toast.error(err.message || 'Hiba a visszajelzés mentésekor')
      setLoading(false)
    }
  }

  return (
    <form
      method="POST"
      action="/api/survey"
      onSubmit={handleSubmit}
      className="space-y-5"
    >
      <input type="hidden" name="phaseType" value="POST_GAME" />
      <input type="hidden" name="sessionId" value={sessionId} />
      <input type="hidden" name="userId" value={userId} />

      {/* Top Banner */}
      <div className="pb-2 border-b border-slate-100">
        <span className="text-[10px] font-mono uppercase font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
          Záró Értékelés
        </span>
        <h2 className="text-lg font-extrabold text-slate-900 tracking-tight mt-1">
          Záró Együttműködési Értékelés
        </h2>
      </div>

      {/* Step 1: Cross-Team Broker Nominations */}
      <div className="space-y-2">
        <label className="text-xs font-bold text-slate-900 block">
          1. Ki segítette leginkább a csapatok közötti megállapodást? (Max. 2 fő)
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto p-0.5">
          {externalCandidates.length === 0 ? (
            <div className="text-xs text-slate-400 italic py-1">
              Nincs más csapatban elérhető játékos.
            </div>
          ) : (
            externalCandidates.map((candidate) => {
              const isSelected = selectedBrokers.includes(candidate.id)
              return (
                <label
                  key={candidate.id}
                  className={`p-2.5 rounded-lg border text-left text-xs transition cursor-pointer flex items-center justify-between gap-2 select-none ${
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
                  <input
                    type="checkbox"
                    name="brokerNominations"
                    value={candidate.id}
                    checked={isSelected}
                    onChange={(e) => toggleBroker(candidate.id, e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-blue-600 accent-blue-600 shrink-0 cursor-pointer"
                  />
                </label>
              )
            })
          )}
        </div>
      </div>

      {/* Step 2: Internal Team Anchor (Enabler Nominations) */}
      <div className="space-y-2 pt-2 border-t border-slate-100">
        <label className="text-xs font-bold text-slate-900 block">
          2. Saját csapatodon belül ki volt a legfőbb támasz? (1 fő)
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-44 overflow-y-auto p-0.5">
          {internalCandidates.length === 0 ? (
            <div className="text-xs text-slate-400 italic py-1">
              Nincs más csapattag a vállalatodban.
            </div>
          ) : (
            internalCandidates.map((candidate) => {
              const isSelected = selectedEnablers.includes(candidate.id)
              return (
                <label
                  key={candidate.id}
                  className={`p-2.5 rounded-lg border text-left text-xs transition cursor-pointer flex items-center justify-between gap-2 select-none ${
                    isSelected
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-900 font-bold'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <span className="truncate">{candidate.name}</span>
                  <input
                    type="radio"
                    name="internalEnablerNominations"
                    value={candidate.id}
                    checked={isSelected}
                    onChange={() => setSelectedEnablers([candidate.id])}
                    className="w-4 h-4 border-slate-300 text-emerald-600 accent-emerald-600 shrink-0 cursor-pointer"
                  />
                </label>
              )
            })
          )}
        </div>
      </div>

      {/* Step 3: Final Energy Slider + 1..10 Quick Tap */}
      <div className="space-y-2 pt-2 border-t border-slate-100">
        <div className="flex justify-between items-center">
          <label
            htmlFor="slider-final-energy"
            className="text-xs font-semibold text-slate-800"
          >
            3. Energiaszinted a játék végén:
          </label>
          <span className="font-mono text-xl font-extrabold text-blue-600 tabular-nums">
            <span id="final-energy-val">{finalEnergy}</span>{' '}
            <span className="text-xs text-slate-400">/ 10</span>
          </span>
        </div>

        <div className="py-1">
          <input
            ref={energyInputRef}
            id="slider-final-energy"
            name="finalEnergy"
            type="range"
            min="1"
            max="10"
            step="1"
            defaultValue={finalEnergy}
            onChange={(e) => setFinalEnergy(parseInt(e.target.value, 10))}
            onInput={(e) =>
              setFinalEnergy(parseInt((e.target as HTMLInputElement).value, 10))
            }
            className="touch-slider cursor-pointer accent-blue-600"
          />
        </div>

        <div className="grid grid-cols-10 gap-1 pt-0.5">
          {SCALE_VALUES.map((val) => {
            const active = finalEnergy === val
            return (
              <button
                key={val}
                type="button"
                data-slider-target="slider-final-energy"
                data-display-target="final-energy-val"
                data-val={val}
                onClick={() => selectFinalEnergy(val)}
                className={`h-8 rounded font-mono text-xs font-bold transition cursor-pointer flex items-center justify-center border ${
                  active
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {val}
              </button>
            )
          })}
        </div>
      </div>

      {/* Step 4: Reflection Textarea */}
      <div className="space-y-1.5 pt-2 border-t border-slate-100">
        <label htmlFor="reflectionText" className="text-xs font-semibold text-slate-800 block">
          4. Rövid észrevétel (opcionális)
        </label>
        <textarea
          id="reflectionText"
          name="reflectionText"
          rows={2}
          maxLength={300}
          placeholder="Mi volt a legfontosabb tanulság?"
          value={reflectionText}
          onChange={(e) => setReflectionText(e.target.value)}
          className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full min-h-[48px] py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-lg shadow-sm transition flex items-center justify-center gap-2 cursor-pointer"
      >
        <span>{loading ? 'Mentés...' : 'Értékelés Véglegesítése →'}</span>
      </button>

      <script
        dangerouslySetInnerHTML={{
          __html: `
(function(){
  var s = document.getElementById('slider-final-energy');
  var d = document.getElementById('final-energy-val');
  if (s && d) {
    s.addEventListener('input', function() {
      d.textContent = s.value;
      var btns = document.querySelectorAll('[data-slider-target="slider-final-energy"]');
      for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        if (b.getAttribute('data-val') === s.value) {
          b.className = 'h-8 rounded font-mono text-xs font-bold transition cursor-pointer flex items-center justify-center border bg-blue-600 text-white border-blue-600 shadow-xs';
        } else {
          b.className = 'h-8 rounded font-mono text-xs font-bold transition cursor-pointer flex items-center justify-center border bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100';
        }
      }
    });
  }
  var btns = document.querySelectorAll('[data-slider-target="slider-final-energy"]');
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function(e) {
      var val = e.currentTarget.getAttribute('data-val');
      if (s && val) {
        s.value = val;
        s.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (d && val) d.textContent = val;
    });
  }
})();
          `,
        }}
      />
    </form>
  )
}
