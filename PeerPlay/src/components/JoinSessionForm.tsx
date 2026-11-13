'use client'

import { useState } from 'react'
import { joinWorkshopSession } from '@/modules/session/actions'
import toast from 'react-hot-toast'

export default function JoinSessionForm({ prefillCode }: { prefillCode?: string }) {
  const [joinCode, setJoinCode] = useState(prefillCode || '')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [gdprConsent, setGdprConsent] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!gdprConsent) {
      toast.error('A csatlakozáshoz fogadd el az adatkezelési hozzájárulást!')
      return
    }

    setLoading(true)
    try {
      const { session, user } = await joinWorkshopSession(joinCode.trim(), name.trim(), email.trim())
      toast.success(`Üdvözlünk a szimulációban, ${user.name}!`)
      // Direct to survey/companion with userId query parameter
      window.location.href = `/survey/${session.id}?userId=${user.id}`
    } catch (e: any) {
      toast.error(e.message || 'Hiba a csatlakozás során. Ellenőrizd a kódot!')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleJoin} className="space-y-4 w-full">
      {/* PIN Code */}
      <div>
        <label className="text-xs font-mono uppercase font-bold text-slate-500 tracking-wider block mb-1">
          Munkamenet PIN Kód (6 Karakter)
        </label>
        <input
          type="text"
          value={joinCode}
          onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
          required
          maxLength={6}
          placeholder="PL. TRD-01"
          className="w-full text-center font-mono text-2xl font-black tracking-widest py-3 px-4 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
        />
      </div>

      {/* Name */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-1">
          Teljes Név
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="pl. Kovács Péter"
          className="w-full text-sm px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Work Email */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-1">
          Munkahelyi E-mail Cím
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="pl. peter.kovacs@cegnev.hu"
          className="w-full text-sm px-3.5 py-2.5 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* GDPR Checkbox */}
      <div className="pt-2">
        <label className="flex items-start gap-2.5 text-xs text-slate-600 leading-normal cursor-pointer select-none">
          <input
            type="checkbox"
            checked={gdprConsent}
            onChange={(e) => setGdprConsent(e.target.checked)}
            className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span>
            Hozzájárulok a szimulációban való részvételemhez és az eredmények szervezetdiagnosztikai aggregálásához.
          </span>
        </label>
      </div>

      {/* 48px Touch-friendly CTA Button */}
      <button
        type="submit"
        disabled={loading || !gdprConsent}
        className="w-full min-h-[48px] py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-sm rounded-lg shadow-sm transition flex items-center justify-center gap-2 cursor-pointer mt-4"
      >
        <span>{loading ? 'Csatlakozás...' : 'Csatlakozás a Munkamenethez →'}</span>
      </button>
    </form>
  )
}
