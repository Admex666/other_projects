'use client'

import { useState } from 'react'
import toast from 'react-hot-toast'

export default function JoinSessionForm({ prefillCode }: { prefillCode?: string }) {
  const [joinCode, setJoinCode] = useState(prefillCode || '')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [gdprConsent, setGdprConsent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleJoin = async () => {
    if (loading) return
    setErrorMessage(null)

    const cleanCode = (joinCode || '').trim().toUpperCase()
    const cleanName = (name || '').trim()
    const cleanEmail = (email || '').trim().toLowerCase()

    if (!cleanCode) {
      const msg = 'Kérlek add meg a munkamenet PIN kódot!'
      setErrorMessage(msg)
      toast.error(msg)
      return
    }

    if (!cleanName) {
      const msg = 'Kérlek add meg a teljes nevedet!'
      setErrorMessage(msg)
      toast.error(msg)
      return
    }

    if (!cleanEmail || !cleanEmail.includes('@')) {
      const msg = 'Kérlek érvényes munkahelyi e-mail címet adj meg!'
      setErrorMessage(msg)
      toast.error(msg)
      return
    }

    if (!gdprConsent) {
      const msg = 'A csatlakozáshoz kérlek pipáld be az adatkezelési hozzájárulást!'
      setErrorMessage(msg)
      toast.error(msg)
      return
    }

    setLoading(true)

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 12000)

    try {
      const res = await fetch('/api/join', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          joinCode: cleanCode,
          name: cleanName,
          email: cleanEmail,
        }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)
      const data = await res.json()

      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Hiba a csatlakozás során. Ellenőrizd a kódot!')
      }

      toast.success(`Sikeres csatlakozás! Üdvözlünk, ${data.user.name}!`)
      // Navigálás a felmérésre
      window.location.href = `/survey/${data.session.id}?userId=${data.user.id}`
    } catch (e: any) {
      clearTimeout(timeoutId)
      const msg =
        e.name === 'AbortError'
          ? 'Időtúllépés a szerver felé. Kérlek ellenőrizd a kapcsolatot és próbáld újra!'
          : e.message || 'Hiba a csatlakozás során. Kérlek próbáld újra!'
      setErrorMessage(msg)
      toast.error(msg)
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleJoin()
    }
  }

  return (
    <div className="space-y-4 w-full">
      {/* Error Banner */}
      {errorMessage && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-xl flex items-center gap-2.5 animate-in fade-in slide-in-from-top-1 duration-200">
          <svg className="w-4 h-4 shrink-0 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="leading-snug">{errorMessage}</span>
        </div>
      )}

      {/* PIN Code */}
      <div>
        <label htmlFor="joinCode" className="text-xs font-mono uppercase font-bold text-slate-500 tracking-wider block mb-1">
          Munkamenet PIN Kód
        </label>
        <input
          id="joinCode"
          name="joinCode"
          type="text"
          value={joinCode}
          onChange={(e) => {
            setJoinCode(e.target.value.toUpperCase())
            if (errorMessage) setErrorMessage(null)
          }}
          onKeyDown={handleKeyDown}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="characters"
          spellCheck="false"
          maxLength={12}
          placeholder="PL. DEMO01"
          className="w-full text-center font-mono text-2xl font-black tracking-widest py-3 px-4 bg-slate-50 border border-slate-300 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase touch-manipulation"
        />
      </div>

      {/* Name */}
      <div>
        <label htmlFor="fullName" className="text-xs font-semibold text-slate-700 block mb-1">
          Teljes Név
        </label>
        <input
          id="fullName"
          name="fullName"
          type="text"
          value={name}
          onChange={(e) => {
            setName(e.target.value)
            if (errorMessage) setErrorMessage(null)
          }}
          onKeyDown={handleKeyDown}
          autoComplete="name"
          autoCapitalize="words"
          placeholder="pl. Kovács Péter"
          className="w-full text-sm px-3.5 py-3 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 touch-manipulation"
        />
      </div>

      {/* Work Email */}
      <div>
        <label htmlFor="workEmail" className="text-xs font-semibold text-slate-700 block mb-1">
          Munkahelyi E-mail Cím
        </label>
        <input
          id="workEmail"
          name="workEmail"
          type="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            if (errorMessage) setErrorMessage(null)
          }}
          onKeyDown={handleKeyDown}
          autoComplete="email"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck="false"
          inputMode="email"
          placeholder="pl. peter.kovacs@cegnev.hu"
          className="w-full text-sm px-3.5 py-3 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 touch-manipulation"
        />
      </div>

      {/* Native Interactive GDPR Checkbox Card */}
      <div className="pt-1">
        <label
          htmlFor="gdprConsent"
          className={`w-full min-h-[56px] p-3.5 rounded-xl border transition-all cursor-pointer flex items-center gap-3.5 touch-manipulation active:scale-[0.99] select-none ${
            gdprConsent
              ? 'bg-blue-50/90 border-blue-400 text-slate-900 ring-1 ring-blue-400'
              : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
          }`}
        >
          <input
            id="gdprConsent"
            name="gdprConsent"
            type="checkbox"
            checked={gdprConsent}
            onChange={(e) => {
              setGdprConsent(e.target.checked)
              if (errorMessage) setErrorMessage(null)
            }}
            className="w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500 shrink-0 cursor-pointer accent-blue-600"
          />
          <span className="text-xs font-normal leading-relaxed text-left cursor-pointer">
            Hozzájárulok a szimulációban való részvételemhez és az eredmények szervezetdiagnosztikai aggregálásához.
          </span>
        </label>
      </div>

      {/* 52px Touch-friendly CTA Button */}
      <button
        type="button"
        onClick={handleJoin}
        disabled={loading}
        className="w-full min-h-[52px] py-3.5 px-4 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:opacity-60 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer mt-3 touch-manipulation active:scale-[0.98]"
      >
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Csatlakozás folyamatban...
          </span>
        ) : (
          <span>Csatlakozás a Munkamenethez →</span>
        )}
      </button>
    </div>
  )
}
