'use client'

import { useState, useRef } from 'react'
import toast from 'react-hot-toast'

interface PreGamePulseFormProps {
  sessionId: string
  userId: string
  onSubmitted?: () => void
}

const SCALE_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

export default function PreGamePulseForm({
  sessionId,
  userId,
  onSubmitted,
}: PreGamePulseFormProps) {
  const [energy, setEnergy] = useState<number>(7)
  const [engagement, setEngagement] = useState<number>(8)
  const [loading, setLoading] = useState<boolean>(false)

  const energyInputRef = useRef<HTMLInputElement>(null)
  const engagementInputRef = useRef<HTMLInputElement>(null)

  const selectEnergy = (val: number) => {
    setEnergy(val)
    if (energyInputRef.current) {
      energyInputRef.current.value = String(val)
    }
  }

  const selectEngagement = (val: number) => {
    setEngagement(val)
    if (engagementInputRef.current) {
      engagementInputRef.current.value = String(val)
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (loading) return
    setLoading(true)

    const form = e.currentTarget
    const formData = new FormData(form)
    const submittedEnergy = Number(formData.get('energy') || energy)
    const submittedEngagement = Number(formData.get('engagement') || engagement)

    try {
      const res = await fetch('/api/survey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phaseType: 'PRE_GAME',
          sessionId,
          userId,
          energy: submittedEnergy,
          engagement: submittedEngagement,
        }),
      })

      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.success) {
        throw new Error(data?.error || 'Hiba a válaszok elküldésekor')
      }

      toast.success('Köszönjük! A kezdő energiaszintedet rögzítettük.')
      if (onSubmitted) {
        onSubmitted()
      } else {
        window.location.reload()
      }
    } catch (err: any) {
      toast.error(err.message || 'Hiba a válaszok elküldésekor')
      setLoading(false)
    }
  }

  return (
    <form
      method="POST"
      action="/api/survey"
      onSubmit={handleSubmit}
      className="space-y-6"
    >
      {/* Hidden inputs for native HTML POST fallback */}
      <input type="hidden" name="phaseType" value="PRE_GAME" />
      <input type="hidden" name="sessionId" value={sessionId} />
      <input type="hidden" name="userId" value={userId} />

      {/* Top Banner */}
      <div className="pb-2 border-b border-slate-100">
        <span className="text-[10px] font-mono uppercase font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
          Nyitó Felmérés
        </span>
        <h2 className="text-lg font-extrabold text-slate-900 tracking-tight mt-1">
          Kezdő Hangulatfelmérés
        </h2>
      </div>

      {/* Slider 1: Energy */}
      <div className="space-y-2.5">
        <div className="flex justify-between items-center gap-2">
          <label
            htmlFor="slider-energy"
            className="text-xs font-semibold text-slate-800"
          >
            1. Milyen a fizikai &amp; mentális energiaszinted most?
          </label>
          <span className="font-mono text-xl font-extrabold text-blue-600 tabular-nums shrink-0">
            <span id="energy-val">{energy}</span>{' '}
            <span className="text-xs text-slate-400">/ 10</span>
          </span>
        </div>

        <div className="py-1">
          <input
            ref={energyInputRef}
            id="slider-energy"
            name="energy"
            type="range"
            min="1"
            max="10"
            step="1"
            defaultValue={energy}
            onChange={(e) => setEnergy( parseInt(e.target.value, 10) )}
            onInput={(e) =>
              setEnergy(parseInt((e.target as HTMLInputElement).value, 10))
            }
            className="touch-slider cursor-pointer accent-blue-600"
          />
        </div>

        {/* 1..10 Quick Tap Buttons */}
        <div className="grid grid-cols-10 gap-1 pt-0.5" data-quick-group="energy">
          {SCALE_VALUES.map((val) => {
            const active = energy === val
            return (
              <button
                key={val}
                type="button"
                data-slider-target="slider-energy"
                data-display-target="energy-val"
                data-val={val}
                onClick={() => selectEnergy(val)}
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

        <div className="flex justify-between text-[10px] font-medium text-slate-400">
          <span>1 - Kimerült, tompa</span>
          <span>10 - Tettre kész, energikus</span>
        </div>
      </div>

      {/* Slider 2: Engagement */}
      <div className="space-y-2.5 pt-2 border-t border-slate-100">
        <div className="flex justify-between items-center gap-2">
          <label
            htmlFor="slider-engagement"
            className="text-xs font-semibold text-slate-800"
          >
            2. Mekkora kíváncsisággal és nyitottsággal érkeztél?
          </label>
          <span className="font-mono text-xl font-extrabold text-blue-600 tabular-nums shrink-0">
            <span id="engagement-val">{engagement}</span>{' '}
            <span className="text-xs text-slate-400">/ 10</span>
          </span>
        </div>

        <div className="py-1">
          <input
            ref={engagementInputRef}
            id="slider-engagement"
            name="engagement"
            type="range"
            min="1"
            max="10"
            step="1"
            defaultValue={engagement}
            onChange={(e) => setEngagement(parseInt(e.target.value, 10))}
            onInput={(e) =>
              setEngagement(parseInt((e.target as HTMLInputElement).value, 10))
            }
            className="touch-slider cursor-pointer accent-blue-600"
          />
        </div>

        {/* 1..10 Quick Tap Buttons */}
        <div className="grid grid-cols-10 gap-1 pt-0.5" data-quick-group="engagement">
          {SCALE_VALUES.map((val) => {
            const active = engagement === val
            return (
              <button
                key={val}
                type="button"
                data-slider-target="slider-engagement"
                data-display-target="engagement-val"
                data-val={val}
                onClick={() => selectEngagement(val)}
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

      {/* Pre-hydration progressive enhancement script for instant slider/button feedback */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
(function(){
  function bindSlider(sliderId, displayId) {
    var s = document.getElementById(sliderId);
    var d = document.getElementById(displayId);
    if (!s || !d) return;
    s.addEventListener('input', function() {
      d.textContent = s.value;
      var btns = document.querySelectorAll('[data-slider-target="' + sliderId + '"]');
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
  bindSlider('slider-energy', 'energy-val');
  bindSlider('slider-engagement', 'engagement-val');

  var allBtns = document.querySelectorAll('[data-slider-target]');
  for (var i = 0; i < allBtns.length; i++) {
    allBtns[i].addEventListener('click', function(e) {
      var btn = e.currentTarget;
      var sId = btn.getAttribute('data-slider-target');
      var dId = btn.getAttribute('data-display-target');
      var val = btn.getAttribute('data-val');
      var s = document.getElementById(sId);
      var d = document.getElementById(dId);
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
