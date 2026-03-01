'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

import { randomBytes } from 'crypto'

export async function createSession(organizationId: string, scenarioId: string) {
    const joinCode = randomBytes(2).toString('hex').toUpperCase();

    const session = await prisma.session.create({
        data: {
            organizationId,
            scenarioId,
            joinCode,
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

        // --- GLOBAL EXCHANGE TEAM ALLOCATION ---
        // Fetch all participants to allocate them
        const participants = await tx.sessionParticipant.findMany({
            where: { sessionId }
        })

        // Define the 5 team profiles
        const teamProfiles = [
            { type: 'Alpha', name: 'Team Alpha', raw: 3, tech: 5, cap: 800, eff: 1.4 },
            { type: 'Beta', name: 'Team Beta', raw: 15, tech: 1, cap: 200, eff: 0.8 },
            { type: 'Gamma', name: 'Team Gamma', raw: 8, tech: 3, cap: 500, eff: 1.0 },
            { type: 'Delta', name: 'Team Delta', raw: 5, tech: 2, cap: 1200, eff: 1.0 },
            { type: 'Epsilon', name: 'Team Epsilon', raw: 10, tech: 4, cap: 400, eff: 1.2 },
        ]

        // Only create as many teams as needed based on participants (min 1 per team if we have few players, up to 5)
        const numTeamsToCreate = Math.min(participants.length, 5)
        const createdTeams = []

        for (let i = 0; i < numTeamsToCreate; i++) {
            const profile = teamProfiles[i]
            const team = await tx.team.create({
                data: {
                    sessionId,
                    name: profile.name,
                    teamType: profile.type,
                    rawMaterial: profile.raw,
                    techLevel: profile.tech,
                    capital: profile.cap,
                    productionEff: profile.eff
                }
            })
            createdTeams.push(team)
        }

        // Shuffle participants for random allocation
        const shuffled = [...participants].sort(() => 0.5 - Math.random());

        // Assign participants to teams sequentially (Round-robin)
        for (let i = 0; i < shuffled.length; i++) {
            const team = createdTeams[i % createdTeams.length]
            await tx.sessionParticipant.update({
                where: { id: shuffled[i].id },
                data: { teamId: team.id }
            })
        }

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

export async function joinSession(joinCodeParam: string, username: string) {
    const joinCode = joinCodeParam.toUpperCase()
    const session = await prisma.session.findUnique({
        where: { joinCode },
        include: { organization: true }
    })

    if (!session) throw new Error('Session not found by this code')
    if (session.status !== 'draft') throw new Error('Cannot join active or closed session')

    // Find or create user
    let user = await prisma.user.findFirst({
        where: { name: username, organizationId: session.organizationId }
    })

    if (!user) {
        user = await prisma.user.create({
            data: {
                name: username,
                organizationId: session.organizationId,
                role: 'Participant'
            }
        })
    }

    // Upsert participant
    await prisma.sessionParticipant.upsert({
        where: { sessionId_userId: { sessionId: session.id, userId: user.id } },
        create: { sessionId: session.id, userId: user.id },
        update: {}
    })

    return { session, user }
}

export async function getSessionDetails(idOrCode: string) {
    return prisma.session.findFirst({
        where: { OR: [{ id: idOrCode }, { joinCode: idOrCode }] },
        include: {
            organization: true,
            scenario: true,
            participants: {
                include: { user: true, team: true }
            },
            rounds: {
                orderBy: { number: 'desc' },
                take: 1
            },
            teams: true,
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
