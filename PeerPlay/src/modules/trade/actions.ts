'use server'

import prisma from '@/lib/prisma'
import { safeRevalidatePath } from '@/lib/safeRevalidate'

export interface ResourceBundle {
  cash: number
  paperSheets: number
  scissorsCount: number
  rulersCount: number
  templatesCount: number
}

function sanitizeBundle(bundle?: Partial<ResourceBundle>): ResourceBundle {
  return {
    cash: Math.max(0, Math.floor(bundle?.cash ?? 0)),
    paperSheets: Math.max(0, Math.floor(bundle?.paperSheets ?? 0)),
    scissorsCount: Math.max(0, Math.floor(bundle?.scissorsCount ?? 0)),
    rulersCount: Math.max(0, Math.floor(bundle?.rulersCount ?? 0)),
    templatesCount: Math.max(0, Math.floor(bundle?.templatesCount ?? 0)),
  }
}

function isBundleEmpty(bundle: ResourceBundle): boolean {
  return (
    bundle.cash === 0 &&
    bundle.paperSheets === 0 &&
    bundle.scissorsCount === 0 &&
    bundle.rulersCount === 0 &&
    bundle.templatesCount === 0
  )
}

/**
 * 1. Ajánlat küldése és azonnali letétbe helyezés (Immediate Escrow)
 */
