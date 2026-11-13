'use server'

import prisma from '@/lib/prisma'
import { safeRevalidatePath } from '@/lib/safeRevalidate'
import { randomBytes } from 'crypto'
import { TEAM_ARCHETYPES } from './teamProfiles'
import { autoRefundOnPhaseEnd } from '@/modules/trade/actions'
import { WORKSHOP_PHASES, PHASE_DEFAULT_DURATIONS } from './constants'
import type { WorkshopPhase } from './constants'



/**
 * 1. Workshop Session létrehozása a megadott szervezethez
 */
export async function createWorkshopSession(
  orgId?: string,
  joinCode?: string,
  sessionName?: string
) {
  let organizationId = orgId

  if (!organizationId) {
    let defaultOrg = await prisma.organization.findFirst()
    if (!defaultOrg) {
      defaultOrg = await prisma.organization.create({
        data: {
          name: 'Demo Vállalat',
          industry: 'Enterprise Tech',
        },
      })
    }
    organizationId = defaultOrg.id
  }

  const finalJoinCode = (joinCode || randomBytes(2).toString('hex')).toUpperCase()

  const session = await prisma.session.create({
    data: {
      organizationId,
      name: sessionName || 'The Trading Game Workshop',
      joinCode: finalJoinCode,
      status: 'DRAFT',
      currentPhase: 'PHASE_0_SETUP',
      phaseStartedAt: new Date(),
      phaseDurationSeconds: PHASE_DEFAULT_DURATIONS.PHASE_0_SETUP,
      isTimerPaused: false,
      timerRemainingSeconds: PHASE_DEFAULT_DURATIONS.PHASE_0_SETUP,
    },
  })

  // Automatikusan inicializáljuk a 4 aszimmetrikus csapatot
  await initializeTeamArchetypes(session.id)

  safeRevalidatePath('/dashboard')
  safeRevalidatePath('/sessions')
  return session
}

/**
 * 2. Aszimmetrikus csapatok inicializálása (Capital, Resource, Tech, Emerging)
 */
export async function initializeTeamArchetypes(sessionId: string) {
  const createdTeams = await prisma.$transaction(async (tx) => {
    const teams = []
    for (const archetype of TEAM_ARCHETYPES) {
      const team = await tx.sessionTeam.upsert({
        where: {
          sessionId_name: {
            sessionId,
            name: archetype.name,
          },
        },
        create: {
          sessionId,
          name: archetype.name,
          profileCode: archetype.profileCode,
          cashBalance: archetype.cashBalance,
          paperSheets: archetype.paperSheets,
          scissorsCount: archetype.scissorsCount,
          rulersCount: archetype.rulersCount,
          templatesCount: archetype.templatesCount,
        },
        update: {
          profileCode: archetype.profileCode,
          cashBalance: archetype.cashBalance,
          paperSheets: archetype.paperSheets,
          scissorsCount: archetype.scissorsCount,
          rulersCount: archetype.rulersCount,
          templatesCount: archetype.templatesCount,
        },
      })
      teams.push(team)
    }
    return teams
  })

  safeRevalidatePath(`/sessions/${sessionId}`)
  safeRevalidatePath(`/play/${sessionId}`)
  return createdTeams
}

/**
 * 3. Fázis léptetése a 11 fázisú állapotgép mentén
 * Kereskedési kör zárásakor automatikus Escrow refund fut!
 */
export async function advanceSessionPhase(sessionId: string, nextPhase: string) {
  const session = await prisma.session.findUnique({
    where: { id: sessionId },
  })

  if (!session) {
    throw new Error('A keresett szimulációs munkamenet nem található.')
  }

  // Ha aktív kereskedési körből lépünk ki, visszatérítjük az összes nyitott ajánlatot
  const tradingPhases = ['PHASE_4_ROUND_1', 'PHASE_6_ROUND_2', 'PHASE_8_ROUND_3']
  if (tradingPhases.includes(session.currentPhase)) {
    await autoRefundOnPhaseEnd(sessionId)
  }

  const duration =
    PHASE_DEFAULT_DURATIONS[nextPhase as WorkshopPhase] ?? 300

  const nextStatus =
    nextPhase === 'PHASE_11_DEBRIEF'
      ? 'COMPLETED'
      : session.status === 'DRAFT'
      ? 'ACTIVE'
      : session.status

  const updatedSession = await prisma.session.update({
    where: { id: sessionId },
    data: {
      currentPhase: nextPhase,
      status: nextStatus,
      phaseStartedAt: new Date(),
      phaseDurationSeconds: duration,
      isTimerPaused: false,
      timerRemainingSeconds: duration,
      closedAt: nextPhase === 'PHASE_11_DEBRIEF' ? new Date() : undefined,
    },
  })

  safeRevalidatePath(`/sessions/${sessionId}`)
  safeRevalidatePath(`/play/${sessionId}`)
  return updatedSession
}

/**
 * 4. Időzítő módosítása (+2 perc hozzáadása vagy szüneteltetés/újraindítás)
 */
