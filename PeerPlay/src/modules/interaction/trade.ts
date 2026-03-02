'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

export type ResourceBundle = {
    capital?: number
    rawMaterial?: number
    wheat?: number
    corn?: number
    sunflower?: number
    wine?: number
}

/** Send a trade request from one player to another */
export async function sendTradeRequest(
    sessionId: string,
    fromUserId: string,
    toUserId: string,
    offered: ResourceBundle,
    requested: ResourceBundle,
    message?: string
) {
    if (fromUserId === toUserId) throw new Error("Nem kereskedhetsz saját magaddal")

    const trade = await prisma.tradeRequest.create({
        data: {
            sessionId,
            fromUserId,
            toUserId,
            offeredResources: JSON.stringify(offered),
            requestedResources: JSON.stringify(requested),
            message: message || null,
            status: 'pending'
        }
    })

    revalidatePath(`/play/${sessionId}`)
    return trade
}

/** Accept a trade and atomically transfer resources between participants */
export async function acceptTrade(tradeId: string, sessionId: string) {
    const result = await prisma.$transaction(async (tx) => {
        const trade = await tx.tradeRequest.findUnique({ where: { id: tradeId } })
        if (!trade || trade.status !== 'pending') throw new Error('Trade not found or not pending')

        const offered: ResourceBundle = JSON.parse(trade.offeredResources)
        const requested: ResourceBundle = JSON.parse(trade.requestedResources)

        const sender = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId: trade.fromUserId } }
        })
        const receiver = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId: trade.toUserId } }
        })

        if (!sender || !receiver) throw new Error('Participants not found')

        // Validate sender has enough of what they offered
        const senderInventory = JSON.parse(sender.inventory || '{}')
        if ((offered.capital || 0) > sender.capital) throw new Error('Küldőnek nincs elég tőkéje')
        if ((offered.rawMaterial || 0) > sender.rawMaterial) throw new Error('Küldőnek nincs elég vetőmagja')
        for (const [item, qty] of Object.entries(offered)) {
            if (['wheat', 'corn', 'sunflower', 'wine'].includes(item)) {
                if ((qty || 0) > (senderInventory[item] || 0)) throw new Error(`Küldőnek nincs elég ${item}`)
            }
        }

        // Validate receiver has enough of what they offered in return
        const receiverInventory = JSON.parse(receiver.inventory || '{}')
        if ((requested.capital || 0) > receiver.capital) throw new Error('Fogadónak nincs elég tőkéje')
        if ((requested.rawMaterial || 0) > receiver.rawMaterial) throw new Error('Fogadónak nincs elég vetőmagja')
        for (const [item, qty] of Object.entries(requested)) {
            if (['wheat', 'corn', 'sunflower', 'wine'].includes(item)) {
                if ((qty || 0) > (receiverInventory[item] || 0)) throw new Error(`Fogadónak nincs elég ${item}`)
            }
        }

        // Apply transfers: sender gives offered, receives requested
        const newSenderInventory = { ...senderInventory }
        const newReceiverInventory = { ...receiverInventory }

        // Deduct from sender, credit receiver (offered)
        for (const [item, qty] of Object.entries(offered)) {
            if (item === 'capital') {
                await tx.sessionParticipant.update({ where: { id: sender.id }, data: { capital: { decrement: qty || 0 } } })
                await tx.sessionParticipant.update({ where: { id: receiver.id }, data: { capital: { increment: qty || 0 } } })
            } else if (item === 'rawMaterial') {
                await tx.sessionParticipant.update({ where: { id: sender.id }, data: { rawMaterial: { decrement: qty || 0 } } })
                await tx.sessionParticipant.update({ where: { id: receiver.id }, data: { rawMaterial: { increment: qty || 0 } } })
            } else {
                newSenderInventory[item] = (newSenderInventory[item] || 0) - (qty || 0)
                newReceiverInventory[item] = (newReceiverInventory[item] || 0) + (qty || 0)
            }
        }

        // Deduct from receiver, credit sender (requested)
        for (const [item, qty] of Object.entries(requested)) {
            if (item === 'capital') {
                await tx.sessionParticipant.update({ where: { id: receiver.id }, data: { capital: { decrement: qty || 0 } } })
                await tx.sessionParticipant.update({ where: { id: sender.id }, data: { capital: { increment: qty || 0 } } })
            } else if (item === 'rawMaterial') {
                await tx.sessionParticipant.update({ where: { id: receiver.id }, data: { rawMaterial: { decrement: qty || 0 } } })
                await tx.sessionParticipant.update({ where: { id: sender.id }, data: { rawMaterial: { increment: qty || 0 } } })
            } else {
                newReceiverInventory[item] = (newReceiverInventory[item] || 0) - (qty || 0)
                newSenderInventory[item] = (newSenderInventory[item] || 0) + (qty || 0)
            }
        }

        // Update inventories
        await tx.sessionParticipant.update({ where: { id: sender.id }, data: { inventory: JSON.stringify(newSenderInventory) } })
        await tx.sessionParticipant.update({ where: { id: receiver.id }, data: { inventory: JSON.stringify(newReceiverInventory) } })

        // Mark trade as accepted
        const updated = await tx.tradeRequest.update({ where: { id: tradeId }, data: { status: 'accepted' } })

        // Log as interaction
        const session = await tx.session.findUnique({
            where: { id: sessionId }, include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })
        if (session?.rounds[0]) {
            await tx.interaction.create({
                data: { sessionId, roundId: session.rounds[0].id, fromUserId: trade.fromUserId, toUserId: trade.toUserId, type: 'trade-accepted', quantity: 1 }
            })
        }

        return updated
    })

    revalidatePath(`/play/${sessionId}`)
    return result
}

/** Reject a pending trade */
export async function rejectTrade(tradeId: string, sessionId: string) {
    await prisma.tradeRequest.update({ where: { id: tradeId }, data: { status: 'rejected' } })
    revalidatePath(`/play/${sessionId}`)
}

/** Cancel a pending trade (by sender) */
export async function cancelTrade(tradeId: string, sessionId: string) {
    await prisma.tradeRequest.update({ where: { id: tradeId }, data: { status: 'cancelled' } })
    revalidatePath(`/play/${sessionId}`)
}

/** Get all trade requests for a session involving a specific user */
export async function getTradesForUser(sessionId: string, userId: string) {
    return prisma.tradeRequest.findMany({
        where: {
            sessionId,
            OR: [{ fromUserId: userId }, { toUserId: userId }]
        },
        include: {
            fromUser: { select: { id: true, name: true } },
            toUser: { select: { id: true, name: true } }
        },
        orderBy: { createdAt: 'desc' },
        take: 50
    })
}
