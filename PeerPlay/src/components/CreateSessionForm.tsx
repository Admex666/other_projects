'use client'

import { useState } from 'react'
import { createWorkshopSession } from '@/modules/session/actions'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

export default function CreateSessionForm({ orgId }: { orgId?: string }) {
  const [loading, setLoading] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const router = useRouter()

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const session = await createWorkshopSession(orgId, undefined, sessionName || undefined)
      toast.success('Munkamenet sikeresen létrehozva!')
      router.push(`/sessions/${session.id}`)
    } catch (err: any) {
      toast.error(err.message || 'Hiba történt a munkamenet létrehozásakor.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleCreate} className="flex items-center gap-3">
      <input
        type="text"
        placeholder="Munkamenet megnevezése (opcionális)"
        value={sessionName}
        onChange={(e) => setSessionName(e.target.value)}
        className="px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64 shadow-2xs"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-xs transition-colors flex items-center gap-2 cursor-pointer"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        {loading ? 'Létrehozás...' : 'Új Munkamenet'}
      </button>
    </form>
  )
}
