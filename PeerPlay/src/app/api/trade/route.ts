import { NextResponse } from 'next/server'
import prisma from '@/lib/prisma'
import {
  createTradeOffer,
  acceptTradeOffer,
  rejectTradeOffer,
  cancelTradeOffer,
} from '@/modules/trade/actions'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  const contentType = (req.headers.get('content-type') || '').toLowerCase()
  const isJson = contentType.includes('application/json')

  let action = 'create'
  let sessionId = ''
  let userId = ''
  let userName = ''
  let createdByName = ''
  let createdByUserId = ''
  let acceptedByName = ''
  let acceptedByUserId = ''
  let senderTeamId = ''
  let receiverTeamId = ''
  let tradeId = ''
  let notes = ''
  let offered = {
    cash: 0,
    paperSheets: 0,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
  }
  let requested = {
    cash: 0,
    paperSheets: 0,
    scissorsCount: 0,
    rulersCount: 0,
    templatesCount: 0,
  }

  try {
    if (isJson) {
      const body = await req.json()
      action = String(body.action || 'create')
      sessionId = String(body.sessionId || '').trim()
      userId = String(body.userId || '').trim()
      userName = String(body.userName || '').trim()
      createdByName = String(body.createdByName || body.userName || '').trim()
      createdByUserId = String(body.createdByUserId || body.userId || '').trim()
      acceptedByName = String(body.acceptedByName || body.userName || '').trim()
      acceptedByUserId = String(body.acceptedByUserId || body.userId || '').trim()
      senderTeamId = String(body.senderTeamId || body.teamId || '').trim()
      receiverTeamId = String(body.receiverTeamId || body.targetTeamId || '').trim()
      tradeId = String(body.tradeId || '').trim()
      notes = typeof body.notes === 'string' ? body.notes.trim() : ''
      if (body.offered) {
        offered = {
          cash: Number(body.offered.cash || 0),
          paperSheets: Number(body.offered.paperSheets || 0),
          scissorsCount: Number(body.offered.scissorsCount || 0),
          rulersCount: Number(body.offered.rulersCount || 0),
          templatesCount: Number(body.offered.templatesCount || 0),
        }
      }
      if (body.requested) {
        requested = {
          cash: Number(body.requested.cash || 0),
          paperSheets: Number(body.requested.paperSheets || 0),
          scissorsCount: Number(body.requested.scissorsCount || 0),
          rulersCount: Number(body.requested.rulersCount || 0),
          templatesCount: Number(body.requested.templatesCount || 0),
        }
      }
    } else {
      const formData = await req.formData()
      action = String(formData.get('action') || 'create')
      sessionId = String(formData.get('sessionId') || '').trim()
      userId = String(formData.get('userId') || '').trim()
      userName = String(formData.get('userName') || '').trim()
      createdByName = String(formData.get('createdByName') || formData.get('userName') || '').trim()
      createdByUserId = String(formData.get('createdByUserId') || formData.get('userId') || '').trim()
      acceptedByName = String(formData.get('acceptedByName') || formData.get('userName') || '').trim()
      acceptedByUserId = String(formData.get('acceptedByUserId') || formData.get('userId') || '').trim()
      senderTeamId = String(formData.get('senderTeamId') || formData.get('teamId') || '').trim()
      receiverTeamId = String(formData.get('receiverTeamId') || formData.get('targetTeamId') || '').trim()
      tradeId = String(formData.get('tradeId') || '').trim()
      notes = String(formData.get('notes') || '').trim()
      offered = {
        cash: Number(formData.get('offeredCash') || 0),
        paperSheets: Number(formData.get('offeredPaper') || 0),
        scissorsCount: Number(formData.get('offeredScissors') || 0),
        rulersCount: Number(formData.get('offeredRulers') || 0),
        templatesCount: Number(formData.get('offeredTemplates') || 0),
      }
      requested = {
        cash: Number(formData.get('requestedCash') || 0),
        paperSheets: Number(formData.get('requestedPaper') || 0),
        scissorsCount: Number(formData.get('requestedScissors') || 0),
        rulersCount: Number(formData.get('requestedRulers') || 0),
        templatesCount: Number(formData.get('requestedTemplates') || 0),
      }
    }

    if (!sessionId) {
      throw new Error('Hiányzó munkamenet azonosító.')
    }

    let result: any = null

    if (action === 'create') {
      result = await createTradeOffer(
        sessionId,
        senderTeamId,
        receiverTeamId,
        offered,
        requested,
        notes,
        createdByName || undefined,
        createdByUserId || undefined
      )
    } else if (action === 'accept') {
      result = await acceptTradeOffer(
        sessionId,
        tradeId,
        receiverTeamId || senderTeamId,
        acceptedByName || undefined,
        acceptedByUserId || undefined
      )
    } else if (action === 'reject') {
      result = await rejectTradeOffer(sessionId, tradeId, receiverTeamId || senderTeamId)
    } else if (action === 'cancel') {
      result = await cancelTradeOffer(sessionId, tradeId, senderTeamId)
    } else {
      throw new Error(`Ismeretlen kereskedelmi művelet: ${action}`)
    }

    if (isJson) {
      return NextResponse.json({ success: true, trade: result })
    }

    const redirectUrl = userId
      ? `/survey/${encodeURIComponent(sessionId)}?userId=${encodeURIComponent(userId)}`
      : `/play/${encodeURIComponent(sessionId)}`

    return new Response(null, {
      status: 303,
      headers: { Location: redirectUrl },
    })
  } catch (err: any) {
    console.error('POST /api/trade error:', err)
    const errMsg = err.message || 'Hiba a kereskedelmi művelet során.'
    if (isJson) {
      return NextResponse.json({ success: false, error: errMsg }, { status: 400 })
    }
    const redirectUrl = sessionId
      ? userId
        ? `/survey/${encodeURIComponent(sessionId)}?userId=${encodeURIComponent(userId)}`
        : `/play/${encodeURIComponent(sessionId)}`
      : '/join'
    return new Response(null, {
      status: 303,
      headers: { Location: redirectUrl },
    })
  }
}
