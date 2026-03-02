'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'
import { PRODUCTION_RECIPES, ProductType } from './constants'

import { BANK_BUY_MARKUP, RAW_MATERIAL_BUY_PRICE } from './bankConstants'

// Sell one unit of a produced item to the Bank for its base value × productionEff
export async function sellToBank(sessionId: string, userId: string, productType: ProductType) {
    const recipe = PRODUCTION_RECIPES[productType]
    if (!recipe) throw new Error("Invalid product type")

    const result = await prisma.$transaction(async (tx) => {
        const participant = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId } }
        })

        if (!participant) throw new Error("Participant not found")

        const inventory = JSON.parse(participant.inventory || "{}")
        const currentQty = inventory[productType] || 0

        if (currentQty < 1) {
            throw new Error(`Nincs elegendő ${recipe.name} az inventoryban`)
        }

        inventory[productType] = currentQty - 1
        const revenue = Math.round(recipe.baseValue * participant.productionEff)

        const updated = await tx.sessionParticipant.update({
            where: { id: participant.id },
            data: { inventory: JSON.stringify(inventory), capital: participant.capital + revenue }
        })

        const session = await tx.session.findUnique({
            where: { id: sessionId },
            include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })
        if (session?.rounds[0]) {
            await tx.interaction.create({
                data: { sessionId, roundId: session.rounds[0].id, fromUserId: userId, type: 'bank-sale', resourceType: productType, quantity: 1 }
            })
        }

        return updated
    })

    revalidatePath(`/play/${sessionId}`)
    return result
}

// Buy 1 unit of a produced item from the Bank (costs baseValue × BANK_BUY_MARKUP)
export async function buyFromBank(sessionId: string, userId: string, productType: ProductType) {
    const recipe = PRODUCTION_RECIPES[productType]
    if (!recipe) throw new Error("Invalid product type")

    const cost = Math.round(recipe.baseValue * BANK_BUY_MARKUP)

    const result = await prisma.$transaction(async (tx) => {
        const participant = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId } }
        })
        if (!participant) throw new Error("Participant not found")
        if (participant.capital < cost) throw new Error(`Nincs elég tőke (kell: $${cost}, van: $${participant.capital})`)

        const inventory = JSON.parse(participant.inventory || "{}")
        inventory[productType] = (inventory[productType] || 0) + 1

        const updated = await tx.sessionParticipant.update({
            where: { id: participant.id },
            data: { inventory: JSON.stringify(inventory), capital: participant.capital - cost }
        })

        const session = await tx.session.findUnique({
            where: { id: sessionId }, include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })
        if (session?.rounds[0]) {
            await tx.interaction.create({
                data: { sessionId, roundId: session.rounds[0].id, fromUserId: userId, type: 'bank-buy', resourceType: productType, quantity: 1 }
            })
        }

        return updated
    })

    revalidatePath(`/play/${sessionId}`)
    return result
}

// Buy 1 unit of raw material (vetőmag) from the bank for a fixed price
export async function buyRawMaterial(sessionId: string, userId: string) {
    const cost = RAW_MATERIAL_BUY_PRICE

    const result = await prisma.$transaction(async (tx) => {
        const participant = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId } }
        })
        if (!participant) throw new Error("Participant not found")
        if (participant.capital < cost) throw new Error(`Nincs elég tőke (kell: $${cost})`)

        const updated = await tx.sessionParticipant.update({
            where: { id: participant.id },
            data: { rawMaterial: participant.rawMaterial + 1, capital: participant.capital - cost }
        })

        return updated
    })

    revalidatePath(`/play/${sessionId}`)
    return result
}
