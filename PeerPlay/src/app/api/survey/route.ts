import { NextResponse } from 'next/server'
import prisma from '@/lib/prisma'
import { submitPreGameSurvey, submitPostGameFeedback } from '@/modules/survey/actions'

async function resolveSurveyUserId(sessionId: string, providedUserId?: string): Promise<string> {
  const cleanUserId = (providedUserId || '').trim()
  if (cleanUserId) {
    const existingUser = await prisma.user.findUnique({ where: { id: cleanUserId } })
    if (existingUser) return existingUser.id
  }

  // Fallback if userId is missing or invalid: check latest participant in session
  const latestParticipant = await prisma.teamParticipant.findFirst({
    where: { sessionId },
    orderBy: { joinedAt: 'desc' },
  })
  if (latestParticipant) {
    return latestParticipant.userId
  }

  // Last resort: create a mobile participant user for the session's organization
  const session = await prisma.session.findUnique({ where: { id: sessionId } })
  if (!session) {
    throw new Error('A munkamenet nem található.')
  }

  const fallbackEmail = `guest-${Date.now()}@peerplay.local`
  const guestUser = await prisma.user.create({
    data: {
      name: 'Mobil Résztvevő',
      email: fallbackEmail,
      organizationId: session.organizationId,
    },
  })
  return guestUser.id
}

export async function POST(req: Request) {
  const contentType = (req.headers.get('content-type') || '').toLowerCase()
  const isJson = contentType.includes('application/json')

  let phaseType = 'PRE_GAME'
  let sessionId = ''
  let userId = ''

  try {
    if (isJson) {
      const body = await req.json()
      phaseType = String(body.phaseType || 'PRE_GAME').toUpperCase()
      sessionId = String(body.sessionId || '').trim()
      userId = String(body.userId || '').trim()

      if (!sessionId) {
        return NextResponse.json(
          { success: false, error: 'Hiányzó munkamenet azonosító (sessionId).' },
          { status: 400 }
        )
      }

      const resolvedUserId = await resolveSurveyUserId(sessionId, userId)

      if (phaseType === 'POST_GAME') {
        const finalEnergy = Number(body.finalEnergy ?? body.finalEnergyLevel ?? 8)
        const reflectionText = typeof body.reflectionText === 'string' ? body.reflectionText.trim() : ''
        const brokerNominations = Array.isArray(body.brokerNominations)
          ? body.brokerNominations.map(String).filter(Boolean).slice(0, 2)
          : []
        const internalEnablerNominations = Array.isArray(body.internalEnablerNominations)
          ? body.internalEnablerNominations.map(String).filter(Boolean).slice(0, 1)
          : []

        await submitPostGameFeedback(
          sessionId,
          resolvedUserId,
          brokerNominations,
          internalEnablerNominations,
          finalEnergy,
          reflectionText
        )
      } else {
        const energy = Number(body.energy ?? body.initialEnergyLevel ?? 7)
        const engagement = Number(body.engagement ?? body.initialEngagementLevel ?? 8)

        await submitPreGameSurvey(sessionId, resolvedUserId, energy, engagement)
      }

      return NextResponse.json({
        success: true,
        sessionId,
        userId: resolvedUserId,
        phaseType,
      })
    } else {
      const formData = await req.formData()
      phaseType = String(formData.get('phaseType') || 'PRE_GAME').toUpperCase()
      sessionId = String(formData.get('sessionId') || '').trim()
      userId = String(formData.get('userId') || '').trim()

      if (!sessionId) {
        return new Response(null, {
          status: 303,
          headers: { Location: '/join' },
        })
      }

      const resolvedUserId = await resolveSurveyUserId(sessionId, userId)

      if (phaseType === 'POST_GAME') {
        const finalEnergy = Number(formData.get('finalEnergy') ?? formData.get('finalEnergyLevel') ?? 8)
        const reflectionText = String(formData.get('reflectionText') || '').trim()
        const brokerNominations = formData
          .getAll('brokerNominations')
          .map((v) => String(v).trim())
          .filter(Boolean)
          .slice(0, 2)
        const internalEnablerNominations = formData
          .getAll('internalEnablerNominations')
          .map((v) => String(v).trim())
          .filter(Boolean)
          .slice(0, 1)

        await submitPostGameFeedback(
          sessionId,
          resolvedUserId,
          brokerNominations,
          internalEnablerNominations,
          finalEnergy,
          reflectionText
        )
      } else {
        const energy = Number(formData.get('energy') ?? formData.get('initialEnergyLevel') ?? 7)
        const engagement = Number(formData.get('engagement') ?? formData.get('initialEngagementLevel') ?? 8)

        await submitPreGameSurvey(sessionId, resolvedUserId, energy, engagement)
      }

      return new Response(null, {
        status: 303,
        headers: {
          Location: `/survey/${encodeURIComponent(sessionId)}?userId=${encodeURIComponent(resolvedUserId)}`,
        },
      })
    }
  } catch (err: any) {
    console.error('API /api/survey error:', err)
    const errMsg = err.message || 'Hiba a kérdőív mentésekor.'
    if (isJson) {
      return NextResponse.json({ success: false, error: errMsg }, { status: 400 })
    }
    const fallbackUrl = sessionId
      ? `/survey/${encodeURIComponent(sessionId)}${userId ? `?userId=${encodeURIComponent(userId)}` : ''}`
      : '/join'
    return new Response(null, {
      status: 303,
      headers: { Location: fallbackUrl },
    })
  }
}
