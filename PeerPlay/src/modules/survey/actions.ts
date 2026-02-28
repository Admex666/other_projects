'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export async function submitSurvey(
    sessionId: string,
    userId: string,
    responses: { questionId: string; targetUserId: string | null; answer: number }[]
) {
    // Check session
    const session = await prisma.session.findUnique({
        where: { id: sessionId }
    })

    // We only allow surveys in closed sessions 
    // (In MVP, closing session moves users to survey)
    if (!session || session.status !== 'closed') {
        throw new Error('Survey can only be submitted for closed sessions')
    }

    // Save all responses
    const data = responses.map(r => ({
        sessionId,
        userId,
        questionId: r.questionId,
        targetUserId: r.targetUserId,
        answer: r.answer
    }))

    await prisma.surveyResponse.createMany({
        data
    })

    revalidatePath(`/survey/${sessionId}`)
    revalidatePath(`/sessions/${sessionId}`)

    return true
}

export async function hasCompletedSurvey(sessionId: string, userId: string) {
    const count = await prisma.surveyResponse.count({
        where: { sessionId, userId }
    })
    return count > 0
}
