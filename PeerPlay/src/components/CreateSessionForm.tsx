'use client'

import { useState } from 'react'
import { createSession } from '@/modules/session/actions'
import { useRouter } from 'next/navigation'

export default function CreateSessionForm({ orgId, scenarioId }: { orgId: string, scenarioId: string }) {
    const [loading, setLoading] = useState(false)
    const router = useRouter()

    const handleCreate = async () => {
        setLoading(true)
        try {
            const session = await createSession(orgId, scenarioId)
            router.push(`/sessions/${session.id}`)
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    return (
        <button
            onClick={handleCreate}
            disabled={loading}
            className={`px-4 py-2 font-semibold text-white bg-indigo-600 rounded-lg shadow-md hover:bg-indigo-700 
        ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
            {loading ? 'Creating...' : '+ New Session'}
        </button>
    )
}
