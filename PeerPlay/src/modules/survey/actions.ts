'use server'

import prisma from '@/lib/prisma'
import { safeRevalidatePath } from '@/lib/safeRevalidate'
import { randomUUID } from 'crypto'

export interface PreGameSurveyInput {
  initialEnergyLevel: number // 1 - 10
  initialEngagementLevel: number // 1 - 10
}

export interface PostGameFeedbackInput {
  brokerNominations: string[] // User IDs of brokers (from other teams)
  internalEnablerNominations: string[] // User IDs of enablers (from own team)
  finalEnergyLevel: number // 1 - 10
  reflectionText?: string
}

export interface OnaConnectionInput {
  targetUserId: string
  relationType: 'ADVICE' | 'INFORMATION' | 'COLLABORATION' | 'TRUST' | string
  frequency?: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'RARELY' | string
  frequencyScore?: number // 1 - 5
}

/**
 * 1. Pre-Game Kérdőív Beküldése (Fázis 1 · 1-10 skála)
 */
export async function submitPreGameSurvey(
  sessionId: string,
  userId: string,
  initialEnergyLevel: number,
  initialEngagementLevel: number
) {
  if (initialEnergyLevel < 1 || initialEnergyLevel > 10) {
    throw new Error('A kezdeti energiaszintnek 1 és 10 között kell lennie.')
  }
  if (initialEngagementLevel < 1 || initialEngagementLevel > 10) {
    throw new Error('A részvételi kedvnek 1 és 10 között kell lennie.')
  }

  const payloadJson = JSON.stringify({
    initialEnergyLevel,
    initialEngagementLevel,
  })

  const response = await prisma.surveyResponse.upsert({
    where: {
      sessionId_userId_phaseType: {
        sessionId,
        userId,
        phaseType: 'PRE_GAME',
      },
    },
    create: {
      sessionId,
      userId,
      phaseType: 'PRE_GAME',
      payloadJson,
      submittedAt: new Date(),
    },
    update: {
      payloadJson,
      submittedAt: new Date(),
    },
  })

  safeRevalidatePath(`/survey/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return response
}

/**
 * 2. Post-Game Peer Feedback & Reflexió Beküldése (Fázis 10)
 */
export async function submitPostGameFeedback(
  sessionId: string,
  userId: string,
  brokerNominations: string[],
  internalEnablerNominations: string[],
  finalEnergyLevel: number,
  reflectionText?: string
) {
  if (finalEnergyLevel < 1 || finalEnergyLevel > 10) {
    throw new Error('A záró energiaszintnek 1 és 10 között kell lennie.')
  }

  const payloadJson = JSON.stringify({
    brokerNominations: brokerNominations || [],
    internalEnablerNominations: internalEnablerNominations || [],
    finalEnergyLevel,
    reflectionText: reflectionText || '',
  })

  const response = await prisma.surveyResponse.upsert({
    where: {
      sessionId_userId_phaseType: {
        sessionId,
        userId,
        phaseType: 'POST_GAME',
      },
    },
    create: {
      sessionId,
      userId,
      phaseType: 'POST_GAME',
      payloadJson,
      submittedAt: new Date(),
    },
    update: {
      payloadJson,
      submittedAt: new Date(),
    },
  })

  safeRevalidatePath(`/survey/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return response
}

/**
 * 3. Workshop Utáni Munkahelyi ONA Kitöltése (Aszinkron, Token-alapú)
 */
export async function submitWorkplaceOna(
  invitationToken: string,
  respondentUserId: string,
  connections: OnaConnectionInput[]
) {
  return await prisma.$transaction(async (tx) => {
    const invitation = await tx.onaInvitation.findUnique({
      where: { uniqueToken: invitationToken },
    })

    if (!invitation) {
      throw new Error('Érvénytelen ONA meghívó link vagy token.')
    }
    if (invitation.isCompleted) {
      throw new Error('Ez a kérdőív már korábban kitöltésre került.')
    }
    if (new Date() > new Date(invitation.expiresAt)) {
      throw new Error('A kérdőív kitöltési határideje lejárt.')
    }
    if (invitation.userId !== respondentUserId) {
      throw new Error('A megadott felhasználó nem egyezik a meghívó jogosultjával.')
    }

    // Korábbi válaszok törlése az újrarögzítés előtt (idempotens biztonság)
    await tx.onaResponse.deleteMany({
      where: { invitationId: invitation.id },
    })

    const frequencyMap: Record<string, number> = {
      DAILY: 5,
      WEEKLY: 4,
      MONTHLY: 3,
      RARELY: 1,
    }

    for (const conn of connections) {
      let score = conn.frequencyScore
      if (score === undefined || score === null) {
        score = (conn.frequency && frequencyMap[conn.frequency.toUpperCase()]) || 2
      }
      // Korlátok: 1 és 5 között
      score = Math.max(1, Math.min(5, Math.round(score)))

      await tx.onaResponse.create({
        data: {
          invitationId: invitation.id,
          targetUserId: conn.targetUserId,
          relationType: conn.relationType || 'COLLABORATION',
          frequencyScore: score,
        },
      })
    }

    const updatedInvitation = await tx.onaInvitation.update({
      where: { id: invitation.id },
      data: {
        isCompleted: true,
        completedAt: new Date(),
      },
    })

    return { success: true, invitation: updatedInvitation, connectionsCount: connections.length }
  })
}

/**
 * 4. ONA Meghívó Generálása Felhasználónak
 */
export async function createOnaInvitation(
  sessionId: string,
  userId: string,
  daysValid: number = 14
) {
  const expiresAt = new Date()
  expiresAt.setDate(expiresAt.getDate() + daysValid)

  const token = randomUUID()

    return await prisma.onaInvitation.create({
      data: {
        sessionId,
        userId,
        uniqueToken: token,
        expiresAt,
        isCompleted: false,
      },
    })
  }

/**
 * 5. Ellenőrzi, hogy a felhasználó beküldte-e már az adott fázis kérdőívét
 */
export async function hasCompletedSurvey(
  sessionId: string,
  userId: string,
  phaseType: 'PRE_GAME' | 'POST_GAME' = 'PRE_GAME'
) {
  const existing = await prisma.surveyResponse.findUnique({
    where: {
      sessionId_userId_phaseType: {
        sessionId,
        userId,
        phaseType,
      },
    },
  })
  return !!existing
}
