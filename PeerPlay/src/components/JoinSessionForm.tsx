'use client'

import { useState } from 'react'
import { joinSession } from '@/modules/session/actions'

export default function JoinSessionForm() {
    const [sessionId, setSessionId] = useState('')
    const [userId, setUserId] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)

    const handleJoin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setSuccess(false)

        try {
            await joinSession(sessionId, userId)
            setSuccess(true)
        } catch (e: any) {
            setError(e.message || 'Failed to join session')
        } finally {
            setLoading(false)
        }
    }

    if (success) {
        return (
            <div className="text-center space-y-4">
                <h2 className="text-xl font-semibold text-green-600">Successfully Joined!</h2>
                <p className="text-gray-600">Waiting for HR to start the session in the lobby...</p>
                <button
                    onClick={() => window.location.reload()}
                    className="text-indigo-600 underline text-sm mt-4 hover:text-indigo-800"
                >
                    Check status
                </button>
            </div>
        )
    }

    return (
        <form onSubmit={handleJoin} className="space-y-4 w-full max-w-sm">
            {error && <div className="text-red-500 text-sm p-2 bg-red-50 rounded">{error}</div>}
            <div>
                <label className="block text-sm font-medium text-gray-700">Session ID</label>
                <input
                    type="text"
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Your User ID</label>
                <input
                    type="text"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    placeholder="e.g. 12345..."
                />
                <p className="text-xs text-gray-500 mt-1">For MVP, copy a User UUID from the DB</p>
            </div>

            <button
                type="submit"
                disabled={loading}
                className={`w-full py-2 px-4 shadow-md text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                {loading ? 'Joining...' : 'Join Session Lobby'}
            </button>
        </form>
    )
}
