'use client'

import { useState } from 'react'
import { submitSurvey } from '@/modules/survey/actions'
import { User } from '@prisma/client'

export default function SurveyForm({
    sessionId,
    currentUserId,
    otherParticipants
}: {
    sessionId: string,
    currentUserId: string,
    otherParticipants: User[]
}) {
    // Store answers as: targetUserId -> rating (1-5)
    const [answers, setAnswers] = useState<Record<string, number>>({})
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleRating = (targetId: string, rating: number) => {
        setAnswers(prev => ({ ...prev, [targetId]: rating }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        // Validate all answered
        if (Object.keys(answers).length !== otherParticipants.length) {
            setError('Please rate all participants before submitting.')
            return
        }

        setLoading(true)
        setError(null)

        const payload = Object.entries(answers).map(([targetUserId, answer]) => ({
            questionId: 'q_influence_1', // MVP hardcoded question ID
            targetUserId,
            answer
        }))

        try {
            await submitSurvey(sessionId, currentUserId, payload)
            setSuccess(true)
        } catch (err: any) {
            setError(err.message || 'Failed to submit survey')
        } finally {
            setLoading(false)
        }
    }

    if (success) {
        return (
            <div className="text-center p-8">
                <h2 className="text-2xl font-bold text-green-600 mb-2">Thank You!</h2>
                <p className="text-gray-600">Your feedback has been recorded safely.</p>
                <p className="text-sm mt-4 text-gray-500">You may now close this window.</p>
            </div>
        )
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-8">
            {error && <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>}

            <div className="space-y-6">
                {otherParticipants.map((user) => (
                    <div key={user.id} className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                        <h4 className="font-semibold text-gray-900 mb-3">{user.name} ({user.role})</h4>
                        <div className="flex items-center space-x-4">
                            <span className="text-sm text-gray-500">Not at all</span>
                            {[1, 2, 3, 4, 5].map((val) => (
                                <label key={val} className="flex flex-col items-center cursor-pointer">
                                    <input
                                        type="radio"
                                        name={`rating_${user.id}`}
                                        value={val}
                                        checked={answers[user.id] === val}
                                        onChange={() => handleRating(user.id, val)}
                                        className="w-5 h-5 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                                    />
                                    <span className="text-xs mt-1 text-gray-400">{val}</span>
                                </label>
                            ))}
                            <span className="text-sm text-gray-500">Significantly</span>
                        </div>
                    </div>
                ))}
            </div>

            <button
                type="submit"
                disabled={loading}
                className={`w-full py-3 px-4 shadow-md bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                {loading ? 'Submitting...' : 'Submit Survey'}
            </button>
        </form>
    )
}
