'use client'

import { useState, useEffect } from 'react'
import { verifyFacilitatorPin } from '@/modules/session/actions'
import Link from 'next/link'

interface FacilitatorPinGateProps {
  children: React.ReactNode
}

export default function FacilitatorPinGate({ children }: FacilitatorPinGateProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [pin, setPin] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // Check if session storage has verified flag
    const storedAuth = sessionStorage.getItem('peerplay_facilitator_auth')
    if (storedAuth === 'true') {
      setIsAuthenticated(true)
    } else {
      setIsAuthenticated(false)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pin.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const res = await verifyFacilitatorPin(pin)
      if (res.success) {
        sessionStorage.setItem('peerplay_facilitator_auth', 'true')
        setIsAuthenticated(true)
      } else {
        setError(res.error || 'Helytelen PIN kód.')
        setPin('')
      }
    } catch {
      setError('Hiba történt az ellenőrzés során. Próbáld újra!')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    sessionStorage.removeItem('peerplay_facilitator_auth')
    setIsAuthenticated(false)
    setPin('')
    setError(null)
  }

  // Initial loading state while reading sessionStorage
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-sans">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  // If authenticated, render children with top right security indicator
  if (isAuthenticated) {
    return (
      <div className="relative">
        <div className="bg-slate-900 text-slate-300 text-xs px-6 py-2 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span className="font-medium text-slate-200">Facilitátori Munkamenet Hitelesítve</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-400">Vezérlési Jogosultság Aktív</span>
          </div>
          <button
            onClick={handleLogout}
            className="text-slate-400 hover:text-white font-medium flex items-center gap-1.5 transition"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
            <span>Zárolás & Kilépés</span>
          </button>
        </div>
        {children}
      </div>
    )
  }

  // Locked state: show PIN entry form
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 font-sans">
      <div className="theme-card max-w-md w-full p-8 sm:p-10 space-y-6 text-center">
        {/* Security Shield Icon */}
        <div className="w-14 h-14 mx-auto rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-2xs">
          <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
          </svg>
        </div>

        <div className="space-y-1.5">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Facilitátori Belépés
          </h1>
          <p className="text-xs text-slate-500 leading-relaxed max-w-sm mx-auto">
            A vezérlőközpont és a munkamenetek kezeléséhez add meg a facilitátori PIN kódot.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div>
            <input
              type="password"
              inputMode="numeric"
              maxLength={10}
              autoFocus
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="••••"
              className="w-full text-center text-2xl font-mono tracking-widest py-3 px-4 rounded-xl border border-slate-200 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 font-medium">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !pin.trim()}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold rounded-xl text-sm transition shadow-xs flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>Belépés a Vezérlőközpontba</span>
            )}
          </button>
        </form>

        <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
          <Link href="/" className="hover:text-slate-600 transition">
            ← Vissza a Kezdőlapra
          </Link>
          <span className="font-mono text-[11px]">PeerPlay Enterprise</span>
        </div>
      </div>
    </div>
  )
}
