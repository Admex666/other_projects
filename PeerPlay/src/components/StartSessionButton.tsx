'use client'

import { useState } from 'react'
import { startSession } from '@/modules/session/actions'
import { useRouter } from 'next/navigation'

export default function StartSessionButton({ sessionId, participantsCount }: { sessionId: string, participantsCount: number }) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()

    const handleStart = async () => {
        if (participantsCount === 0) {
            setError('Cannot start without participants.')
            return
        }

        setLoading(true)
        setError(null)
        try {
            await startSession(sessionId)
            router.refresh()
        } catch (e: any) {
            setError(e.message || 'Failed to start session')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col items-end">
            {error && <span className="text-red-500 text-xs mb-2">{error}</span>}
            <button
                onClick={handleStart}
                disabled={loading || participantsCount === 0}
                className={`px-6 py-2 bg-indigo-600 text-white font-bold rounded-lg shadow hover:bg-indigo-700 
          ${loading || participantsCount === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                {loading ? 'Starting...' : 'Start Session'}
            </button>
            {participantsCount === 0 && (
                <span className="text-xs text-gray-500 mt-2">Waiting for participants...</span>
            )}
        </div>
    )
}
