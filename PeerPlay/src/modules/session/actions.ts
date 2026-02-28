'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export async function createSession(organizationId: string, scenarioId: string) {
    const session = await prisma.session.create({
        data: {
            organizationId,
            scenarioId,
            status: 'draft',
        },
    })

    revalidatePath('/dashboard')
    return session
}

export async function startSession(sessionId: string) {
    // Check if session has participants
    const session = await prisma.session.findUnique({
        where: { id: sessionId },
        include: { _count: { select: { participants: true } } }
    })

    if (!session) throw new Error('Session not found')
    if (session._count.participants === 0) {
        throw new Error('Cannot start session without participants')
    }

    // Update session to active and create Round 1
    const updatedSession = await prisma.$transaction(async (tx) => {
        const activeSession = await tx.session.update({
            where: { id: sessionId },
            data: { status: 'active' },
        })

        await tx.round.create({
            data: {
                sessionId,
                number: 1,
                state: 'open',
            }
        })

        return activeSession
    })

    revalidatePath(`/sessions/${sessionId}`)
    return updatedSession
}

export async function closeSession(sessionId: string) {
    const session = await prisma.session.update({
        where: { id: sessionId },
        data: { status: 'closed' }
    })

    // Close any open rounds
    await prisma.round.updateMany({
        where: { sessionId, state: 'open' },
        data: { state: 'closed' }
    })

    revalidatePath(`/sessions/${sessionId}`)
    return session
}

export async function joinSession(sessionId: string, userId: string) {
    const session = await prisma.session.findUnique({
        where: { id: sessionId }
    })

    if (!session) throw new Error('Session not found')
    if (session.status !== 'draft') throw new Error('Cannot join active or closed session')

    const participant = await prisma.sessionParticipant.create({
        data: {
            sessionId,
            userId,
        }
    })

    revalidatePath('/join')
    return participant
}

export async function getSessionDetails(sessionId: string) {
    return prisma.session.findUnique({
        where: { id: sessionId },
        include: {
            organization: true,
            scenario: true,
            participants: {
                include: { user: true }
            },
            rounds: {
                orderBy: { number: 'desc' },
                take: 1
            },
            interactions: true,
            surveyResponses: true,
        }
    })
}

export async function getSessions() {
    return prisma.session.findMany({
        orderBy: { createdAt: 'desc' },
        include: {
            organization: true,
            scenario: true,
            _count: {
                select: { participants: true, rounds: true }
            }
        }
    })
}