export async function createTradeOffer(
  sessionId: string,
  senderTeamId: string,
  receiverTeamId: string,
  offeredInput: Partial<ResourceBundle>,
  requestedInput: Partial<ResourceBundle>,
  notes?: string
) {
  if (senderTeamId === receiverTeamId) {
    throw new Error('Saját csapatoddal nem kereskedhetsz.')
  }

  const offered = sanitizeBundle(offeredInput)
  const requested = sanitizeBundle(requestedInput)

  if (isBundleEmpty(offered) && isBundleEmpty(requested)) {
    throw new Error('Legalább egy felajánlott vagy kért tételt meg kell adni.')
  }

  const trade = await prisma.$transaction(async (tx) => {
    const session = await tx.session.findUnique({
      where: { id: sessionId },
      select: { currentPhase: true, status: true }
    })

    const activeTradingPhases = ['PHASE_4_ROUND_1', 'PHASE_6_ROUND_2', 'PHASE_8_ROUND_3']
    if (!session || !activeTradingPhases.includes(session.currentPhase)) {
      throw new Error('A kereskedés jelenleg szünetel vagy le van zárva ebben a fázisban.')
    }

    const sender = await tx.sessionTeam.findUnique({
      where: { id: senderTeamId }
    })
    if (!sender || sender.sessionId !== sessionId) {
      throw new Error('A feladó csapat nem található a munkamenetben.')
    }

    const receiver = await tx.sessionTeam.findUnique({
      where: { id: receiverTeamId }
    })
    if (!receiver || receiver.sessionId !== sessionId) {
      throw new Error('A címzett csapat nem található a munkamenetben.')
    }

    // Fedezet ellenőrzése
    if (sender.cashBalance < offered.cash) throw new Error('Nincs elegendő készpénzed az ajánlathoz.')
    if (sender.paperSheets < offered.paperSheets) throw new Error('Nincs elegendő papírlapod az ajánlathoz.')
    if (sender.scissorsCount < offered.scissorsCount) throw new Error('Nincs elegendő ollód az ajánlathoz.')
    if (sender.rulersCount < offered.rulersCount) throw new Error('Nincs elegendő vonalzód az ajánlathoz.')
    if (sender.templatesCount < offered.templatesCount) throw new Error('Nincs elegendő sablonod az ajánlathoz.')

    // 1. Escrow zárolás a feladótól
    await tx.sessionTeam.update({
      where: { id: senderTeamId },
      data: {
        cashBalance: { decrement: offered.cash },
        paperSheets: { decrement: offered.paperSheets },
        scissorsCount: { decrement: offered.scissorsCount },
        rulersCount: { decrement: offered.rulersCount },
        templatesCount: { decrement: offered.templatesCount }
      }
    })

    // 2. Tranzakció létrehozása
    const createdTrade = await tx.tradeTransaction.create({
      data: {
        sessionId,
        senderTeamId,
        receiverTeamId,
        offeredItems: JSON.stringify(offered),
        requestedItems: JSON.stringify(requested),
        escrowedItems: JSON.stringify(offered),
        status: 'PENDING',
        notes: notes || null
      }
    })

    return createdTrade
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return trade
}

/** Alias for backward compatibility */
export const sendTradeOffer = createTradeOffer

/**
 * 2. Ajánlat elfogadása és atomi készletcsere
 */
export async function acceptTradeOffer(sessionId: string, tradeId: string, receiverTeamId: string) {
  const result = await prisma.$transaction(async (tx) => {
    const trade = await tx.tradeTransaction.findUnique({
      where: { id: tradeId }
    })

    if (!trade || trade.sessionId !== sessionId || trade.status !== 'PENDING') {
      throw new Error('Az ajánlat már nem elérhető vagy feldolgozásra került.')
    }
    if (trade.receiverTeamId !== receiverTeamId) {
      throw new Error('Nincs jogosultságod ennek az ajánlatnak az elfogadására.')
    }

    const offered: ResourceBundle = JSON.parse(trade.offeredItems)
    const requested: ResourceBundle = JSON.parse(trade.requestedItems)

    const receiver = await tx.sessionTeam.findUnique({
      where: { id: receiverTeamId }
    })
    if (!receiver) throw new Error('A fogadó csapat nem található.')

    // Ellenőrzés: A fogadó fél képes-e átadni a kért tételeket?
    if (receiver.cashBalance < requested.cash) throw new Error('Nincs elegendő készpénzed az elfogadáshoz.')
    if (receiver.paperSheets < requested.paperSheets) throw new Error('Nincs elegendő papírlapod az elfogadáshoz.')
    if (receiver.scissorsCount < requested.scissorsCount) throw new Error('Nincs elegendő ollód az elfogadáshoz.')
    if (receiver.rulersCount < requested.rulersCount) throw new Error('Nincs elegendő vonalzód az elfogadáshoz.')
    if (receiver.templatesCount < requested.templatesCount) throw new Error('Nincs elegendő sablonod az elfogadáshoz.')

    // 1. Levonás és jóváírás a fogadó félnél (offered - requested net változás)
    await tx.sessionTeam.update({
      where: { id: receiverTeamId },
      data: {
        cashBalance: { increment: offered.cash - requested.cash },
        paperSheets: { increment: offered.paperSheets - requested.paperSheets },
        scissorsCount: { increment: offered.scissorsCount - requested.scissorsCount },
        rulersCount: { increment: offered.rulersCount - requested.rulersCount },
        templatesCount: { increment: offered.templatesCount - requested.templatesCount }
      }
    })

    // 2. Jóváírás a feladó félnek a kért javakból (requested)
    await tx.sessionTeam.update({
      where: { id: trade.senderTeamId },
      data: {
        cashBalance: { increment: requested.cash },
        paperSheets: { increment: requested.paperSheets },
        scissorsCount: { increment: requested.scissorsCount },
        rulersCount: { increment: requested.rulersCount },
        templatesCount: { increment: requested.templatesCount }
      }
    })

    // 3. Tranzakció státusz frissítése
    const updatedTrade = await tx.tradeTransaction.update({
      where: { id: tradeId },
      data: {
        status: 'ACCEPTED',
        resolvedAt: new Date()
      }
    })

    return updatedTrade
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return result
}

/**
 * 3. Ajánlat elutasítása (Címzett utasítja el -> azonnali Escrow visszatérítés a feladónak)
 */
export async function rejectTradeOffer(sessionId: string, tradeId: string, receiverTeamId: string) {
  const result = await prisma.$transaction(async (tx) => {
    const trade = await tx.tradeTransaction.findUnique({
      where: { id: tradeId }
    })

    if (!trade || trade.sessionId !== sessionId || trade.status !== 'PENDING') {
      throw new Error('Az ajánlat nem található vagy már lezárult.')
    }
    if (trade.receiverTeamId !== receiverTeamId) {
      throw new Error('Nincs jogosultságod ennek az ajánlatnak az elutasítására.')
    }

    const escrowed: ResourceBundle = JSON.parse(trade.escrowedItems)

    // Letét visszatérítése a feladónak
    await tx.sessionTeam.update({
      where: { id: trade.senderTeamId },
      data: {
        cashBalance: { increment: escrowed.cash },
        paperSheets: { increment: escrowed.paperSheets },
        scissorsCount: { increment: escrowed.scissorsCount },
        rulersCount: { increment: escrowed.rulersCount },
        templatesCount: { increment: escrowed.templatesCount }
      }
    })

    const updatedTrade = await tx.tradeTransaction.update({
      where: { id: tradeId },
      data: {
        status: 'REJECTED',
        resolvedAt: new Date()
      }
    })

    return updatedTrade
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return result
}

/**
 * 4. Ajánlat visszavonása (Feladó vonja vissza -> azonnali Escrow visszatérítés)
 */
export async function cancelTradeOffer(sessionId: string, tradeId: string, senderTeamId: string) {
  const result = await prisma.$transaction(async (tx) => {
    const trade = await tx.tradeTransaction.findUnique({
      where: { id: tradeId }
    })

    if (!trade || trade.sessionId !== sessionId || trade.status !== 'PENDING') {
      throw new Error('Az ajánlat nem található vagy már lezárult.')
    }
    if (trade.senderTeamId !== senderTeamId) {
      throw new Error('Csak a feladó vonhatja vissza a saját ajánlatát.')
    }

    const escrowed: ResourceBundle = JSON.parse(trade.escrowedItems)

    // Letét visszatérítése a feladónak
    await tx.sessionTeam.update({
      where: { id: senderTeamId },
      data: {
        cashBalance: { increment: escrowed.cash },
        paperSheets: { increment: escrowed.paperSheets },
        scissorsCount: { increment: escrowed.scissorsCount },
        rulersCount: { increment: escrowed.rulersCount },
        templatesCount: { increment: escrowed.templatesCount }
      }
    })

    const updatedTrade = await tx.tradeTransaction.update({
      where: { id: tradeId },
      data: {
        status: 'CANCELLED',
        resolvedAt: new Date()
      }
    })

    return updatedTrade
  })

  safeRevalidatePath(`/play/${sessionId}`)
  safeRevalidatePath(`/sessions/${sessionId}`)
  return result
}

/**
 * 5. Kényszerített kör-zárás és automatikus visszatérítés (Auto-Refund on Phase End)
 */
export async function autoRefundOnPhaseEnd(sessionId: string) {
  return await prisma.$transaction(async (tx) => {
    const pendingTrades = await tx.tradeTransaction.findMany({
      where: {
        sessionId,
        status: 'PENDING'
      }
    })

    for (const trade of pendingTrades) {
      const escrowed: ResourceBundle = JSON.parse(trade.escrowedItems)

      await tx.sessionTeam.update({
        where: { id: trade.senderTeamId },
        data: {
          cashBalance: { increment: escrowed.cash },
          paperSheets: { increment: escrowed.paperSheets },
          scissorsCount: { increment: escrowed.scissorsCount },
          rulersCount: { increment: escrowed.rulersCount },
          templatesCount: { increment: escrowed.templatesCount }
        }
      })

      await tx.tradeTransaction.update({
        where: { id: trade.id },
        data: {
          status: 'EXPIRED',
          resolvedAt: new Date()
        }
      })
    }

    return { refundedCount: pendingTrades.length }
  })
}

/**
 * 6. Csapat kereskedési ajánlatainak lekérése (inbound és outbound)
 */
export async function getTradesForTeam(sessionId: string, teamId: string) {
  return await prisma.tradeTransaction.findMany({
    where: {
      sessionId,
      OR: [{ senderTeamId: teamId }, { receiverTeamId: teamId }],
    },
    include: {
      senderTeam: true,
      receiverTeam: true,
    },
    orderBy: { createdAt: 'desc' },
  })
}

