'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'
import { randomBytes } from 'crypto'
import { TEAM_PROFILES } from './teamProfiles'

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
        // Check if teams have already been manually created
        const existingTeams = await tx.team.findMany({ where: { sessionId } })

        // Define the 5 farm profiles
        const teamProfiles = [
            { type: 'Alpha', name: 'Farm Alpha', raw: 3, tech: 5, cap: 800, eff: 1.4 },
            { type: 'Beta', name: 'Farm Beta', raw: 15, tech: 1, cap: 200, eff: 0.8 },
            { type: 'Gamma', name: 'Farm Gamma', raw: 8, tech: 3, cap: 500, eff: 1.0 },
            { type: 'Delta', name: 'Farm Delta', raw: 5, tech: 2, cap: 1200, eff: 1.0 },
            { type: 'Epsilon', name: 'Farm Epsilon', raw: 10, tech: 4, cap: 400, eff: 1.2 },
        ]

        // Map team type -> profile for quick lookup
        const profileByType: Record<string, typeof teamProfiles[0]> = {}
        teamProfiles.forEach(p => { profileByType[p.type] = p })

        let teamMap: Record<string, { team: { id: string; teamType: string }, profile: typeof teamProfiles[0] }> = {}

        if (existingTeams.length === 0) {
            // No manual assignment yet: create teams and round-robin
            const participants = await tx.sessionParticipant.findMany({ where: { sessionId } })
            const createdTeams: typeof teamMap[string][] = []

            for (let i = 0; i < Math.min(participants.length, 5); i++) {
                const profile = teamProfiles[i]
                const team = await tx.team.create({ data: { sessionId, name: profile.name, teamType: profile.type } })
                createdTeams.push({ team, profile })
                teamMap[team.id] = { team, profile }
            }

            const shuffled = [...participants].sort(() => 0.5 - Math.random())
            for (let i = 0; i < shuffled.length; i++) {
                const assignment = createdTeams[i % createdTeams.length]
                await tx.sessionParticipant.update({
                    where: { id: shuffled[i].id },
                    data: { teamId: assignment.team.id, capital: assignment.profile.cap, rawMaterial: assignment.profile.raw, techLevel: assignment.profile.tech, productionEff: assignment.profile.eff, inventory: "{}" }
                })
            }
        } else {
            // Manual assignment: just initialize resources for each participant based on their team
            existingTeams.forEach(t => {
                const profile = profileByType[t.teamType]
                if (profile) teamMap[t.id] = { team: t, profile }
            })

            const participants = await tx.sessionParticipant.findMany({ where: { sessionId } })
            for (const p of participants) {
                const assignment = p.teamId ? teamMap[p.teamId] : null
                if (assignment) {
                    await tx.sessionParticipant.update({
                        where: { id: p.id },
                        data: { capital: assignment.profile.cap, rawMaterial: assignment.profile.raw, techLevel: assignment.profile.tech, productionEff: assignment.profile.eff, inventory: "{}" }
                    })
                }
            }
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


/** Creates the 5 fixed farm team slots for a session (HR step before start) */
export async function createTeamsForSession(sessionId: string) {
    const existing = await prisma.team.count({ where: { sessionId } })
    if (existing > 0) return

    for (const p of TEAM_PROFILES) {
        await prisma.team.create({
            data: { sessionId, name: p.name, teamType: p.type }
        })
    }
    revalidatePath(`/sessions/${sessionId}`)
}

/** HR manually assigns a participant to a specific team */
export async function assignParticipantToTeam(participantId: string, teamId: string | null, sessionId: string) {
    await prisma.sessionParticipant.update({
        where: { id: participantId },
        data: { teamId }
    })
    revalidatePath(`/sessions/${sessionId}`)
}
