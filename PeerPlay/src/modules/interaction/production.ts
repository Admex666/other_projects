'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

import { PRODUCTION_RECIPES, ProductType } from './constants'

export async function produceItem(sessionId: string, userId: string, productType: ProductType) {
    const recipe = PRODUCTION_RECIPES[productType]
    if (!recipe) throw new Error("Invalid product type")

    // Use transaction to ensure atomic deduct and credit
    const result = await prisma.$transaction(async (tx) => {
        // Fetch participant state
        const participant = await tx.sessionParticipant.findUnique({
            where: { sessionId_userId: { sessionId, userId } }
        })

        if (!participant) throw new Error("Participant not found in session")

        // Validate Requirements
        if (participant.rawMaterial < recipe.rawCost) {
            throw new Error(`Not enough Raw Materials (Need ${recipe.rawCost}, Have ${participant.rawMaterial})`)
        }
        if (participant.techLevel < recipe.techReq) {
            throw new Error(`Tech Level too low (Need Level ${recipe.techReq}, Have Level ${participant.techLevel})`)
        }

        // Update Inventory Instead of Capital
        const inventory = JSON.parse(participant.inventory || "{}")
        inventory[productType] = (inventory[productType] || 0) + 1

        // Véletlenszerű bónusz vetőmag visszanyerés (40% 0, 30% 1, 20% 2, 10% 3)
        const rand = Math.random()
        let bonusSeeds = 0
        if (rand < 0.1) bonusSeeds = 3 // 10%
        else if (rand < 0.3) bonusSeeds = 2 // 20%
        else if (rand < 0.6) bonusSeeds = 1 // 30%
        // maradék 40% (rand 0.6 felett) -> 0

        // Update Participant State
        const updatedParticipant = await tx.sessionParticipant.update({
            where: { id: participant.id },
            data: {
                rawMaterial: participant.rawMaterial - recipe.rawCost + bonusSeeds,
                inventory: JSON.stringify(inventory)
            }
        })

        // Log the production action
        const session = await tx.session.findUnique({
            where: { id: sessionId },
            include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })

        if (session && session.rounds[0]) {
            await tx.interaction.create({
                data: {
                    sessionId: sessionId,
                    roundId: session.rounds[0].id,
                    fromUserId: userId,
                    type: 'production',
                    resourceType: productType,
                    quantity: 1
                }
            })
        }

        return { participant: updatedParticipant, bonusSeeds }
    })

    // Revalidate the play page so UI updates instantly
    revalidatePath(`/play/${sessionId}`)
    return result
}
