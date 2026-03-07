'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'
import { PRODUCTION_RECIPES, ProductType } from './constants'

import { getDynamicPricing } from './pricing'
import { BANK_BUY_MARKUP, RAW_MATERIAL_BUY_PRICE } from './bankConstants'

// Sell one unit of a produced item to the Bank at the current dynamic price
export async function sellToBank(sessionId: string, userId: string, productType: ProductType) {
    const recipe = PRODUCTION_RECIPES[productType]
    if (!recipe) throw new Error("Invalid product type")

    const prices = await getDynamicPricing(sessionId)
    const currentPrice = prices[productType].sellToBank

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
        const revenue = currentPrice

        const updated = await tx.sessionParticipant.update({
            where: { id: participant.id },
            data: { inventory: JSON.stringify(inventory), capital: participant.capital + revenue }
        })

        // Növeljük a Bank inventory-ját, mert vett tőlünk egy terméket
        await tx.bankInventory.upsert({
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            where: { sessionId_productKey: { sessionId, productKey: productType } } as any,
            update: { quantity: { increment: 1 } },
            create: { sessionId, productKey: productType, quantity: 1 }
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

    const prices = await getDynamicPricing(sessionId)
    const cost = prices[productType].buyFromBank

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

        // Csökkentjük a Bank inventory-ját, mert eladott nekünk egy terméket
        await tx.bankInventory.upsert({
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            where: { sessionId_productKey: { sessionId, productKey: productType } } as any,
            update: { quantity: { decrement: 1 } },
            create: { sessionId, productKey: productType, quantity: -1 }
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

// Buy 1 unit of raw material (vetőmag) from the bank at dynamic price
export async function buyRawMaterial(sessionId: string, userId: string) {
    const prices = await getDynamicPricing(sessionId)
    const cost = prices['rawMaterial'].buyFromBank

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

        await tx.bankInventory.upsert({
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            where: { sessionId_productKey: { sessionId, productKey: 'rawMaterial' } } as any,
            update: { quantity: { decrement: 1 } },
            create: { sessionId, productKey: 'rawMaterial', quantity: -1 }
        })

        const session = await tx.session.findUnique({
            where: { id: sessionId }, include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })
        if (session?.rounds[0]) {
            await tx.interaction.create({
                data: { sessionId, roundId: session.rounds[0].id, fromUserId: userId, type: 'bank-buy', resourceType: 'rawMaterial', quantity: 1 }
            })
        }

        return updated
    })

    revalidatePath(`/play/${sessionId}`)
    return result
}

// Sell 1 unit of raw material (vetőmag) to the bank at dynamic price
export async function sellRawMaterial(sessionId: string, userId: string) {
    const prices = await getDynamicPricing(sessionId)
    const revenue = prices['rawMaterial'].sellToBank

    const result = await prisma.$transaction(async (tx) => {
        const participant = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId } }
        })
        if (!participant) throw new Error("Participant not found")
        if (participant.rawMaterial < 1) throw new Error("Nincs elegendő Vetőmag")

        const updated = await tx.sessionParticipant.update({
            where: { id: participant.id },
            data: { rawMaterial: participant.rawMaterial - 1, capital: participant.capital + revenue }
        })

        await tx.bankInventory.upsert({
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            where: { sessionId_productKey: { sessionId, productKey: 'rawMaterial' } } as any,
            update: { quantity: { increment: 1 } },
            create: { sessionId, productKey: 'rawMaterial', quantity: 1 }
        })

        const session = await tx.session.findUnique({
            where: { id: sessionId }, include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })
        if (session?.rounds[0]) {
            await tx.interaction.create({
                data: { sessionId, roundId: session.rounds[0].id, fromUserId: userId, type: 'bank-sale', resourceType: 'rawMaterial', quantity: 1 }
            })
        }

        return updated
    })

    revalidatePath(`/play/${sessionId}`)
    return result
}
