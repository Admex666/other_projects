import { NextResponse } from 'next/server'
import {
  executeBatchBankSale,
  submitBankSaleRequest,
  approveBankSaleRequest,
  rejectBankSaleRequest,
} from '@/modules/bank/actions'
import type { ShapeBatchItem, ShapeType } from '@/modules/bank/constants'

export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  const contentType = (req.headers.get('content-type') || '').toLowerCase()
  const isJson = contentType.includes('application/json')

  let action = ''
  let sessionId = ''
  let teamId = ''
  let userId = ''
  let userName = ''
  let qualityNotes = ''
  let batchIdOrSaleId = ''
  let deliveredByName = ''
  let deliveredByUserId = ''
  let items: ShapeBatchItem[] = []

  try {
    if (isJson) {
      const body = await req.json()
      action = String(body.action || '').trim()
      sessionId = String(body.sessionId || '').trim()
      teamId = String(body.teamId || '').trim()
      userId = String(body.userId || '').trim()
      userName = String(body.userName || '').trim()
      qualityNotes = typeof body.qualityNotes === 'string' ? body.qualityNotes.trim() : ''
      batchIdOrSaleId = String(body.batchId || body.saleId || body.batchIdOrSaleId || '').trim()
      deliveredByName = String(body.deliveredByName || body.submittedByName || body.userName || '').trim()
      deliveredByUserId = String(body.deliveredByUserId || body.submittedByUserId || body.userId || '').trim()

      if (Array.isArray(body.items)) {
        items = body.items
          .map((it: any) => ({
            shapeType: String(it.shapeType) as ShapeType,
            quantity: Number(it.quantity || 0),
          }))
          .filter((it: ShapeBatchItem) => it.quantity > 0)
      }
    } else {
      const formData = await req.formData()
      action = String(formData.get('action') || '').trim()
      sessionId = String(formData.get('sessionId') || '').trim()
      teamId = String(formData.get('teamId') || '').trim()
      userId = String(formData.get('userId') || '').trim()
      userName = String(formData.get('userName') || '').trim()
      qualityNotes = String(formData.get('qualityNotes') || '').trim()
      batchIdOrSaleId = String(formData.get('batchId') || formData.get('saleId') || formData.get('batchIdOrSaleId') || '').trim()
      deliveredByName = String(formData.get('deliveredByName') || formData.get('submittedByName') || formData.get('userName') || '').trim()
      deliveredByUserId = String(formData.get('deliveredByUserId') || formData.get('submittedByUserId') || formData.get('userId') || '').trim()

      const shapes: ShapeType[] = ['SQUARE', 'TRIANGLE', 'CIRCLE', 'RECTANGLE', 'PREMIUM_PACK']
      for (const s of shapes) {
        const qty = Number(formData.get(`qty_${s}`) || 0)
        if (qty > 0) {
          items.push({ shapeType: s, quantity: qty })
        }
      }
    }

    if (!sessionId) {
      throw new Error('Hiányzó munkamenet azonosító.')
    }

    let result: any = null

    // 1. Facilitátori jóváhagyás
    if (action === 'approve') {
      if (!batchIdOrSaleId) {
        throw new Error('Hiányzó tétel vagy köteg azonosító a jóváhagyáshoz.')
      }
      result = await approveBankSaleRequest(sessionId, batchIdOrSaleId, qualityNotes || undefined)
    }
    // 2. Facilitátori elutasítás
    else if (action === 'reject') {
      if (!batchIdOrSaleId) {
        throw new Error('Hiányzó tétel vagy köteg azonosító az elutasításhoz.')
      }
      result = await rejectBankSaleRequest(sessionId, batchIdOrSaleId, qualityNotes || undefined)
    }
    // 3. Játékos eladási igény leadása (Kétlépcsős: PENDING)
    else if (action === 'request' || action === 'submit_request') {
      if (!teamId) {
        throw new Error('Hiányzó csapat azonosító.')
      }
      if (items.length === 0) {
        throw new Error('Legalább egy terméket és darabszámot meg kell adni az igényhez!')
      }
      result = await submitBankSaleRequest(
        sessionId,
        teamId,
        items,
        deliveredByUserId || userId || undefined,
        deliveredByName || userName || undefined,
        qualityNotes || undefined
      )
    }
    // 4. Manuális azonnali átvétel a Facilitátori Pultról
    else {
      if (!teamId) {
        throw new Error('Hiányzó csapat azonosító.')
      }
      if (items.length === 0) {
        throw new Error('Legalább egy terméket és darabszámot meg kell adni az eladáshoz!')
      }
      result = await executeBatchBankSale(
        sessionId,
        teamId,
        items,
        qualityNotes || undefined,
        deliveredByName || undefined,
        deliveredByUserId || undefined
      )
    }

    if (isJson) {
      return NextResponse.json({
        success: true,
        ...result,
      })
    }

    const redirectUrl = userId
      ? `/survey/${encodeURIComponent(sessionId)}?userId=${encodeURIComponent(userId)}`
      : `/sessions/${encodeURIComponent(sessionId)}`

    return new Response(null, {
      status: 303,
      headers: { Location: redirectUrl },
    })
  } catch (err: any) {
    console.error('POST /api/bank error:', err)
    const errMsg = err.message || 'Hiba a banki eladás rögzítésekor.'
    if (isJson) {
      return NextResponse.json({ success: false, error: errMsg }, { status: 400 })
    }
    const redirectUrl = sessionId
      ? userId
        ? `/survey/${encodeURIComponent(sessionId)}?userId=${encodeURIComponent(userId)}`
        : `/sessions/${encodeURIComponent(sessionId)}`
      : '/dashboard'
    return new Response(null, {
      status: 303,
      headers: { Location: redirectUrl },
    })
  }
}
