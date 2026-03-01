'use client'

import { useState } from 'react'
import { joinSession } from '@/modules/session/actions'

export default function JoinSessionForm() {
    const [joinCode, setJoinCode] = useState('')
    const [username, setUsername] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [successData, setSuccessData] = useState<{ joinCode: string, userId: string } | null>(null)

    const handleJoin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setSuccessData(null)

        try {
            const { session, user } = await joinSession(joinCode, username)
            setSuccessData({ joinCode: session.joinCode, userId: user.id })
            window.location.href = `/play/${session.joinCode}?userId=${user.id}`
        } catch (e: any) {
            setError(e.message || 'Failed to join session')
        } finally {
            setLoading(false)
        }
    }

    if (successData) {
        return (
            <div className="text-center space-y-4">
                <h2 className="text-xl font-semibold text-green-600">Successfully Joined!</h2>
                <p className="text-gray-600">Redirecting to lobby...</p>
                <button
                    onClick={() => window.location.href = `/play/${successData.joinCode}?userId=${successData.userId}`}
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
                <label className="block text-sm font-medium text-gray-700">Room Code</label>
                <input
                    type="text"
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value)}
                    required
                    maxLength={4}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 uppercase"
                    placeholder="e.g. A1B2"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">Your Username</label>
                <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                    placeholder="e.g. Alice"
                />
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
