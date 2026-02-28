'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export async function logTrade(
    sessionId: string,
    fromUserId: string,
    toUserId: string,
    resourceType: string,
    quantity: number
) {
    // 1. Get Session and active Round
    const session = await prisma.session.findUnique({
        where: { id: sessionId },
        include: {
            rounds: {
                where: { state: 'open' },
                take: 1
            }
        }
    })

    if (!session) throw new Error('Session not found')
    if (session.status !== 'active') throw new Error('Session is not active')
    if (session.rounds.length === 0) throw new Error('No open round found')

    const activeRound = session.rounds[0]

    // 2. Log interaction
    const interaction = await prisma.interaction.create({
        data: {
            sessionId,
            roundId: activeRound.id,
            fromUserId,
            toUserId,
            type: 'trade',
            resourceType,
            quantity
        }
    })

    // 3. Revalidate paths that might show interaction counts
    revalidatePath(`/sessions/${sessionId}`)
    revalidatePath(`/rounds/${sessionId}`) // Player's round view

    return interaction
}
