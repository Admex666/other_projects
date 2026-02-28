'use client'

import { useState } from 'react'
import { logTrade } from '@/modules/interaction/actions'
import { User } from '@prisma/client'

export default function TradeActionForm({
    sessionId,
    currentUserId,
    otherParticipants
}: {
    sessionId: string,
    currentUserId: string,
    otherParticipants: User[]
}) {
    const [toUserId, setToUserId] = useState(otherParticipants[0]?.id || '')
    const [resourceType, setResourceType] = useState('tech')
    const [quantity, setQuantity] = useState(1)

    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleTrade = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setSuccess(false)
        setError(null)

        try {
            await logTrade(sessionId, currentUserId, toUserId, resourceType, quantity)
            setSuccess(true)
            setTimeout(() => setSuccess(false), 3000)
        } catch (err: any) {
            setError(err.message || 'Trade failed')
        } finally {
            setLoading(false)
        }
    }

    if (otherParticipants.length === 0) {
        return <p className="text-gray-500 italic">No one else is in the session yet.</p>
    }

    return (
        <form onSubmit={handleTrade} className="space-y-4">
            {error && <div className="text-red-500 bg-red-50 p-2 rounded text-sm">{error}</div>}
            {success && <div className="text-green-600 bg-green-50 p-2 rounded text-sm">Trade successful!</div>}

            <div>
                <label className="block text-sm font-medium text-gray-700">Send to</label>
                <select
                    value={toUserId}
                    onChange={(e) => setToUserId(e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm border"
                >
                    {otherParticipants.map(user => (
                        <option key={user.id} value={user.id}>
                            {user.name} ({user.role})
                        </option>
                    ))}
                </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Resource</label>
                    <select
                        value={resourceType}
                        onChange={(e) => setResourceType(e.target.value)}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm border"
                    >
                        <option value="tech">Tech Points</option>
                        <option value="cash">Cash</option>
                        <option value="info">Information</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700">Amount</label>
                    <input
                        type="number"
                        min="1"
                        value={quantity}
                        onChange={(e) => setQuantity(Number(e.target.value))}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 sm:text-sm rounded-md shadow-sm border"
                    />
                </div>
            </div>

            <button
                type="submit"
                disabled={loading}
                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none 
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                {loading ? 'Sending...' : 'Send Trade'}
            </button>
        </form>
    )
}
