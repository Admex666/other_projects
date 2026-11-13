'use server'

import prisma from '@/lib/prisma'
import { safeRevalidatePath } from '@/lib/safeRevalidate'
import { BASE_PRICES } from './constants'
import type { ShapeType, ShapeBatchItem } from './constants'

/**
 * 1. Egyedi termékátvétel és banki kifizetés
 */
export async function executeBankSale(
  sessionId: string,
  teamId: string,
  shapeType: ShapeType,
  quantity: number,
  qualityApproved: boolean,
  notes?: string
) {
  if (quantity <= 0) {
    throw new Error('A mennyiségnek legalább 1-nek kell lennie.')
  }
  if (!qualityApproved) {
    throw new Error('A termék minőségileg elutasításra került. Nem történik kifizetés.')
  }

  const result = await prisma.$transaction(async (tx) => {
    const session = await tx.session.findUnique({
      where: { id: sessionId },
      include: {
        marketEvents: {
          where: { isActive: true },
          orderBy: { triggeredAt: 'desc' },
          take: 1,
        },
      },
    })

    if (!session) {
      throw new Error('A szimulációs munkamenet nem található.')
    }

    let multiplier = 1.0
    if (session.marketEvents.length > 0) {
      const activeEvent = session.marketEvents[0]
      try {
        const modifiers: Record<string, number> = JSON.parse(activeEvent.priceMultipliers || '{}')
        if (typeof modifiers[shapeType] === 'number') {
          multiplier = modifiers[shapeType]
        }
      } catch (err) {
        console.warn('Hiba a piaci szorzók parszolásakor:', err)
      }
    }

    const unitBasePrice = BASE_PRICES[shapeType] || 0
    const finalUnitPrice = Math.round(unitBasePrice * multiplier)
    const totalPayout = finalUnitPrice * quantity

    const updatedTeam = await tx.sessionTeam.update({
      where: { id: teamId },
      data: {
        cashBalance: { increment: totalPayout },
      },
    })

    const saleRecord = await tx.bankSale.create({
      data: {
        sessionId,
        teamId,
        shapeType,
        quantity,
        unitBasePrice,
        multiplier,
        finalUnitPrice,
        totalPayout,
        qualityNotes: notes || null,
        soldAt: new Date(),
      },
    })

    return { saleRecord, newBalance: updatedTeam.cashBalance }
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return result
}

/**
 * 2. Kötegelt Banki Minőségátvétel (Batch Inspection Desk - S-FAC-03)
 */
export async function executeBatchBankSale(
  sessionId: string,
  teamId: string,
  items: ShapeBatchItem[],
  notes?: string
) {
  const validItems = items.filter((it) => it.quantity > 0)
  if (validItems.length === 0) {
    throw new Error('Legalább egy érvényes formát és darabszámot meg kell adni.')
  }

  const result = await prisma.$transaction(async (tx) => {
    const session = await tx.session.findUnique({
      where: { id: sessionId },
      include: {
        marketEvents: {
          where: { isActive: true },
          orderBy: { triggeredAt: 'desc' },
          take: 1,
        },
      },
    })

    if (!session) {
      throw new Error('A munkamenet nem található.')
    }

    let modifiers: Record<string, number> = {}
    if (session.marketEvents.length > 0) {
      try {
        modifiers = JSON.parse(session.marketEvents[0].priceMultipliers || '{}')
      } catch (err) {
        console.warn('Hiba a piaci esemény szorzóinak parszolásakor:', err)
      }
    }

    let totalBatchPayout = 0
    const saleRecords = []

    for (const item of validItems) {
      const multiplier = typeof modifiers[item.shapeType] === 'number' ? modifiers[item.shapeType] : 1.0
      const unitBasePrice = BASE_PRICES[item.shapeType] || 0
      const finalUnitPrice = Math.round(unitBasePrice * multiplier)
      const totalPayout = finalUnitPrice * item.quantity
      totalBatchPayout += totalPayout

      const record = await tx.bankSale.create({
        data: {
          sessionId,
          teamId,
          shapeType: item.shapeType,
          quantity: item.quantity,
          unitBasePrice,
          multiplier,
          finalUnitPrice,
          totalPayout,
          qualityNotes: notes || null,
          soldAt: new Date(),
        },
      })
      saleRecords.push(record)
    }

    const updatedTeam = await tx.sessionTeam.update({
      where: { id: teamId },
      data: {
        cashBalance: { increment: totalBatchPayout },
      },
    })

    return { saleRecords, totalBatchPayout, newBalance: updatedTeam.cashBalance }
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return result
}

/**
 * 3. Piaci Esemény Aktiválása (Breaking Market Shock / Alert)
 */
export async function triggerMarketEvent(
  sessionId: string,
  eventType: string,
  title: string,
  description: string,
  priceMultipliers: Record<string, number> | string,
  durationSeconds: number = 180
) {
  const multipliersJson =
    typeof priceMultipliers === 'string' ? priceMultipliers : JSON.stringify(priceMultipliers)

  const event = await prisma.$transaction(async (tx) => {
    // Előző aktív események leállítása
    await tx.marketEvent.updateMany({
      where: { sessionId, isActive: true },
      data: { isActive: false },
    })

    return await tx.marketEvent.create({
      data: {
        sessionId,
        code: eventType,
        title,
        description,
        priceMultipliers: multipliersJson,
        durationSeconds,
        isActive: true,
        triggeredAt: new Date(),
      },
    })
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return event
}

/**
 * 4. Aktív piaci esemény törlése / piac normalizálása
 */
export async function clearMarketEvents(sessionId: string) {
  await prisma.marketEvent.updateMany({
    where: { sessionId, isActive: true },
    data: { isActive: false },
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return { success: true }
}

/**
 * 5. Aktuális árak lekérése az aktív piaci módosítókkal
 */
export async function getCommodityPrices(sessionId: string) {
  const activeEvent = await prisma.marketEvent.findFirst({
    where: { sessionId, isActive: true },
    orderBy: { triggeredAt: 'desc' },
  })

  let multipliers: Record<string, number> = {}
  if (activeEvent?.priceMultipliers) {
    try {
      multipliers = JSON.parse(activeEvent.priceMultipliers)
    } catch (e) {
      console.warn('Error parsing multipliers:', e)
    }
  }

  const result: Record<ShapeType, { basePrice: number; multiplier: number; finalPrice: number }> = {
    SQUARE: {
      basePrice: BASE_PRICES.SQUARE,
      multiplier: multipliers.SQUARE ?? 1.0,
      finalPrice: Math.round(BASE_PRICES.SQUARE * (multipliers.SQUARE ?? 1.0)),
    },
    TRIANGLE: {
      basePrice: BASE_PRICES.TRIANGLE,
      multiplier: multipliers.TRIANGLE ?? 1.0,
      finalPrice: Math.round(BASE_PRICES.TRIANGLE * (multipliers.TRIANGLE ?? 1.0)),
    },
    CIRCLE: {
      basePrice: BASE_PRICES.CIRCLE,
      multiplier: multipliers.CIRCLE ?? 1.0,
      finalPrice: Math.round(BASE_PRICES.CIRCLE * (multipliers.CIRCLE ?? 1.0)),
    },
    RECTANGLE: {
      basePrice: BASE_PRICES.RECTANGLE,
      multiplier: multipliers.RECTANGLE ?? 1.0,
      finalPrice: Math.round(BASE_PRICES.RECTANGLE * (multipliers.RECTANGLE ?? 1.0)),
    },
    PREMIUM_PACK: {
      basePrice: BASE_PRICES.PREMIUM_PACK,
      multiplier: multipliers.PREMIUM_PACK ?? 1.0,
      finalPrice: Math.round(BASE_PRICES.PREMIUM_PACK * (multipliers.PREMIUM_PACK ?? 1.0)),
    },
  }

  return { prices: result, activeEvent }
}
