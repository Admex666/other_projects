'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

import { PRODUCTION_RECIPES, ShapeType } from './constants'

export async function produceShape(sessionId: string, teamId: string, shapeType: ShapeType) {
    const recipe = PRODUCTION_RECIPES[shapeType]
    if (!recipe) throw new Error("Invalid shape type")

    // Use transaction to ensure atomic deduct and credit
    const result = await prisma.$transaction(async (tx) => {
        // Fetch team state
        const team = await tx.team.findUnique({
            where: { id: teamId }
        })

        if (!team) throw new Error("Team not found")

        // Validate Requirements
        if (team.rawMaterial < recipe.rawCost) {
            throw new Error(`Not enough Raw Materials (Need ${recipe.rawCost}, Have ${team.rawMaterial})`)
        }
        if (team.techLevel < recipe.techReq) {
            throw new Error(`Tech Level too low (Need Level ${recipe.techReq}, Have Level ${team.techLevel})`)
        }

        // Calculate Revenue with Production Efficiency
        const revenue = recipe.baseValue * team.productionEff

        // Update Team State
        const updatedTeam = await tx.team.update({
            where: { id: teamId },
            data: {
                rawMaterial: team.rawMaterial - recipe.rawCost,
                capital: team.capital + revenue
            }
        })

        // Log the production action (Interactions table used generically)
        // Note: For MVP we log production as an 'internal' interaction
        const session = await tx.session.findUnique({
            where: { id: sessionId },
            include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
        })

        if (session && session.rounds[0]) {
            // Find a participant user id from the team to attribute the action to
            const participant = await tx.sessionParticipant.findFirst({
                where: { teamId: teamId }
            })

            if (participant) {
                await tx.interaction.create({
                    data: {
                        sessionId: sessionId,
                        roundId: session.rounds[0].id,
                        fromUserId: participant.userId,
                        type: 'production',
                        resourceType: shapeType,
                        quantity: 1
                    }
                })
            }
        }

        return updatedTeam
    })

    // Revalidate the play page so UI updates instantly
    revalidatePath(`/play/${sessionId}`)
    return result
}
