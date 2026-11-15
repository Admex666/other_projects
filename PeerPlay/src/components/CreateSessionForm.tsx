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
      toast.success('Munkamenet létrehozva!')
      router.push(`/sessions/${session.id}`)
    } catch (err: any) {
      toast.error(err.message || 'Hiba történt a létrehozáskor.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleCreate} className="flex flex-wrap items-center gap-2">
      <input
        type="text"
        placeholder="Új játék neve (opcionális)"
        value={sessionName}
        onChange={(e) => setSessionName(e.target.value)}
        className="px-3 py-1.5 text-xs sm:text-sm bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 w-48 sm:w-56 shadow-2xs"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs sm:text-sm font-bold rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer shrink-0"
      >
        <span>+ {loading ? 'Létrehozás...' : 'Új Munkamenet'}</span>
      </button>
    </form>
  )
}