export async function adjustPhaseTimer(
  sessionId: string,
  additionalSeconds: number = 0,
  isPaused?: boolean
) {
  const session = await prisma.session.findUnique({
    where: { id: sessionId },
  })

  if (!session) {
    throw new Error('A munkamenet nem található.')
  }

  const now = Date.now()

  let newIsPaused = session.isTimerPaused
  let newDuration = session.phaseDurationSeconds
  let newRemaining = session.timerRemainingSeconds
  let newStartedAt = session.phaseStartedAt

  // 1. Szünet / Folytatás kezelése
  if (typeof isPaused === 'boolean') {
    if (isPaused && !session.isTimerPaused) {
      // Szüneteltetés: kiszámoljuk a hátralévő másodperceket és elmentjük
      const elapsedMs = now - new Date(session.phaseStartedAt).getTime()
      const elapsedSec = Math.floor(elapsedMs / 1000)
      newRemaining = Math.max(0, session.phaseDurationSeconds - elapsedSec)
      newIsPaused = true
    } else if (!isPaused && session.isTimerPaused) {
      // Újraindítás: a hátralévő idő lesz az új időtartam
      newIsPaused = false
      newStartedAt = new Date()
      newDuration = session.timerRemainingSeconds
    }
  }

  // 2. További másodpercek hozzáadása (+120s stb.)
  if (additionalSeconds !== 0) {
    if (newIsPaused) {
      newRemaining = Math.max(0, newRemaining + additionalSeconds)
      newDuration = Math.max(0, newDuration + additionalSeconds)
    } else {
      newDuration = Math.max(0, newDuration + additionalSeconds)
    }
  }

  const updated = await prisma.session.update({
    where: { id: sessionId },
    data: {
      isTimerPaused: newIsPaused,
      phaseDurationSeconds: newDuration,
      timerRemainingSeconds: newRemaining,
      phaseStartedAt: newStartedAt,
    },
  })

  safeRevalidatePath(`/sessions/${sessionId}`)
  safeRevalidatePath(`/play/${sessionId}`)
  return updated
}

/**
 * 5. Résztvevő csatlakozása csapathoz (mobil vagy játékos nézet)
 */
export async function joinWorkshopSession(
  joinCode: string,
  userName: string,
  userEmail: string,
  teamId?: string
) {
  const session = await prisma.session.findUnique({
    where: { joinCode: joinCode.toUpperCase() },
    include: { teams: true },
  })

  if (!session) {
    throw new Error('Érvénytelen workshop kód!')
  }

  let user = await prisma.user.findUnique({
    where: { email: userEmail },
  })

  if (!user) {
    user = await prisma.user.create({
      data: {
        email: userEmail,
        name: userName,
        organizationId: session.organizationId,
      },
    })
  }

  // Csapat kiválasztása vagy hozzárendelés
  let targetTeamId = teamId
  if (!targetTeamId) {
    if (session.teams.length === 0) {
      const initialized = await initializeTeamArchetypes(session.id)
      targetTeamId = initialized[0].id
    } else {
      // Legkisebb létszámú csapathoz rendelés
      const teamCounts = await prisma.teamParticipant.groupBy({
        by: ['teamId'],
        where: { sessionId: session.id },
        _count: { userId: true },
      })
      const countMap = new Map<string, number>(teamCounts.map((tc) => [tc.teamId, tc._count.userId]))
      const sortedTeams = [...session.teams].sort(
        (a, b) => Number(countMap.get(a.id) || 0) - Number(countMap.get(b.id) || 0)
      )
      targetTeamId = sortedTeams[0].id
    }
  }

  const participant = await prisma.teamParticipant.upsert({
    where: {
      sessionId_userId: {
        sessionId: session.id,
        userId: user.id,
      },
    },
    create: {
      sessionId: session.id,
      userId: user.id,
      teamId: targetTeamId,
    },
    update: {
      teamId: targetTeamId,
    },
  })

  return { session, user, participant }
}

/**
 * 6. Session részletes adatainak lekérése (ID vagy Join Code alapján)
 */
export async function getSessionDetails(idOrCode: string) {
  const includeQuery = {
    organization: true,
    teams: {
      include: {
        participants: {
          include: {
            user: true,
          },
        },
      },
    },
    tradeTransactions: {
      orderBy: { createdAt: 'desc' as const },
    },
    bankSales: {
      orderBy: { soldAt: 'desc' as const },
    },
    marketEvents: {
      orderBy: { triggeredAt: 'desc' as const },
    },
    surveyResponses: true,
  }

  let session = await prisma.session.findUnique({
    where: { id: idOrCode },
    include: includeQuery,
  })

  if (!session) {
    session = await prisma.session.findUnique({
      where: { joinCode: idOrCode.toUpperCase() },
      include: includeQuery,
    })
  }

  return session
}

/**
 * 7. Összes session listázása a dashboard számára
 */
export async function getSessions() {
  return await prisma.session.findMany({
    orderBy: { createdAt: 'desc' },
    include: {
      organization: true,
      teams: true,
      _count: {
        select: {
          teams: true,
          tradeTransactions: true,
          bankSales: true,
          surveyResponses: true,
        },
      },
    },
  })
}

// Backward-compatible aliases
export const createSession = createWorkshopSession
export const joinSession = joinWorkshopSession


